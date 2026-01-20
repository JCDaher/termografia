#!/bin/bash
# Script de inicialização para Linux
# Execute: ./run_termografia.sh

# Obtém o diretório do script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Ativa o ambiente virtual se existir
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Executa o aplicativo
python3 main.py
