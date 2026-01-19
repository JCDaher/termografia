@echo off
echo ========================================
echo   Criando Atalho - Termografia Medica
echo ========================================
echo.

REM Cria um script VBS temporario para criar o atalho
echo Set WshShell = CreateObject("WScript.Shell") > %TEMP%\create_shortcut.vbs
echo DesktopPath = WshShell.SpecialFolders("Desktop") >> %TEMP%\create_shortcut.vbs
echo Set Shortcut = WshShell.CreateShortcut(DesktopPath ^& "\Termografia Medica.lnk") >> %TEMP%\create_shortcut.vbs
echo Shortcut.TargetPath = "%~dp0run_termografia.bat" >> %TEMP%\create_shortcut.vbs
echo Shortcut.WorkingDirectory = "%~dp0" >> %TEMP%\create_shortcut.vbs
echo Shortcut.Description = "Aplicativo de Termografia Medica" >> %TEMP%\create_shortcut.vbs
echo Shortcut.Save >> %TEMP%\create_shortcut.vbs

REM Executa o script VBS
cscript //nologo %TEMP%\create_shortcut.vbs

REM Remove o script temporario
del %TEMP%\create_shortcut.vbs

echo.
echo Atalho criado com sucesso na Area de Trabalho!
echo.
pause
