# Script PowerShell para criar atalho na Área de Trabalho
# Execute com: powershell -ExecutionPolicy Bypass -File criar_atalho_desktop.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Criando Atalho - Termografia Médica  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Caminhos
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TargetPath = Join-Path $ScriptDir "run_termografia.bat"
$IconPath = Join-Path $ScriptDir "icon.ico"
$ShortcutPath = Join-Path $DesktopPath "Termografia Médica.lnk"

# Cria objeto WScript Shell
$WshShell = New-Object -ComObject WScript.Shell

# Cria o atalho
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetPath
$Shortcut.WorkingDirectory = $ScriptDir
$Shortcut.Description = "Aplicativo de Termografia Médica com Claude AI"
$Shortcut.WindowStyle = 1  # Normal

# Define ícone se existir
if (Test-Path $IconPath) {
    $Shortcut.IconLocation = $IconPath
    Write-Host "Ícone personalizado aplicado" -ForegroundColor Green
} else {
    Write-Host "Ícone padrão será usado (icon.ico não encontrado)" -ForegroundColor Yellow
}

# Salva o atalho
$Shortcut.Save()

Write-Host ""
Write-Host "✓ Atalho criado com sucesso!" -ForegroundColor Green
Write-Host "  Local: $ShortcutPath" -ForegroundColor Gray
Write-Host ""

# Pergunta se quer criar também no Menu Iniciar
$Response = Read-Host "Deseja criar atalho no Menu Iniciar também? (S/N)"
if ($Response -eq "S" -or $Response -eq "s") {
    $StartMenuPath = [Environment]::GetFolderPath("StartMenu")
    $StartMenuShortcut = Join-Path $StartMenuPath "Programs\Termografia Médica.lnk"

    $Shortcut2 = $WshShell.CreateShortcut($StartMenuShortcut)
    $Shortcut2.TargetPath = $TargetPath
    $Shortcut2.WorkingDirectory = $ScriptDir
    $Shortcut2.Description = "Aplicativo de Termografia Médica com Claude AI"
    if (Test-Path $IconPath) {
        $Shortcut2.IconLocation = $IconPath
    }
    $Shortcut2.Save()

    Write-Host "✓ Atalho do Menu Iniciar criado!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Pressione qualquer tecla para fechar..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
