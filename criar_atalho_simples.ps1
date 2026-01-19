# Script simples para criar atalho
$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TargetPath = Join-Path $ScriptDir "run_termografia.bat"
$ShortcutPath = Join-Path $DesktopPath "Termografia Medica.lnk"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetPath
$Shortcut.WorkingDirectory = $ScriptDir
$Shortcut.Description = "Aplicativo de Termografia Medica"
$Shortcut.Save()

Write-Host "Atalho criado com sucesso na Area de Trabalho!" -ForegroundColor Green
Write-Host "Pressione Enter para fechar..."
Read-Host
