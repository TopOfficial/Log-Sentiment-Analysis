$Credential = Get-Credential
$Credential | Export-Clixml -Path "path/to/your/directory/file.xml"