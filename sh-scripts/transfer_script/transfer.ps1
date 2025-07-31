# Define parameters for the script
param(
    [string]$SourcePath = "C:\tdf\log1",
    [string]$DestinationUNCPath = "path/to/your/network/directory",
    [string]$FilePrefix = "TEC_",
    [string]$CredentialPath = "path/to/your/directory/file.xml"
)

# Import credentials from a secure file
if (-Not (Test-Path -Path $CredentialPath)) {
    Write-Host "Error: Credential file '$CredentialPath' not found." -ForegroundColor Red
    exit 1
}
$Credential = Import-Clixml -Path $CredentialPath

# Use a temporary drive to access the UNC path
$DriveName = "TempDrive"

try {
    # Remove the drive if it already exists
    if (Get-PSDrive -Name $DriveName -ErrorAction SilentlyContinue) {
        Remove-PSDrive -Name $DriveName -Force
    }

    # Map the UNC path to a temporary drive using credentials
    New-PSDrive -Name $DriveName -PSProvider FileSystem -Root $DestinationUNCPath -Credential $Credential

    # Check if the source path exists
    if (-Not (Test-Path -Path $SourcePath)) {
        Write-Host "Error: Source path '$SourcePath' does not exist." -ForegroundColor Red
        exit 1
    }

    # Check if the temporary drive (destination) is accessible
    if (-Not (Test-Path -Path "${DriveName}:\")) {
        Write-Host "Error: Destination UNC path '$DestinationUNCPath' is not accessible." -ForegroundColor Red
        exit 1
    }

    # Copy only the latest 5 files from the source to the destination
    Write-Host "Copying the latest 5 files from '$SourcePath' to '$DestinationUNCPath' that start with '$FilePrefix', ignoring files starting with 'TEC_YM_'..."

    # Get the latest 5 files in the source path that meet the criteria
    $FilesToCopy = Get-ChildItem -Path $SourcePath | Where-Object {
        -Not $_.PSIsContainer -and $_.Name -like "$FilePrefix*" -and $_.Name -notlike "TEC_YM_*"
    } | Sort-Object -Property LastWriteTime -Descending | Select-Object -First 5

    # Check if there are any files to copy
    if ($FilesToCopy.Count -eq 0) {
        Write-Host "No files starting with '$FilePrefix' (except those ignored) were found in '$SourcePath'." -ForegroundColor Yellow
    } else {
        # Copy each matching file to the destination, skipping files that already exist
        foreach ($File in $FilesToCopy) {
            $SourceFile = $File.FullName
            $DestinationFile = Join-Path -Path "${DriveName}:\" -ChildPath $File.Name

            # Skip if the file already exists in the destination
            if (Test-Path -Path $DestinationFile) {
                Write-Host "Skipping: $DestinationFile (already exists)" -ForegroundColor Yellow
                continue
            }

            # Copy the file (no -Force, so it won't overwrite)
            Copy-Item -Path $SourceFile -Destination $DestinationFile
            Write-Host "Copied: $SourceFile -> $DestinationFile" -ForegroundColor Green
        }

        Write-Host "Latest 5 files copied successfully!" -ForegroundColor Green
    }
} catch {
    Write-Host "Error: An error occurred. $_" -ForegroundColor Red
} finally {
    # Remove the temporary drive
    Remove-PSDrive -Name $DriveName -Force -ErrorAction SilentlyContinue
    Write-Host "Temporary drive '$DriveName' removed."
}
