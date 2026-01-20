# Detecção de Padrões de Fibromialgia via Termografia

## ✅ O que foi implementado

O sistema agora possui **conhecimento específico sobre padrões termográficos de fibromialgia** integrado ao Claude AI. Quando você gera um laudo, o AI analisa automaticamente os dados procurando por padrões sugestivos.

## 🎯 Padrões que o AI identifica

### 1. **Padrão Periorbicular**
- Alterações térmicas características ao redor dos olhos
- Hiper ou hiporradiação periocular

### 2. **Termorregulação Disfuncional**
- **Hiporradiação de extremidades** (mãos e pés mais frios)
- Contraste térmico entre extremidades e tronco
- Temperaturas distais consistentemente reduzidas bilateralmente

### 3. **Tender Points (Pontos de Dor)**
- Assimetrias térmicas nos 18 tender points clássicos
- Manifestam-se como hiper-radiação ou hiporradiação
- Padrões neurovasculares de sensibilização central

### 4. **Padrão Cervical Superior**
- **Hiporradiação em C7-T1-T2** (região cervical superior fria)
- Áreas frias nas junções articulares
- Padrão em "colar frio"

### 5. **Características Gerais**
- Múltiplas áreas de assimetria **sem padrão dermatomérico claro**
- Distribuição bilateral mas não necessariamente simétrica
- Padrões térmicos complexos e multifocais
- Alterações que não seguem território nervoso específico

## 📊 Como funciona na prática

### Processamento em Lote (50+ imagens)

Quando você usa **"🔥 Processar Todas (Auto)"** e depois gera o laudo:

1. O Claude AI recebe:
   - Temperaturas de cada região (esquerda/direita)
   - Delta T de múltiplas áreas
   - Distribuição de classificações

2. O AI analisa:
   - Se há padrão bilateral de alterações
   - Se há múltiplas assimetrias sem padrão dermatomérico
   - Se há consistência sugestiva de fibromialgia

3. Se identificar padrão sugestivo, o laudo incluirá:
   ```
   IMPRESSÃO DIAGNÓSTICA
   b. Musculoesquelética: Padrão termográfico com características
      sugestivas de fibromialgia: múltiplas áreas de assimetria térmica
      bilateral sem padrão dermatomérico claro. Sugerimos correlação com
      avaliação reumatológica e critérios clínicos do ACR.

   CONCLUSÃO
   Achados termográficos compatíveis com padrão de fibromialgia,
   recomenda-se correlação clínica.
   ```

## ⚠️ Limitações importantes

### O que o sistema PODE fazer:
✅ Identificar padrões **sugestivos** quando presentes nos dados
✅ Mencionar características compatíveis com fibromialgia
✅ Recomendar correlação clínica e avaliação reumatológica
✅ Usar linguagem medicamente apropriada (nunca diagnóstico definitivo)

### O que o sistema NÃO faz:
❌ Diagnosticar fibromialgia definitivamente
❌ Substituir avaliação clínica
❌ Analisar automaticamente tender points específicos (ainda)
❌ Medir temperatura de extremidades vs tronco automaticamente
❌ Detectar padrão periorbicular (requer ROI facial)

## 🔬 Evidência científica considerada

O prompt foi construído baseado em:

1. **Padrão de hiporradiação de extremidades**
   - Característica mais consistente
   - Indica disfunção termorreguladora

2. **Tender points com alterações térmicas**
   - Mudanças neurovasculares
   - 18 pontos clássicos do ACR

3. **Padrão cervical superior frio**
   - Região C7-T1-T2 com hiporradiação
   - "Colar frio" característico

4. **Alta especificidade, sensibilidade variável**
   - Termografia é complementar
   - Não substitui critérios clínicos ACR

## 💡 Melhorias futuras possíveis

### Curto prazo:
1. **ROIs específicas para tender points**
   - Criar template com os 18 pontos
   - Análise automática de cada ponto

2. **Análise de extremidades**
   - Comparar temperatura mãos/pés vs tronco
   - Detectar automaticamente hiporradiação distal

### Médio prazo:
3. **Mapa de calor facial**
   - Detecção de padrão periorbicular
   - ROI automática em região ocular

4. **Score de fibromialgia**
   - Quantificar probabilidade baseado em múltiplos critérios
   - Dashboard com pontuação

### Longo prazo:
5. **Machine Learning**
   - Treinar modelo para reconhecer padrões
   - Classificação automática

## 📖 Como usar para suspeita de fibromialgia

### Protocolo recomendado:

1. **Captura de imagens:**
   - Imagens de corpo inteiro (anterior/posterior)
   - Foco em: mãos, pés, região cervical superior
   - Imagens faciais (se possível)
   - Tender points específicos

2. **Processamento:**
   - Use **"🔥 Processar Todas (Auto)"** para múltiplas imagens
   - Ou desenhe ROIs manualmente em tender points

3. **Geração de laudo:**
   - Clique em **"📄 Gerar Laudo"**
   - O AI analisará automaticamente
   - Revisão médica obrigatória

4. **Interpretação:**
   - **Se o AI mencionar fibromialgia:**
     - Correlacionar com sintomas clínicos
     - Aplicar critérios ACR
     - Considerar avaliação reumatológica

   - **Se NÃO mencionar:**
     - Padrão pode estar ausente (sensibilidade variável)
     - Não descarta fibromialgia
     - Diagnóstico continua sendo clínico

## ⚕️ Importante para uso clínico

### SEMPRE lembrar:

1. **Termografia é COMPLEMENTAR**
   - Não faz diagnóstico sozinha
   - Ajuda a visualizar dor
   - Monitora tratamento

2. **Diagnóstico é CLÍNICO**
   - Critérios ACR 2010/2016
   - História + exame físico
   - Exclusão de outras causas

3. **Especificidade alta, sensibilidade variável**
   - Achado positivo → investigar
   - Achado negativo → não descarta

4. **Correlação obrigatória**
   - Avaliação reumatológica
   - Exames complementares
   - Resposta terapêutica

## 📚 Referências integradas ao prompt

- Critérios ACR (American College of Rheumatology)
- Padrões termográficos validados em literatura
- Tender points clássicos
- Conhecimento sobre termorregulação disfuncional

---

**Versão:** 1.0
**Data:** 2026-01-20
**Autor:** Dr. Jorge Cecílio Daher Jr.
**CRM-GO:** 6108
