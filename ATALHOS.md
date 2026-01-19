# 🚀 Atalhos para Iniciar o Aplicativo

Este documento explica como usar os atalhos criados para facilitar a inicialização do aplicativo de Termografia Médica.

---

## 📋 Arquivos de Atalho Disponíveis

### 1. **run_termografia.bat** (Recomendado)
Arquivo batch que ativa o ambiente virtual e executa o aplicativo.

**Como usar:**
- Clique duplo no arquivo `run_termografia.bat`
- O aplicativo será iniciado automaticamente

**Características:**
- Mostra mensagens de status no console
- Útil para ver erros se houver problemas
- Mantém a janela aberta em caso de erro

---

### 2. **run_termografia_silent.vbs** (Modo Silencioso)
Script VBS que executa o aplicativo sem mostrar janela de console.

**Como usar:**
- Clique duplo no arquivo `run_termografia_silent.vbs`
- O aplicativo abre diretamente sem janela de console

**Características:**
- Interface mais limpa (sem console)
- Ideal para uso diário
- Não mostra mensagens de status

---

### 3. **criar_atalho_desktop.ps1** (Criador de Atalho)
Script PowerShell que cria atalhos na Área de Trabalho e Menu Iniciar.

**Como usar:**

1. Abra o PowerShell como Administrador
2. Navegue até a pasta do projeto:
   ```powershell
   cd C:\Users\Win10\Documents\termografia
   ```
3. Execute o script:
   ```powershell
   powershell -ExecutionPolicy Bypass -File criar_atalho_desktop.ps1
   ```
4. Siga as instruções na tela

**Resultado:**
- Cria atalho "Termografia Médica" na Área de Trabalho
- Opcionalmente cria atalho no Menu Iniciar
- Usa ícone personalizado se disponível (icon.ico)

---

## 🎯 Qual Atalho Usar?

| Situação | Atalho Recomendado |
|----------|-------------------|
| **Uso diário** | `run_termografia_silent.vbs` |
| **Primeira vez / Testes** | `run_termografia.bat` |
| **Criar atalho permanente** | `criar_atalho_desktop.ps1` |
| **Debugging / Ver erros** | `run_termografia.bat` |

---

## 🖼️ Adicionar Ícone Personalizado (Opcional)

Para usar um ícone personalizado:

1. Coloque um arquivo `icon.ico` na pasta do projeto
2. Execute novamente o `criar_atalho_desktop.ps1`
3. O atalho será atualizado com o novo ícone

**Onde encontrar ícones:**
- [Flaticon](https://www.flaticon.com/) - Busque por "medical" ou "thermometer"
- [Icons8](https://icons8.com/) - Baixe em formato .ico
- Crie o seu usando um conversor PNG → ICO online

---

## 🔧 Solução de Problemas

### Erro: "Ambiente virtual não encontrado"
**Solução:**
```powershell
cd C:\Users\Win10\Documents\termografia
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Erro: "Não é possível executar scripts"
**Solução para PowerShell:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Aplicativo não abre
**Solução:**
1. Execute `run_termografia.bat` (mostra erros no console)
2. Verifique o log: `logs\termografia.log`
3. Confirme que todas as dependências estão instaladas

---

## 📌 Dica: Fixar na Barra de Tarefas

Após criar o atalho:

1. Vá para a Área de Trabalho
2. Clique com botão direito em "Termografia Médica"
3. Selecione "Fixar na barra de tarefas"
4. Pronto! Acesso com 1 clique

---

## ⚡ Início Rápido

**Método mais rápido para começar:**

1. Abra PowerShell na pasta do projeto
2. Execute:
   ```powershell
   powershell -ExecutionPolicy Bypass -File criar_atalho_desktop.ps1
   ```
3. Vá para a Área de Trabalho
4. Clique duplo em "Termografia Médica"
5. Pronto! 🎉

---

## 📝 Notas

- Os atalhos funcionam mesmo se você mover a pasta do projeto (eles usam caminhos relativos)
- Se mover o projeto, execute novamente o `criar_atalho_desktop.ps1`
- O atalho `.bat` sempre mostra o diretório atual antes de executar
- Logs de erro são salvos em `logs\termografia.log`

---

**Desenvolvido com ❤️ para facilitar seu trabalho!**
