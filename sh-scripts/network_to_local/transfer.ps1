# Define parameters for the script
param(
    [string[]]$SourcePaths = @("path/to/your/network/directory1", "path/to/your/network/directory2", "path/to/your/network/directoryXX"), # Example source paths
    [string[]]$DestinationUNCPaths = @("path/to/your/local/directory1", "path/to/your/local/directory2", "path/to/your/local/directoryXX"), # Example destination paths
    [string]$FilePrefix = "TEC_", # Prefix for filtering files
    [string]$CredentialPath = "path/to/your/directory/file.xml"
)

# Validate that source and destination arrays match in length
if ($SourcePaths.Count -ne $DestinationUNCPaths.Count) {
    Write-Host "Error: The number of source paths must match the number of destination paths." -ForegroundColor Red
    exit 1
}

# Import credentials from a secure file
if (-Not (Test-Path -Path $CredentialPath)) {
    Write-Host "Error: Credential file '$CredentialPath' not found." -ForegroundColor Red
    exit 1
}
$Credential = Import-Clixml -Path $CredentialPath

# Use a temporary drive to access the UNC paths
$DriveName = "TempDrive"

# Loop through each source and destination pair
for ($i = 0; $i -lt $SourcePaths.Count; $i++) {
    $SourcePath = $SourcePaths[$i]
    $DestinationUNCPath = $DestinationUNCPaths[$i]

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
            continue
        }

        # Check if the destination path (using drive) is accessible
        if (-Not (Test-Path -Path "${DriveName}:\\")) {
            Write-Host "Error: Destination UNC path '$DestinationUNCPath' is not accessible." -ForegroundColor Red
            continue
        }

        # Ensure the destination directory exists
        $DestinationPath = "${DriveName}:\"
        if (-Not (Test-Path -Path $DestinationPath)) {
            Write-Host "Creating destination directory at '$DestinationPath'..."
            New-Item -Path $DestinationPath -ItemType Directory -Force | Out-Null
        }

        # Copy all files (that start with the specified prefix)
        Write-Host "Copying all files from '$SourcePath' to '$DestinationUNCPath' that start with '$FilePrefix'..."

        # Get all files in the source path that meet the criteria
        $FilesToCopy = Get-ChildItem -Path $SourcePath | Where-Object {
            -Not $_.PSIsContainer -and $_.Name -like "$FilePrefix*"
        }

        # Check if there are any files to copy
        if ($FilesToCopy.Count -eq 0) {
            Write-Host "No files starting with '$FilePrefix' were found in '$SourcePath'." -ForegroundColor Yellow
        } else {
            # Copy each matching file to the destination, skipping files that already exist
            foreach ($File in $FilesToCopy) {
                $SourceFile = $File.FullName
                $DestinationFile = Join-Path -Path $DestinationPath -ChildPath $File.Name

                # Skip if the file already exists in the destination
                if (Test-Path -Path $DestinationFile) {
                    Write-Host "Skipping: $DestinationFile (already exists)" -ForegroundColor Yellow
                    continue
                }

                # Copy the file (no -Force, so it won't overwrite)
                Copy-Item -Path $SourceFile -Destination $DestinationFile
                Write-Host "Copied: $SourceFile -> $DestinationFile" -ForegroundColor Green
            }

            Write-Host "All files copied successfully!" -ForegroundColor Green
        }
    } catch {
        Write-Host "Error: An error occurred while processing source '$SourcePath' and destination '$DestinationUNCPath'. $_" -ForegroundColor Red
    } finally {
        # Remove the temporary drive
        Remove-PSDrive -Name $DriveName -Force -ErrorAction SilentlyContinue
        Write-Host "Temporary drive '$DriveName' removed for destination '$DestinationUNCPath'."
    }
}