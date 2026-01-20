# Solução de Problemas - API Key

## ❌ Erro: "Erro ao descriptografar dados"

### Causa
Este erro acontece quando a **API key foi configurada em um ambiente diferente** do atual:
- Configurada em outro computador (ex: Mac → Windows)
- Configurada com outro usuário do sistema
- Sistema operacional foi reinstalado
- Nome do computador (hostname) mudou

A criptografia usa informações da máquina para gerar a chave, então **não é possível transferir credenciais entre máquinas**.

### ✅ Solução Rápida (via Interface)

1. **Quando o erro aparecer**, clique em **"Yes"** na mensagem
2. A aplicação vai:
   - Deletar as credenciais antigas automaticamente
   - Abrir a aba **Configurações**
3. **Insira sua API key** da Anthropic novamente
4. Clique em **"Salvar API Key"**
5. Pronto! Agora você pode gerar laudos normalmente

### ✅ Solução Manual (via Linha de Comando)

Se preferir fazer manualmente no Windows:

```bash
# 1. Entre no diretório do projeto
cd \home\user\termografia

# 2. Ative o ambiente virtual
venv\Scripts\activate

# 3. Abra o Python
python

# 4. Execute:
from config.security import get_security_manager
sm = get_security_manager()
sm.delete_api_key()
print("Credenciais deletadas!")
exit()

# 5. Agora rode a aplicação e configure novamente
python main.py
```

### 🔑 Onde conseguir uma API Key?

1. Acesse: **https://console.anthropic.com/settings/keys**
2. Faça login com sua conta Anthropic
3. Clique em **"Create Key"**
4. Copie a chave (começa com `sk-ant-api03-...`)
5. **IMPORTANTE**: Guarde em local seguro - você não poderá vê-la novamente!

### 📍 Onde ficam armazenadas as credenciais?

As credenciais são armazenadas de forma criptografada em:

**Windows:**
```
%APPDATA%\TermografiaApp\credentials.dat
%APPDATA%\TermografiaApp\.key
```

Exemplo: `C:\Users\SeuUsuario\AppData\Roaming\TermografiaApp\`

**macOS:**
```
~/Library/Application Support/TermografiaApp/credentials.dat
~/Library/Application Support/TermografiaApp/.key
```

**Linux:**
```
~/.config/termografia/credentials.dat
~/.config/termografia/.key
```

### ⚠️ Importante

- **NÃO compartilhe** o arquivo `credentials.dat` entre máquinas - não funcionará!
- **NÃO commite** esses arquivos no Git - são específicos por máquina
- Cada máquina precisa ter sua própria configuração da API key
- A mesma API key pode ser usada em múltiplas máquinas, mas cada uma precisa configurá-la separadamente

### 🔒 Segurança

A aplicação usa:
- **Fernet (AES-128)** para criptografia simétrica
- **PBKDF2-SHA256** com 100.000 iterações para derivação de chave
- **Salt baseado na máquina**: nome do host + sistema operacional + usuário
- Chave única por máquina/usuário

Isso garante que mesmo se alguém copiar o arquivo `credentials.dat`, não conseguirá descriptografar em outra máquina.

### 📞 Suporte

Se o problema persistir após reconfigurar:

1. Verifique se a API key está correta (copie/cole diretamente do console Anthropic)
2. Verifique se tem saldo/créditos na sua conta Anthropic
3. Teste a conectividade: vá em **Configurações > Testar Conexão**
4. Verifique os logs em `termografia.log` para mais detalhes

---

**Última atualização:** 2026-01-20
**Versão da aplicação:** 2.0.0
