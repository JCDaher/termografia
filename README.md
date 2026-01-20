# Termografia Médica - Sistema Completo

Aplicativo desktop **multiplataforma** (Windows, macOS, Linux) profissional para análise de imagens termográficas FLIR radiométricas com inteligência artificial.

## 🚀 Funcionalidades - FASE 2 Completa

### 📸 Processamento de Imagens
- ✅ Importação múltipla de imagens FLIR radiométricas
- ✅ Navegação entre imagens (Anterior/Próxima)
- ✅ Geração automática de heatmaps coloridos
- ✅ Visualização de estatísticas térmicas (min/max/média/desvio)
- ✅ Toggle entre imagem original e heatmap

### 🎨 Editor de ROIs Interativo
- ✅ Desenho de polígonos manualmente
- ✅ Desenho de retângulos (click e arraste)
- ✅ Desenho de elipses
- ✅ Nomeação personalizada de ROIs
- ✅ Lista de ROIs com remoção individual
- ✅ Preview em tempo real

### 📊 Análise Térmica
- ✅ Análise de assimetrias em dermátomos (C3-T1)
- ✅ Cálculo automático de ΔT entre lados
- ✅ Classificação: Normal/Leve/Moderada/Severa
- ✅ Análise BTT (Brain Thermal Tunnel) para cefaleias
- ✅ Correlação topográfica dor vs. padrão térmico

### 🤖 Inteligência Artificial
- ✅ Geração automática de laudos com Claude AI (Sonnet 4.5)
- ✅ System prompts especializados para dermátomos e BTT
- ✅ Interpretação clínica fundamentada
- ✅ Sugestões de conduta e exames complementares

### ✍️ Editor de Laudos Profissional
- ✅ Revisão e edição de laudos gerados
- ✅ Formatação Markdown (negrito, itálico, cabeçalhos, listas)
- ✅ 3 tabs: Editor / Metadados / Pré-visualização
- ✅ Campos para médico responsável (Nome, CRM, Especialidade)
- ✅ Conclusão e recomendações separadas
- ✅ Tipos de laudo: Preliminar/Final/Complementar
- ✅ Contador de caracteres e palavras
- ✅ Botão restaurar original

### 📄 Exportação PDF Profissional
- ✅ PDFs formatados com ReportLab
- ✅ Cabeçalho com logo e dados do médico
- ✅ Rodapé com data/hora de geração
- ✅ Numeração automática de páginas
- ✅ Formatação automática de seções
- ✅ Inclusão opcional de imagens termográficas
- ✅ Assinatura digital do médico

### 👤 Histórico de Pacientes
- ✅ Busca por nome ou prontuário
- ✅ Visualização de dados do paciente
- ✅ Lista de todos os exames do paciente
- ✅ Detalhes completos de cada exame
- ✅ Carregamento rápido de pacientes/exames anteriores
- ✅ Estatísticas de imagens e laudos

### 💾 Banco de Dados
- ✅ SQLite local (100% offline)
- ✅ Schema completo com 8 tabelas
- ✅ Relacionamentos entre pacientes, exames, imagens, ROIs e laudos
- ✅ Triggers automáticos para updated_at
- ✅ Índices para performance

### 🎨 Temas Personalizáveis
- ✅ Tema Claro (padrão)
- ✅ Tema Escuro (Dark Mode)
- ✅ Tema Azul Médico
- ✅ Toggle rápido Claro/Escuro (Ctrl+T)
- ✅ Paletas de cores otimizadas
- ✅ Stylesheets completos

### ⌨️ Atalhos de Teclado
- `Ctrl+N` - Novo Exame
- `Ctrl+H` - Histórico de Pacientes
- `Ctrl+R` - Editor de ROIs
- `Ctrl+I` - Importar Imagens
- `Ctrl+T` - Toggle Tema Claro/Escuro
- `Ctrl+Q` - Sair

### 🔐 Segurança
- ✅ Criptografia multiplataforma com Fernet (AES-128)
- ✅ Derivação de chave PBKDF2 (100.000 iterações)
- ✅ Salt único por máquina
- ✅ Armazenamento seguro por SO:
  - Windows: `%APPDATA%/TermografiaApp`
  - macOS: `~/Library/Application Support/TermografiaApp`
  - Linux: `~/.config/termografia`
- ✅ Nenhuma credencial em texto plano

## 💻 Instalação

### Windows

```bash
# Clonar repositório
git clone https://github.com/JCDaher/termografia.git
cd termografia

# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Executar
python main.py
```

### macOS

```bash
# Clonar repositório
git clone https://github.com/JCDaher/termografia.git
cd termografia

# Executar setup automático
chmod +x setup_macos.sh
./setup_macos.sh

# Executar aplicativo
chmod +x run_termografia.command
./run_termografia.command
```

### Linux

```bash
# Clonar repositório
git clone https://github.com/JCDaher/termografia.git
cd termografia

# Executar setup automático
chmod +x setup_linux.sh
./setup_linux.sh

# Executar aplicativo
./run_termografia.sh
```

## 🎯 Início Rápido

### Usando Atalhos Windows

**Opção 1: Clique duplo**
```
run_termografia.bat
```

**Opção 2: Criar atalho na área de trabalho**
```
criar_atalho.bat
```

### Primeiro Uso

1. **Configure API Key da Anthropic**
   - Vá para aba "Configurações"
   - Cole sua API key
   - Clique em "Salvar API Key"

2. **Crie um Novo Exame**
   - Menu: Arquivo → Novo Exame (ou Ctrl+N)
   - Preencha dados do paciente
   - Clique em "Criar Novo Exame"

3. **Importe Imagens**
   - Menu: Ferramentas → Importar Imagens (ou Ctrl+I)
   - Selecione múltiplas imagens FLIR (Ctrl+Click)
   - Navegue entre elas com os botões

4. **Desenhe ROIs** (opcional)
   - Menu: Ferramentas → Editor de ROIs (ou Ctrl+R)
   - Escolha modo (Polígono/Retângulo/Elipse)
   - Desenhe as regiões de interesse
   - Nomeie e salve

5. **Analise Assimetrias**
   - Vá para aba "Análise"
   - Digite temperaturas esquerda/direita
   - Selecione o dermátomo
   - Clique em "Analisar Assimetria"

6. **Gere Laudo**
   - Clique em "Gerar Laudo"
   - Aguarde Claude AI processar
   - Revise e edite no Editor de Laudos
   - Salve automaticamente

7. **Exporte PDF**
   - Aba "Laudo" → "Exportar PDF"
   - Escolha local para salvar
   - PDF profissional gerado!

## 📁 Estrutura do Projeto

```
termografia/
├── api/                    # Integração Claude AI
│   ├── claude_client.py
│   └── prompts.py
├── config/                 # Configurações e segurança
│   └── security.py
├── core/                   # Processamento térmico
│   ├── flir_processor.py
│   └── thermal_analyzer.py
├── database/               # Banco de dados
│   ├── schema.sql
│   └── db_manager.py
├── reports/                # Geração de PDFs
│   └── pdf_generator.py
├── ui/                     # Interface PyQt6
│   ├── main_window.py
│   ├── roi_editor.py
│   ├── patient_history.py
│   ├── report_editor.py
│   └── themes.py
├── main.py                 # Entry point
├── requirements.txt
└── README.md
```

## 🛠️ Tecnologias

- **Python 3.11+**
- **PyQt6** - Interface gráfica moderna e multiplataforma
- **OpenCV** - Processamento de imagens
- **NumPy** - Computação numérica
- **Anthropic API** - Claude AI para laudos
- **SQLite** - Banco de dados local
- **ReportLab** - Geração de PDFs
- **Cryptography** - Criptografia Fernet multiplataforma (AES-128)

## 📊 Requisitos do Sistema

### Sistemas Operacionais Suportados
- ✅ Windows 10/11
- ✅ macOS 11 (Big Sur) ou superior
- ✅ Linux (Ubuntu 20.04+, Fedora 35+, Debian 11+)

### Requisitos Mínimos
- Python 3.11 ou superior
- 4GB RAM mínimo (8GB recomendado)
- 500MB espaço em disco
- Conexão com internet (para Claude AI)

## 🔬 Casos de Uso

### Análise de Dermátomos
- Radiculopatias cervicais/lombares
- Hérnias discais
- Compressões nervosas
- Síndrome do túnel do carpo
- SDRC (Síndrome Dolorosa Regional Complexa)

### Análise BTT (Brain Thermal Tunnel)
- Enxaqueca
- Cefaleia tensional
- Cefaleia em salvas
- Cefaleia cervicogênica

### Outras Aplicações
- Medicina esportiva
- Reabilitação
- Avaliação pré/pós-operatória
- Monitoramento de tratamentos

## 📖 Documentação

- `ATALHOS.md` - Guia completo de atalhos do Windows
- `CLAUDE_INSTRUCTIONS.md` - Instruções para desenvolvimento
- Logs em: `logs/termografia.log`
- Banco de dados em: `data/termografia.db`

## 🆘 Suporte e Troubleshooting

### Problemas Comuns

#### macOS: "Cannot open because developer cannot be verified"
```bash
# Remover quarentena do arquivo
xattr -d com.apple.quarantine run_termografia.command

# OU abra com Ctrl+Click > Abrir
```

#### Linux: Missing Qt platform plugin
```bash
# Ubuntu/Debian
sudo apt install python3-pyqt6 libxcb-xinerama0

# Fedora
sudo dnf install python3-qt6
```

#### Windows: DLL load failed
Instale Visual C++ Redistributable:
https://aka.ms/vs/17/release/vc_redist.x64.exe

### Suporte Geral

Em caso de problemas:
1. Verifique `logs/termografia.log`
2. Certifique-se que API key está configurada
3. Confirme que todas dependências estão instaladas
4. Para macOS/Linux: Verifique permissões de execução (`chmod +x`)
5. Abra um issue no GitHub

## 📝 Licença

Uso profissional médico. Todos os direitos reservados.

## 👨‍⚕️ Autor

**Dr. Jorge Cecílio Daher Jr.**
Endocrinologista e Metabologista
CRM-GO 6108

---

**Sistema FASE 2 - 100% Completo e Funcional** 🎉
