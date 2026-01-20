# 📘 Guia de Uso - Sistema de Termografia Médica

## 🔥 IMPORTANTE: Instalar Suporte a Dados Térmicos FLIR

**ANTES DE USAR O SISTEMA**, instale o suporte para extração de dados térmicos reais:

```bash
./install_flir_support.sh
```

Isso instala a biblioteca `flirimageextractor` que extrai temperaturas REAIS das imagens FLIR.

**Por que isso é necessário?**
- ✅ Extrai dados térmicos REAIS embutidos nas imagens FLIR
- ✅ Temperaturas PRECISAS em °C
- ✅ Análise termográfica CONFIÁVEL

Sem isso, o sistema usará apenas aproximações baseadas na imagem visível!

📖 Leia: `CORRECAO_DADOS_TERMICOS.md` para mais detalhes

---

## 🚀 Início Rápido

### 1. Configurar API Key da Anthropic

**Antes de tudo**, você precisa configurar sua chave API do Claude:

1. Abra o aplicativo
2. Vá em **Configurações** (aba no canto direito)
3. Cole sua API Key da Anthropic
4. Clique em **Salvar API Key**

> ⚠️ **Importante**: Sem a API Key configurada, você não poderá gerar laudos!

---

## 📊 Processamento de Uma Única Imagem

### Passo 1: Importar Imagem FLIR

1. Menu **Arquivo > Importar Imagem FLIR**
2. Selecione uma imagem térmica `.jpg`, `.jpeg`, `.png` ou `.bmp`
3. A imagem aparecerá na tela principal

### Passo 2: Desenhar ROIs (Regiões de Interesse)

1. Menu **Ferramentas > Editor de ROIs**
2. Uma nova janela abre com a imagem

**Como desenhar:**

- **Polígono** (padrão):
  - Clique para adicionar pontos
  - Clique com botão **direito** para fechar o polígono

- **Retângulo**:
  - Selecione "Retângulo" no menu
  - Clique e arraste

- **Elipse**:
  - Selecione "Elipse" no menu
  - Clique e arraste

3. Quando finalizar o desenho, digite um nome para a ROI
   - Use nomes como: **"Esquerdo"**, **"Direito"**, **"Esq"**, **"Dir"**
   - Isso permite detecção automática de lateralidade

4. Desenhe todas as ROIs necessárias

5. Clique em **"Salvar ROIs"**

> ✅ **As temperaturas aparecem imediatamente** após salvar!

### Passo 3: Processar a Imagem

1. Clique no botão **"Processar"** (⚙️)
2. O sistema:
   - Identifica automaticamente ROIs esquerda/direita
   - Preenche os campos de temperatura
   - Calcula o ΔT (diferença térmica)
   - Classifica a assimetria

### Passo 4: Gerar Laudo Profissional

1. Preencha os campos obrigatórios:
   - Nome do paciente
   - Indicação clínica
   - Dermátomo sendo analisado

2. Clique em **"Gerar Laudo"** (📄)

3. O Claude AI gerará um laudo profissional completo seguindo o formato médico padronizado

4. Revise e edite o laudo se necessário

5. Clique em **"Salvar Laudo"** ou **"Exportar PDF"**

---

## 📦 Processamento em Lote (Múltiplas Imagens)

### Ideal para processar 50+ imagens rapidamente!

### Passo 1: Carregar Múltiplas Imagens

1. Menu **Arquivo > Importar Imagem FLIR**
2. **Selecione múltiplas imagens** (Ctrl+clique ou Shift+clique)
3. Todas aparecerão na lista lateral

### Passo 2: Preparar Template de ROIs

1. Selecione a **primeira imagem** na lista
2. Abra o **Editor de ROIs**
3. Desenhe as ROIs que serão usadas em **todas** as imagens
   - Exemplo: ROI "Esquerdo" e ROI "Direito" na região cervical
4. **Salvar ROIs**

### Passo 3: Processar Todas as Imagens

1. Clique em **"Processar Todas"** (⚙️)
2. Escolha **"SIM"** para usar as mesmas ROIs em todas as imagens
3. Aguarde o processamento (barra de progresso aparece)
4. Ao final, você verá:
   - Total de imagens processadas
   - Estatísticas gerais (ΔT médio, máximo, mínimo)
   - Distribuição das classificações

### Passo 4: Gerar Laudo Consolidado

1. Clique em **"Gerar Laudo"** (📄)
2. O sistema gera automaticamente um laudo profissional com:
   - Análise de todas as imagens processadas
   - Estatísticas consolidadas
   - Tabela com resultados individuais
   - Conclusões baseadas no conjunto completo

---

## 🔍 Verificação de Problemas

### ❌ "Botão Processar não funciona"

**Causa**: Provavelmente não há ROIs desenhadas

**Solução**:
1. Verifique se você desenhou e salvou ROIs
2. Abra o Editor de ROIs novamente
3. Certifique-se de clicar em "Salvar ROIs" após desenhar

### ❌ "Temperaturas não aparecem"

**Causas possíveis**:
- Imagem não contém dados térmicos EXIF
- ROIs desenhadas fora da área da imagem
- ROIs muito pequenas

**Solução**:
1. Verifique se a imagem é realmente FLIR (deve ter metadados de temperatura)
2. Redesenhe as ROIs garantindo que estão dentro da imagem
3. Faça ROIs maiores (pelo menos 10x10 pixels)
4. Veja os **logs** para diagnóstico detalhado

### ❌ "Gerar Laudo não está clicável"

**Causa**: Você precisa processar primeiro

**Solução**:
1. Clique em "Processar" **antes** de "Gerar Laudo"
2. Aguarde a conclusão do processamento
3. O botão "Gerar Laudo" será habilitado automaticamente

### ❌ "Processar Todas não aparece"

**Causa**: Você importou apenas 1 imagem

**Solução**:
- "Processar Todas" só aparece quando você tem **2 ou mais** imagens carregadas
- Importe múltiplas imagens usando Ctrl+clique na seleção

---

## 📝 Dicas e Boas Práticas

### Nomenclatura de ROIs

Para detecção automática de lateralidade, use nomes que contenham:

- **Esquerdo**: `esq`, `left`, `e`, `Esquerdo`, `Left`
- **Direito**: `dir`, `right`, `d`, `Direito`, `Right`

Exemplos:
- ✅ "C5 Esquerdo" e "C5 Direito"
- ✅ "Esq" e "Dir"
- ✅ "Left shoulder" e "Right shoulder"
- ❌ "ROI 1" e "ROI 2" (não detecta lateralidade)

### Desenho de ROIs Precisas

1. **Polígono** é o mais preciso para áreas irregulares
2. **Retângulo** é rápido para áreas retangulares
3. **Elipse** é ideal para áreas circulares/ovais

### Fluxo de Trabalho Otimizado

Para 50+ imagens:

1. ⬇️ Carregue TODAS as imagens de uma vez
2. 🎨 Desenhe ROIs apenas na primeira imagem
3. ⚙️ Use "Processar Todas" com template de ROIs
4. 📄 Gere um laudo consolidado único

Economiza tempo e garante consistência!

---

## 🆘 Suporte

### Ver Logs Detalhados

Os logs aparecem no terminal onde você iniciou o aplicativo.

Para executar com logs visíveis:

**macOS/Linux:**
```bash
./venv/bin/python main.py
```

**Windows:**
```bash
venv\Scripts\python.exe main.py
```

### Reportar Problemas

Se encontrar bugs, reporte em:
- GitHub: https://github.com/anthropics/claude-code/issues

---

## ⚡ Atalhos de Teclado

| Atalho | Função |
|--------|--------|
| `Ctrl+O` | Abrir/Importar imagem |
| `Ctrl+S` | Salvar laudo |
| `Ctrl+P` | Exportar PDF |
| `Ctrl+Q` | Sair |
| `F1` | Ajuda |

---

## 📖 Informações Adicionais

### Formato do Laudo Profissional

O laudo segue o formato médico padronizado com 10 seções obrigatórias:

1. **TÉCNICA** - Equipamento e metodologia
2. **IMPRESSÃO DIAGNÓSTICA** - Achados por categoria
3. **DESCRIÇÃO** - Detalhamento das áreas examinadas
4. **PROCEDIMENTO** - Protocolo de aquisição
5. **RELATÓRIO** - Análise dermatomérica detalhada
6. **RESULTADOS DO EXAME** - Tabela de valores
7. **VALORES NORMAIS** - Referências de normalidade
8. **VALORES ANORMAIS** - Achados patológicos
9. **OBSERVAÇÕES** - Notas técnicas
10. **CONCLUSÃO** - Síntese diagnóstica

### Classificação de Assimetria Térmica

- **Normal**: ΔT < 0.5°C
- **Leve**: 0.5°C ≤ ΔT < 1.0°C
- **Moderada**: 1.0°C ≤ ΔT < 1.5°C
- **Severa**: ΔT ≥ 1.5°C

---

**Desenvolvido com Claude AI** 🤖
