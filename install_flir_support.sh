#!/bin/bash

# Script para instalar suporte completo a extração de dados térmicos FLIR
# Instala a biblioteca flirimageextractor

echo "================================================"
echo "  Instalando Suporte a Dados Térmicos FLIR    "
echo "================================================"
echo ""

# Detectar sistema operacional
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
    PYTHON_CMD="./venv/bin/python"
    PIP_CMD="./venv/bin/pip"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
    PYTHON_CMD="./venv/bin/python"
    PIP_CMD="./venv/bin/pip"
else
    OS="Windows"
    PYTHON_CMD="venv\Scripts\python.exe"
    PIP_CMD="venv\Scripts\pip.exe"
fi

echo "Sistema operacional detectado: $OS"
echo ""

# Verificar se ambiente virtual existe
if [ ! -d "venv" ]; then
    echo "❌ Ambiente virtual não encontrado!"
    echo "Execute primeiro: python3 -m venv venv"
    echo "Ou no macOS: ./setup_macos.sh"
    exit 1
fi

echo "✅ Ambiente virtual encontrado"
echo ""

# Atualizar pip
echo "📦 Atualizando pip..."
$PIP_CMD install --upgrade pip

# Instalar flirimageextractor
echo ""
echo "📦 Instalando flirimageextractor..."
$PIP_CMD install flirimageextractor>=1.2.0

# Verificar instalação
echo ""
echo "🔍 Verificando instalação..."
$PYTHON_CMD -c "from flirimageextractor import FlirImageExtractor; print('✅ flirimageextractor instalado com sucesso!')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo ""
    echo "================================================"
    echo "  ✅ Instalação Concluída com Sucesso!         "
    echo "================================================"
    echo ""
    echo "Agora o sistema pode extrair dados térmicos REAIS"
    echo "das imagens FLIR, incluindo temperaturas precisas!"
    echo ""
    echo "Execute o aplicativo:"
    if [[ "$OS" == "macOS" ]] || [[ "$OS" == "Linux" ]]; then
        echo "  ./venv/bin/python main.py"
    else
        echo "  venv\Scripts\python.exe main.py"
    fi
    echo ""
else
    echo ""
    echo "⚠️  Houve um problema na instalação"
    echo "Tente instalar manualmente:"
    echo "  $PIP_CMD install flirimageextractor"
    exit 1
fi
