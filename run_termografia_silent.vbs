' Script VBS para executar o aplicativo sem mostrar janela de console
' Útil para criar um atalho "limpo" no desktop

Set WshShell = CreateObject("WScript.Shell")

' Obtém o diretório do script
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

' Executa o bat de forma oculta (0 = oculto)
WshShell.Run Chr(34) & scriptDir & "\run_termografia.bat" & Chr(34), 0, False

Set WshShell = Nothing
