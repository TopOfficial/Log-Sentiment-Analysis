# Define parameters for the script
param(
    [string[]]$SourcePaths = @("path/to/your/network/directory1", "path/to/your/network/directory2", "path/to/your/network/directoryXX"), # Example source paths
    [string]$FilePrefix = "TEC_", # Prefix for filtering files
    [int]$FileAgeInDays = 30, # File retention period in days
    [string]$CredentialPath = "path/to/your/directory/file.xml"
)

# Import credentials from a secure file
if (-Not (Test-Path -Path $CredentialPath)) {
    Write-Host "Error: Credential file '$CredentialPath' not found." -ForegroundColor Red
    exit 1
}
$Credential = Import-Clixml -Path $CredentialPath

# Loop through each source path
foreach ($SourcePath in $SourcePaths) {
    try {
        # Check if the source path exists
        if (-Not (Test-Path -Path $SourcePath)) {
            Write-Host "Error: Source path '$SourcePath' does not exist." -ForegroundColor Red
            continue
        }

        # Get the current date and calculate the cutoff date
        $CutoffDate = (Get-Date).AddDays(-$FileAgeInDays)

        # Get all files in the source path that meet the criteria
        $FilesToDelete = Get-ChildItem -Path $SourcePath | Where-Object {
            -Not $_.PSIsContainer -and $_.Name -like "$FilePrefix*" -and $_.LastWriteTime -lt $CutoffDate
        }

        # Check if there are any files to delete
        if ($FilesToDelete.Count -eq 0) {
            Write-Host "No files older than $FileAgeInDays days with prefix '$FilePrefix' were found in '$SourcePath'." -ForegroundColor Yellow
        } else {
            # Delete each matching file
            foreach ($File in $FilesToDelete) {
                try {
                    $FilePath = $File.FullName

                    # Delete the file
                    Remove-Item -Path $FilePath -Force
                    Write-Host "Deleted: $FilePath" -ForegroundColor Green
                } catch {
                    Write-Host "Error: Failed to delete file '$FilePath'. $_" -ForegroundColor Red
                }
            }

            Write-Host "All files older than $FileAgeInDays days have been deleted from '$SourcePath'." -ForegroundColor Green
        }
    } catch {
        Write-Host "Error: An error occurred while processing source '$SourcePath'. $_" -ForegroundColor Red
    }
}