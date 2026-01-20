#!/bin/bash
# Script para criar um aplicativo macOS (.app) para o Termografia
# Este app pode ser movido para a pasta Aplicativos ou área de trabalho

APP_NAME="Termografia"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_PATH="$SCRIPT_DIR/${APP_NAME}.app"

echo "================================"
echo "Criando aplicativo macOS"
echo "================================"
echo ""

# Remove app antigo se existir
if [ -d "$APP_PATH" ]; then
    echo "Removendo aplicativo anterior..."
    rm -rf "$APP_PATH"
fi

# Cria estrutura do .app
echo "Criando estrutura do aplicativo..."
mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"

# Cria o Info.plist
echo "Criando Info.plist..."
cat > "$APP_PATH/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Termografia</string>
    <key>CFBundleIdentifier</key>
    <string>com.termografia.app</string>
    <key>CFBundleName</key>
    <string>Termografia</string>
    <key>CFBundleVersion</key>
    <string>2.0</string>
    <key>CFBundleShortVersionString</key>
    <string>2.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Cria o script executável
echo "Criando script executável..."
cat > "$APP_PATH/Contents/MacOS/Termografia" << 'EOF'
#!/bin/bash

# Obtém o diretório do projeto (3 níveis acima)
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ../../.. && pwd )"
cd "$APP_DIR"

# Abre terminal com o aplicativo
osascript <<APPLESCRIPT
tell application "Terminal"
    activate
    do script "cd '$APP_DIR' && ./venv/bin/python main.py; echo ''; echo 'Pressione qualquer tecla para fechar...'; read -n 1"
end tell
APPLESCRIPT
EOF

# Torna o script executável
chmod +x "$APP_PATH/Contents/MacOS/Termografia"

# Tenta criar um ícone (opcional)
if command -v sips &> /dev/null; then
    echo "Criando ícone..."
    # Aqui você pode adicionar um ícone personalizado se tiver um arquivo .png ou .icns
fi

echo ""
echo "================================"
echo "✅ Aplicativo criado com sucesso!"
echo "================================"
echo ""
echo "Localização: $APP_PATH"
echo ""
echo "Para usar:"
echo "1. Duplo clique em 'Termografia.app'"
echo "   OU"
echo "2. Arraste para /Applications"
echo "3. Arraste para o Dock para acesso rápido"
echo ""
echo "Se o macOS bloquear por segurança:"
echo "  1. Vá em Preferências do Sistema > Segurança"
echo "  2. Clique em 'Abrir Mesmo Assim'"
echo "  OU"
echo "  Execute: xattr -cr '$APP_PATH'"
echo ""
