#!/bin/bash
# Script de configuração inicial para Linux

echo "================================"
echo "Termografia Médica - Setup Linux"
echo "================================"
echo ""

# Verifica se Python 3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado!"
    echo "Por favor, instale Python 3:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "  Fedora: sudo dnf install python3 python3-pip"
    echo "  Arch: sudo pacman -S python python-pip"
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
echo "  ./run_termografia.sh"
echo ""
echo "Se necessário, torne o script executável:"
echo "  chmod +x run_termografia.sh"
echo ""
