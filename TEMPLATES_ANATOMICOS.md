# Sistema de Templates Anatômicos - Análise Multi-Ponto

## 📋 Visão Geral

Sistema avançado para criar **documentos/protocolos** com **múltiplas ROIs anatomicamente identificadas**, permitindo análise comparativa não apenas de lateralidade (esquerdo/direito) mas entre **qualquer ponto e qualquer ponto**.

## 🎯 Funcionalidades Principais

### 1. **Templates Anatômicos**
Documentos estruturados que contêm:
- ✅ Nome e descrição do protocolo
- ✅ Categoria (fibromialgia, dermátomos, articulações, personalizado)
- ✅ Múltiplas ROIs com localização anatômica detalhada
- ✅ Grupos de comparação personalizáveis
- ✅ Imagem de referência (opcional)
- ✅ Metadados e observações

### 2. **ROIs Anatômicas**
Cada ROI contém:
- **Nome**: Ex: "Joelho direito", "C5 esquerdo", "Tender point occipital"
- **Localização anatômica**: Descrição detalhada
- **Coordenadas**: Polígono desenhado na imagem
- **Tipo**: dermatome, tender_point, joint, extremity, custom
- **Faixa esperada**: Temperatura esperada (opcional)
- **Observações**: Notas clínicas

### 3. **Análise Multi-Ponto**
Sistema que gera:
- **Matriz de comparação**: Todos os pontos vs todos os pontos
- **Análise por grupos**: Comparações bilaterais, regionais, etc.
- **Estatísticas completas**: Temperatura média, amplitude, ΔT máximo
- **Tabelas formatadas**: Markdown, texto, HTML

## 📊 Exemplo de Uso: Fibromialgia 18 Tender Points

### Template Pré-Configurado

O sistema inclui template completo para avaliação de fibromialgia (ACR 1990):

```python
template = create_fibromyalgia_18_points_template()

# 18 Tender Points (9 pares bilaterais):
✓ Occipital (bilateral)
✓ Cervical baixo C5-C7 (bilateral)
✓ Trapézio (bilateral)
✓ Supraespinal (bilateral)
✓ Segunda costela (bilateral)
✓ Epicôndilo lateral (bilateral)
✓ Glúteo (bilateral)
✓ Trocanter maior (bilateral)
✓ Joelho (bilateral)
```

### Resultado da Análise

```markdown
# Análise Multi-Ponto: Fibromialgia - 18 Tender Points

## Temperaturas por ROI

| ROI | Temperatura | Pixels |
|-----|-------------|--------|
| Occipital Esquerdo | 34.52°C | 1520 |
| Occipital Direito | 35.18°C | 1480 |
| Cervical Baixo Esquerdo | 33.21°C | 1350 |
| Cervical Baixo Direito | 33.89°C | 1400 |
...

## Estatísticas Gerais

- **Total de ROIs:** 18
- **Temperatura Média:** 34.12°C
- **Amplitude:** 3.45°C
- **ΔT Médio:** 0.68°C
- **ΔT Máximo:** 2.15°C

## Comparações Bilaterais

| Grupo | ROI 1 | Temp 1 | ROI 2 | Temp 2 | ΔT | Classificação |
|-------|-------|--------|-------|--------|-----|---------------|
| Occipital | Esquerdo | 34.52°C | Direito | 35.18°C | 0.66°C | Leve |
| Cervical | Esquerdo | 33.21°C | Direito | 33.89°C | 0.68°C | Leve |
...
```

## 🔬 Estrutura de Dados

### AnatomicalROI

```python
@dataclass
class AnatomicalROI:
    name: str  # Nome da ROI
    anatomical_location: str  # Descrição anatômica
    coordinates: List[Tuple[int, int]]  # Pontos do polígono
    region_type: str  # Tipo de região
    expected_temp_range: Optional[Tuple[float, float]]  # Faixa esperada
    notes: str  # Observações
```

### AnatomicalTemplate

```python
@dataclass
class AnatomicalTemplate:
    template_id: Optional[int]
    name: str  # Nome do protocolo
    description: str  # Descrição
    category: str  # Categoria
    reference_image_path: Optional[str]  # Imagem de referência
    rois: List[AnatomicalROI]  # Lista de ROIs
    comparison_groups: List[List[str]]  # Grupos de comparação
    created_date: str
    modified_date: str
    metadata: Dict[str, Any]
```

### MultiPointAnalysisResult

```python
@dataclass
class MultiPointAnalysisResult:
    template_name: str
    image_name: str
    roi_temperatures: Dict[str, float]  # {nome_roi: temp}
    roi_pixel_counts: Dict[str, int]  # {nome_roi: pixels}
    comparison_matrix: Dict[str, Dict[str, float]]  # Matriz todos vs todos
    group_comparisons: List[Dict[str, Any]]  # Resultados por grupo
    overall_stats: Dict[str, float]  # Estatísticas gerais
```

## 💡 Casos de Uso

### 1. **Fibromialgia - 18 Tender Points**
- Template pré-configurado com os 18 pontos clássicos
- Comparação bilateral automática
- Identificação de assimetrias significativas
- Geração de mapa de dor térmico

### 2. **Dermátomos Múltiplos**
- Criar template com C3-C8, T1-T12, L1-L5, S1-S5
- Comparar dermátomos adjacentes
- Identificar padrões radiculares
- Análise sequencial (C5 vs C6 vs C7)

### 3. **Articulações Bilaterais**
- Joelhos, ombros, cotovelos, punhos
- Comparação esquerda/direita
- Identificação de processos inflamatórios
- Monitoramento de tratamento

### 4. **Extremidades vs Tronco**
- Avaliação de termorregulação
- Identificação de hiporradiação distal
- Padrões de fibromialgia
- Disfunção autonômica

### 5. **Protocolos Personalizados**
- Criar protocolo específico para cada caso
- Definir grupos de comparação customizados
- Salvar e reutilizar em follow-ups
- Comparar mesmas ROIs ao longo do tempo

## 🛠️ API de Uso

### Criar Template Personalizado

```python
from core.anatomical_template import AnatomicalTemplate, AnatomicalROI

# Criar template
template = AnatomicalTemplate(
    name="Protocolo Joelhos - Gonartrose",
    description="Avaliação bilateral de joelhos",
    category="joints"
)

# Adicionar ROIs
roi_esquerdo = AnatomicalROI(
    name="Joelho Esquerdo",
    anatomical_location="Articulação femorotibial esquerda - face anterior",
    coordinates=[(100, 200), (150, 200), (150, 280), (100, 280)],
    region_type="joint",
    expected_temp_range=(32.0, 35.0)
)
template.add_roi(roi_esquerdo)

# Adicionar ROI direita
roi_direito = AnatomicalROI(
    name="Joelho Direito",
    anatomical_location="Articulação femorotibial direita - face anterior",
    coordinates=[(400, 200), (450, 200), (450, 280), (400, 280)],
    region_type="joint",
    expected_temp_range=(32.0, 35.0)
)
template.add_roi(roi_direito)

# Definir grupo de comparação bilateral
template.add_comparison_group(["Joelho Esquerdo", "Joelho Direito"])

# Salvar template
template.save_to_file(Path("protocolo_joelhos.json"))
```

### Analisar Imagem com Template

```python
from core.multipoint_analyzer import MultiPointAnalyzer

# Carregar template
template = AnatomicalTemplate.load_from_file("protocolo_joelhos.json")

# Processar imagem
analyzer = MultiPointAnalyzer()
result = analyzer.analyze_template(
    template=template,
    thermal_data=thermal_data,
    visible_image=visible_image,
    image_name="Paciente_123_Joelhos.jpg"
)

# Gerar tabela de resultados
table_md = analyzer.generate_comparison_table(result, format="markdown")
print(table_md)

# Acessar temperaturas específicas
temp_esq = result.roi_temperatures["Joelho Esquerdo"]
temp_dir = result.roi_temperatures["Joelho Direito"]
delta_t = result.get_delta_t("Joelho Esquerdo", "Joelho Direito")

print(f"Esquerdo: {temp_esq:.2f}°C")
print(f"Direito: {temp_dir:.2f}°C")
print(f"ΔT: {delta_t:.2f}°C")

# Obter maior assimetria
roi1, roi2, max_delta = result.get_max_delta_t()
print(f"Maior assimetria: {roi1} vs {roi2} = {max_delta:.2f}°C")
```

## 📈 Vantagens do Sistema

### vs Sistema Anterior (Apenas Esq/Dir)

**Antes:**
- ❌ Apenas 2 ROIs (esquerdo/direito)
- ❌ Sem localização anatômica detalhada
- ❌ Sem análise multi-ponto
- ❌ Difícil reutilização

**Agora:**
- ✅ **Múltiplas ROIs** (quantas quiser)
- ✅ **Localização anatômica** detalhada
- ✅ **Análise todos vs todos**
- ✅ **Templates reutilizáveis**
- ✅ **Grupos de comparação** customizáveis
- ✅ **Protocolos pré-configurados** (fibromialgia, etc.)
- ✅ **Estatísticas avançadas**
- ✅ **Export estruturado** (JSON, MD, HTML)

## 🔮 Próximos Passos

### Fase 1 - Interface (Em Desenvolvimento)
- [ ] Interface gráfica para criar/editar templates
- [ ] Desenhar múltiplas ROIs visualmente
- [ ] Gerenciar biblioteca de templates
- [ ] Aplicar template em imagem

### Fase 2 - Banco de Dados
- [ ] Salvar templates no banco SQLite
- [ ] Histórico de análises
- [ ] Comparar mesmas ROIs em follow-ups

### Fase 3 - Revisão de Laudos
- [ ] Sistema de validação de laudos
- [ ] Comparar laudo gerado vs dados do template
- [ ] Sugerir correções/melhorias

### Fase 4 - Integração com IA
- [ ] Claude AI usa dados do template para gerar laudo
- [ ] Menciona cada ROI com temperatura e localização
- [ ] Identifica automaticamente padrões (fibromialgia, etc.)

## 📚 Referências

- **ACR 1990**: Critérios para fibromialgia com 18 tender points
- **Dermátomos**: Mapas neurológicos C1-S5
- **Termografia médica**: Protocolos padronizados de captura

---

**Status:** ✅ Estrutura base implementada (modelo de dados + analisador)
**Próximo:** Interface gráfica e integração com banco de dados
**Versão:** 1.0-alpha
**Data:** 2026-01-20
