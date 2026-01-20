#!/bin/bash
# Script de inicialização para macOS
# Duplo clique neste arquivo para executar o aplicativo

# Obtém o diretório do script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Usa Python do ambiente virtual se existir, senão usa Python global
if [ -f "venv/bin/python" ]; then
    echo "Usando Python do ambiente virtual..."
    ./venv/bin/python main.py
elif [ -f "venv/bin/python3" ]; then
    echo "Usando Python3 do ambiente virtual..."
    ./venv/bin/python3 main.py
else
    echo "Ambiente virtual não encontrado, usando Python global..."
    python3 main.py
fi

# Pausa para mostrar erros (se houver)
read -p "Pressione ENTER para fechar..."
