@echo off
REM Atalho para iniciar o aplicativo de Termografia Médica
REM Criado automaticamente

echo ========================================
echo   Termografia Médica - Inicializando
echo ========================================
echo.

cd /d "%~dp0"

REM Verifica se o ambiente virtual existe
if not exist "venv\Scripts\python.exe" (
    echo ERRO: Ambiente virtual nao encontrado!
    echo Por favor, crie o ambiente virtual primeiro.
    echo.
    pause
    exit /b 1
)

REM Ativa o ambiente virtual e executa o aplicativo
echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo Iniciando aplicativo...
echo.

python main.py

REM Se houver erro, mantém a janela aberta
if errorlevel 1 (
    echo.
    echo ERRO ao executar o aplicativo!
    echo Verifique os logs em: logs\termografia.log
    echo.
    pause
)
