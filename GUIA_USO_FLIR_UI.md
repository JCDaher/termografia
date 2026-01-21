# Guia de Uso - Integração FLIR na Interface

## 🎯 Visão Geral Rápida

A interface agora possui **integração completa com FLIR Thermal Studio**, permitindo importar medições de referência e validar automaticamente a precisão do sistema.

## 🚀 Como Usar (Passo a Passo)

### 1. Importar Dados FLIR

**Opção A: Botão na Toolbar**
1. Clique no botão **"📥 Importar FLIR HTML"** na barra superior
2. Selecione o arquivo HTML exportado do FLIR Thermal Studio
3. Veja resumo das medições importadas

**Opção B: Menu FLIR**
1. Menu **FLIR** → **Importar FLIR HTML...**
2. Ou use o atalho: **Ctrl+F**

**Resultado:**
- ✅ Dialog mostra quantas imagens e medições foram importadas
- 🔵 Indicador FLIR na toolbar muda para **"FLIR: ✓ (N)"** (azul)

### 2. Processar Imagens (com validação automática)

**Após importar FLIR, processe normalmente:**

1. Importe sua(s) imagem(ns) térmica(s): **"📁 Importar Imagem(ns) FLIR"**
2. Processe:
   - **Opção 1:** Desenhe ROIs manualmente → **"⚙️ Processar Atual"**
   - **Opção 2:** Use detecção automática → **"🔥 Processar Todas (Auto)"**

**O que acontece automaticamente:**
- ✅ Sistema calcula temperaturas
- ✅ Valida contra medições FLIR importadas
- ✅ Indicador FLIR atualiza com resultado:
  - 🟢 **"FLIR: ✓✓ 95%"** (verde) = Precisão ≥ 90%
  - 🟠 **"FLIR: ✓ 78%"** (laranja) = Precisão 70-90%
  - 🔴 **"FLIR: ⚠ 62%"** (vermelho) = Precisão < 70%

### 3. Ver Relatório de Validação Detalhado

**Para ver estatísticas completas:**

1. **Passe o mouse** sobre o indicador FLIR na toolbar
   - Tooltip mostra resumo: precisão, ROIs, diferenças

2. **Clique no menu FLIR** → **"Ver Relatório de Validação"**
   - Ou use: **Ctrl+Shift+V**
   - Mostra relatório completo com:
     - ✅ ROIs OK (diferença < 0.5°C)
     - ⚠️ ROIs Warning (diferença 0.5-1.0°C)
     - ❌ ROIs Error (diferença > 1.0°C)
     - Estatísticas: diferença média, máxima, desvio padrão

### 4. Gerar Laudo (com dados FLIR)

**Quando gerar laudo:**

1. Clique em **"📄 Gerar Laudo"**

**O que acontece automaticamente:**
- ✅ Sistema detecta que FLIR foi importado
- ✅ Adiciona medições FLIR ao prompt do Claude AI
- ✅ Inclui estatísticas de validação
- ✅ Claude AI usa dados mais precisos para gerar o laudo

**O laudo gerado:**
- Usa medições validadas
- Pode mencionar validação FLIR (se relevante)
- Maior precisão e confiabilidade

### 5. Limpar Dados FLIR (quando necessário)

**Para remover dados FLIR importados:**

1. Menu **FLIR** → **"Limpar Dados FLIR"**
2. Confirme a ação

**Resultado:**
- ✅ Dados FLIR removidos
- Indicador volta para: **"FLIR: ✗"** (cinza)

## 📊 Indicadores Visuais

### Barra de Status FLIR (Toolbar - Direita)

| Indicador | Cor | Significado |
|-----------|-----|-------------|
| **FLIR: ✗** | Cinza | Nenhum dado FLIR importado |
| **FLIR: ✓ (18)** | Azul | 18 medições FLIR importadas, aguardando processamento |
| **FLIR: ✓✓ 95%** | Verde | Validação OK - Precisão ≥ 90% |
| **FLIR: ✓ 75%** | Laranja | Validação moderada - 70-90% |
| **FLIR: ⚠ 65%** | Vermelho | Baixa precisão - < 70% |

**Tooltip (ao passar mouse):**
```
Validação FLIR:
Precisão: 95.2%
ROIs: 17/18
✅ OK: 16
⚠️ Warning: 1
❌ Error: 0

Estatísticas:
Diff média: 0.08°C
Diff máxima: 0.25°C
```

## ⌨️ Atalhos de Teclado

| Atalho | Ação |
|--------|------|
| **Ctrl+F** | Importar FLIR HTML |
| **Ctrl+Shift+V** | Ver Relatório de Validação |

## 💡 Casos de Uso

### Caso 1: Validar Precisão do Sistema

**Objetivo:** Verificar se o sistema está medindo temperaturas corretamente.

**Passos:**
1. Processar imagem no FLIR Thermal Studio
2. Desenhar ROIs e exportar HTML
3. Processar mesma imagem no sistema
4. Importar HTML FLIR
5. Ver relatório de validação
6. Ajustar se necessário

### Caso 2: Gerar Laudo com Referência FLIR

**Objetivo:** Laudo com máxima precisão usando dados FLIR.

**Passos:**
1. Exportar medições FLIR em HTML
2. Importar HTML no sistema
3. Processar imagens
4. Gerar laudo (automaticamente usa dados FLIR)

### Caso 3: Processar Múltiplas Imagens com Validação

**Objetivo:** Batch processing com validação.

**Passos:**
1. Importar FLIR HTML (com todas as medições)
2. Importar todas as imagens térmicas
3. **"🔥 Processar Todas (Auto)"**
4. Sistema valida cada imagem automaticamente
5. Gerar laudo consolidado

## ⚠️ Troubleshooting

### Problema: Baixa precisão (<70%)

**Possíveis causas:**
- ROIs desenhadas em posições diferentes
- Imagem diferente entre FLIR e sistema
- Nomes de ROIs não correspondem

**Solução:**
1. Ver relatório detalhado (Ctrl+Shift+V)
2. Verificar quais ROIs têm maior diferença
3. Redesenhar ROIs em posições idênticas
4. Usar nomes padronizados

### Problema: ROIs não correspondem

**Sintoma:** Muitas "ROIs não encontradas" no relatório

**Solução:**
- Sistema usa "fuzzy matching" automático
- Exemplo: "Joelho Dir" corresponde a "Joelho Direito"
- Padronize nomenclatura:
  - ✅ "Joelho Direito", "C5 Esquerdo"
  - ❌ "Sp1", "ROI01"

### Problema: FLIR importado mas não valida

**Sintoma:** Indicador fica azul mesmo após processar

**Causa:** Nenhuma ROI do sistema corresponde ao FLIR

**Solução:**
1. Ver relatório de validação
2. Verificar nomes das ROIs
3. Usar nomes similares aos do FLIR

## 🎓 Dicas de Uso

### Padronização de Nomes

**No FLIR Thermal Studio, use nomes descritivos:**
- ✅ "Joelho Direito"
- ✅ "C5 Esquerdo"
- ✅ "Tender Point Occipital Dir"

**No sistema, use nomes idênticos ou similares:**
- Sistema reconhece variações automaticamente
- "Joelho Dir" = "Joelho Direito" ✅

### Organização de Arquivos

**Estrutura recomendada:**
```
pacientes/
├── joao_silva/
│   ├── 2024-01-15/
│   │   ├── imagens/
│   │   │   ├── IR_joelhos.jpg
│   │   │   └── IR_coluna.jpg
│   │   └── flir/
│   │       └── export_joao_2024-01-15.html
```

### Fluxo Ideal

**Sequência recomendada:**
1. 📥 Importar FLIR HTML **PRIMEIRO**
2. 📁 Importar imagens térmicas
3. ⚙️ Processar (manual ou automático)
4. 👁️ Ver validação (se necessário)
5. 📄 Gerar laudo

**Por quê nesta ordem?**
- FLIR primeiro → validação automática
- Feedback imediato de precisão
- Laudos já incluem dados validados

## 📚 Documentação Completa

Para detalhes técnicos e casos avançados, consulte:
- **`FLIR_HTML_IMPORT.md`** - Detalhes do parser e formato HTML
- **`INTEGRACAO_FLIR_COMPLETA.md`** - Integração completa e API
- **`TEMPLATES_ANATOMICOS.md`** - Sistema de templates multi-ponto

## ✨ Recursos Avançados (Futuros)

### Em desenvolvimento:
- [ ] Gráficos de validação (scatter plot sistema vs FLIR)
- [ ] Histórico de precisão ao longo do tempo
- [ ] Templates a partir de FLIR HTML
- [ ] Exportar relatório de validação em PDF

---

**Versão:** 2.0.0
**Data:** 2026-01-21
**Integração FLIR:** ✅ Completa e Funcional

## 🎉 Resumo

A integração FLIR na interface oferece:
- ✅ **Importação fácil** com 1 clique
- ✅ **Validação automática** em tempo real
- ✅ **Feedback visual** colorido
- ✅ **Laudos enriquecidos** com dados FLIR
- ✅ **Relatórios detalhados** de precisão

**Tudo integrado, intuitivo e pronto para uso!** 🚀
