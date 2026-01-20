# Como Criar Atalho no macOS

Este guia mostra 3 formas de criar um atalho fácil para executar o aplicativo Termografia no macOS.

## Método 1: Script Automático (Mais Fácil) ✅

Execute o script que cria automaticamente um aplicativo .app:

```bash
cd ~/termografia
chmod +x criar_app_macos.sh
./criar_app_macos.sh
```

Isso cria `Termografia.app` que você pode:
- **Duplo clicar** para executar
- **Arrastar para /Applications** (Pasta Aplicativos)
- **Arrastar para o Dock** para acesso rápido
- **Adicionar ao Launchpad**

Se o macOS bloquear por segurança:
```bash
xattr -cr ~/termografia/Termografia.app
```

---

## Método 2: Automator (GUI do macOS)

### Passo a Passo:

1. **Abra o Automator**
   - Pressione `Cmd + Espaço`
   - Digite "Automator"
   - Pressione Enter

2. **Crie Novo Documento**
   - Escolha: **Aplicativo**
   - Clique em "Escolher"

3. **Adicione Ação de Terminal**
   - Na barra de busca, digite: "Executar Script de Shell"
   - Arraste "Executar Script de Shell" para o painel direito

4. **Cole o Script**
   ```bash
   cd ~/termografia

   if [ -f "venv/bin/python" ]; then
       ./venv/bin/python main.py
   else
       python3 main.py
   fi
   ```

5. **Salve o Aplicativo**
   - Menu: Arquivo > Salvar
   - Nome: "Termografia"
   - Local: Área de Trabalho (ou /Applications)
   - Clique em "Salvar"

6. **Use o Aplicativo**
   - Duplo clique no ícone criado
   - Adicione ao Dock arrastando

### Adicionar Ícone Personalizado (Opcional):

1. Encontre uma imagem de termografia (PNG/JPG)
2. Abra a imagem no Preview
3. Selecione tudo (Cmd+A) e copie (Cmd+C)
4. Clique com botão direito no app Termografia
5. Escolha "Obter Informações"
6. Clique no ícone pequeno no topo
7. Cole (Cmd+V)

---

## Método 3: Atalho via Finder

### Criar Alias (Atalho):

1. **No Finder, navegue até:**
   ```
   ~/termografia
   ```

2. **Localize o arquivo:**
   ```
   run_termografia.command
   ```

3. **Crie um Alias:**
   - Clique com botão direito no arquivo
   - Escolha "Criar Alias"
   - Renomeie para "Termografia"

4. **Mova o Alias:**
   - Arraste o alias para:
     - Área de Trabalho
     - /Applications
     - Dock
     - Barra lateral do Finder

---

## Método 4: AppleScript (Avançado)

Crie um arquivo chamado `Termografia.scpt` com:

```applescript
tell application "Terminal"
    activate
    do script "cd ~/termografia && ./run_termografia.command"
end tell
```

Depois salve como **Aplicativo** no Editor de Scripts.

---

## Solução de Problemas

### "Não é possível abrir porque é de desenvolvedor não identificado"

**Solução 1:**
```bash
xattr -cr ~/termografia/Termografia.app
```

**Solução 2:**
1. System Preferences > Segurança e Privacidade
2. Clique em "Abrir Mesmo Assim"

**Solução 3:**
- Ctrl + Click no app
- Escolha "Abrir"
- Confirme "Abrir"

### Aplicativo não encontra Python/dependências

Certifique-se de ter executado o setup:
```bash
cd ~/termografia
./setup_macos.sh
```

### Terminal fecha muito rápido

Edite o script para adicionar uma pausa:
```bash
./venv/bin/python main.py
echo "Pressione qualquer tecla para fechar..."
read -n 1
```

---

## Dicas Extras

### Adicionar ao Launchpad
Após criar o app em /Applications, ele aparecerá automaticamente no Launchpad.

### Criar Atalho de Teclado
1. System Preferences > Teclado > Atalhos
2. App Shortcuts > +
3. Escolha o aplicativo Termografia
4. Defina um atalho (ex: Cmd+Shift+T)

### Abrir ao Iniciar o Mac
1. System Preferences > Usuários e Grupos
2. Login Items
3. Clique em + e adicione Termografia.app

---

## Resumo Rápido

**Para usuários iniciantes:**
```bash
cd ~/termografia
./criar_app_macos.sh
# Duplo clique em Termografia.app
```

**Para usar Automator:**
1. Abra Automator
2. Novo > Aplicativo
3. Adicione "Executar Script de Shell"
4. Cole o script de execução
5. Salve como "Termografia"

Pronto! 🎉
