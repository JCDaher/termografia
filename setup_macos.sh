#!/bin/bash
# Script de configuração inicial para macOS

echo "================================"
echo "Termografia Médica - Setup macOS"
echo "================================"
echo ""

# Verifica se Python 3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado!"
    echo "Por favor, instale Python 3 de https://www.python.org/downloads/"
    exit 1
fi

echo "✓ Python 3 encontrado: $(python3 --version)"
echo ""

# Cria ambiente virtual
echo "Criando ambiente virtual..."
python3 -m venv venv

# Ativa ambiente virtual
echo "Ativando ambiente virtual..."
source venv/bin/activate

# Atualiza pip
echo "Atualizando pip..."
pip install --upgrade pip

# Instala dependências
echo "Instalando dependências..."
pip install -r requirements.txt

echo ""
echo "================================"
echo "✅ Instalação concluída!"
echo "================================"
echo ""
echo "Para executar o aplicativo:"
echo "1. Duplo clique em 'run_termografia.command'"
echo "   OU"
echo "2. No terminal: ./run_termografia.command"
echo ""
echo "Primeira execução:"
echo "1. Execute: chmod +x run_termografia.command"
echo "2. Depois: ./run_termografia.command"
echo ""
