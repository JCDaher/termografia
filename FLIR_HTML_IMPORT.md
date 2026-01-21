# Importação de Medições FLIR Thermal Studio

## 📋 Visão Geral

Sistema de **importação e validação** de medições de ROIs exportadas do **FLIR Thermal Studio** em formato HTML. Permite:

- ✅ Extrair medições de referência do FLIR
- ✅ Criar templates anatômicos a partir do FLIR
- ✅ Validar cálculos do sistema contra medições FLIR
- ✅ Enriquecer prompts do Claude AI com dados FLIR

## 🎯 Por que importar do FLIR?

### Casos de Uso

1. **Validação de Precisão**
   - Comparar cálculos do sistema vs FLIR Thermal Studio
   - Identificar discrepâncias em medições
   - Garantir precisão das análises

2. **Criação Rápida de Templates**
   - Exportar ROIs do FLIR
   - Importar para criar template anatomicamente identificado
   - Reutilizar em análises futuras

3. **Dados de Referência para IA**
   - Fornecer medições FLIR ao Claude AI
   - AI pode comparar suas medições com referência FLIR
   - Maior confiança nos laudos gerados

4. **Migração de Dados Existentes**
   - Importar histórico de medições do FLIR
   - Integrar com novo sistema
   - Manter continuidade de dados

## 📊 Formato HTML do FLIR Thermal Studio

### Estrutura do Export

O FLIR Thermal Studio exporta HTML com esta estrutura:

```html
<html>
<body>
  <!-- Cada imagem = uma section -->
  <section>
    <!-- Informações do arquivo -->
    <table>
      <caption>File information</caption>
      <tr><th>File name</th><td>IR_0001.jpg</td></tr>
      <tr><th>Resolution</th><td>640 × 480</td></tr>
      ...
    </table>

    <!-- Medições das ROIs -->
    <table>
      <caption>Measurements</caption>
      <tr><th>Name</th><th>Max</th><th>Mean</th><th>Min</th></tr>
      <tr><td>Joelho Direito</td><td>35.5 °C</td><td>34.2 °C</td><td>32.8 °C</td></tr>
      <tr><td>Joelho Esquerdo</td><td>35.1 °C</td><td>34.0 °C</td><td>32.5 °C</td></tr>
      ...
    </table>
  </section>

  <section>
    <!-- Próxima imagem... -->
  </section>
</body>
</html>
```

### Dados Extraídos

Para cada imagem, o parser extrai:

- **Nome do arquivo**: `IR_0001.jpg`
- **Informações adicionais**: Resolução, temperaturas globais, etc.
- **Medições de ROIs**:
  - Nome da ROI
  - Temperatura Máxima
  - Temperatura Média
  - Temperatura Mínima

## 🛠️ Como Usar

### 1. Exportar do FLIR Thermal Studio

No FLIR Thermal Studio:

1. Abra suas imagens térmicas
2. Desenhe as ROIs desejadas
3. Vá em **File → Export → Report...**
4. Escolha formato **HTML**
5. Marque opção **Include measurements**
6. Salve o arquivo HTML

### 2. Importar no Sistema

#### Opção A: Criar Template Anatômico

```python
from pathlib import Path
from core.flir_html_parser import FLIRHTMLParser

# Parse HTML
parser = FLIRHTMLParser()
flir_data = parser.parse_file(Path("export_flir.html"))

# Converte para template anatômico
template = parser.to_anatomical_template(
    flir_data,
    template_name="Protocolo Joelhos - Importado FLIR",
    category="joints"
)

# Salva template
template.save_to_file(Path("template_joelhos_flir.json"))

print(f"✅ Template criado com {len(template.rois)} ROIs")
for roi in template.rois:
    print(f"  - {roi.name}: {roi.notes}")
```

#### Opção B: Validar Medições do Sistema

```python
from core.flir_html_parser import FLIRHTMLParser
from core.multipoint_analyzer import MultiPointAnalyzer

# Parse HTML FLIR
parser = FLIRHTMLParser()
flir_data = parser.parse_file(Path("export_flir.html"))

# Processa imagem com sistema
analyzer = MultiPointAnalyzer()
result = analyzer.analyze_template(template, thermal_data, visible_image)

# Compara FLIR vs Sistema
validation_report = parser.create_validation_report(
    flir_data,
    result.roi_temperatures
)

print(validation_report)
```

Exemplo de saída:

```
================================================================================
RELATÓRIO DE VALIDAÇÃO: FLIR vs Sistema
================================================================================

Total de ROIs no FLIR: 18
Total de ROIs no Sistema: 18

COMPARAÇÕES DETALHADAS:
--------------------------------------------------------------------------------
ROI Name                       FLIR Mean    Sistema      Diferença    Status
--------------------------------------------------------------------------------
Joelho Direito                  34.20°C      34.18°C        0.02°C    ✅ OK
Joelho Esquerdo                 34.00°C      34.05°C        0.05°C    ✅ OK
Cervical C5 Dir                 33.50°C      33.45°C        0.05°C    ✅ OK
...

ESTATÍSTICAS:
--------------------------------------------------------------------------------
ROIs correspondentes: 18/18
Diferença média: 0.08°C
Diferença máxima: 0.25°C
Diferença mínima: 0.01°C
Desvio padrão: 0.09°C
```

### 3. Integrar com Claude AI (Futuro)

O sistema poderá enviar medições FLIR junto com o prompt:

```
Análise térmica com dados de referência FLIR:

MEDIÇÕES DO SISTEMA:
- Joelho Direito: 34.18°C

MEDIÇÕES FLIR (REFERÊNCIA):
- Joelho Direito: Max=35.5°C, Mean=34.20°C, Min=32.8°C

Por favor, gere o laudo considerando ambas as medições.
```

## 🔬 Estrutura de Dados

### FLIRMeasurement

```python
@dataclass
class FLIRMeasurement:
    """Medição de uma ROI no FLIR."""
    roi_name: str           # "Joelho Direito"
    max_temp: float         # 35.5
    mean_temp: float        # 34.2
    min_temp: float         # 32.8
```

### FLIRImageData

```python
@dataclass
class FLIRImageData:
    """Dados de uma imagem no export."""
    filename: str                        # "IR_0001.jpg"
    measurements: List[FLIRMeasurement]  # Lista de medições
    file_info: Dict[str, str]            # Informações adicionais
```

### FLIRExportData

```python
@dataclass
class FLIRExportData:
    """Dados completos do export HTML."""
    images: List[FLIRImageData]  # Todas as imagens
    source_file: str             # Caminho do HTML

    def get_all_measurements(self) -> List[FLIRMeasurement]:
        """Retorna todas as medições de todas as imagens."""

    def get_measurements_by_image(self, filename: str) -> Optional[FLIRImageData]:
        """Busca medições de imagem específica."""
```

## 📈 Fluxos de Trabalho

### Fluxo 1: Validação de Precisão

```
1. Processar imagem no FLIR Thermal Studio
   ↓
2. Desenhar ROIs e exportar HTML
   ↓
3. Processar mesma imagem no nosso sistema
   ↓
4. Importar HTML FLIR
   ↓
5. Gerar relatório de validação
   ↓
6. Analisar discrepâncias (se houver)
```

### Fluxo 2: Criação de Template

```
1. No FLIR: criar protocolo com ROIs anatomicamente posicionadas
   ↓
2. Exportar para HTML com medições
   ↓
3. Importar no sistema → cria template
   ↓
4. Enriquecer template com descrições anatômicas
   ↓
5. Salvar e reutilizar em futuras análises
```

### Fluxo 3: Migração de Histórico

```
1. Exportar todas as análises antigas do FLIR
   ↓
2. Processar batch de HTMLs
   ↓
3. Converter para templates/registros
   ↓
4. Importar para banco de dados do sistema
   ↓
5. Histórico completo disponível
```

## ⚠️ Limitações e Considerações

### Diferenças Esperadas

É **normal** haver pequenas diferenças entre FLIR e sistema:

1. **Algoritmos de interpolação**
   - FLIR usa algoritmos proprietários
   - Sistema usa interpolação OpenCV
   - Diferenças de 0.1-0.3°C são aceitáveis

2. **Precisão de coordenadas**
   - ROIs desenhadas podem não ser exatamente idênticas
   - Pixels incluídos podem variar ligeiramente

3. **Conversão de formato**
   - FLIR trabalha com dados RAW originais
   - Sistema pode processar imagens exportadas (JPEG)
   - Possível perda de precisão radiométrica

### Limites Aceitáveis

- **✅ Excelente**: Diferença < 0.2°C
- **✅ Bom**: Diferença < 0.5°C
- **⚠️ Atenção**: Diferença 0.5-1.0°C (verificar ROI)
- **❌ Problema**: Diferença > 1.0°C (investigar)

### Quando Investigar Discrepâncias

Se diferença > 1.0°C, verificar:

1. **ROIs desenhadas identicamente?**
   - Tamanho, posição, forma
   - Mesma área coberta

2. **Mesma imagem de origem?**
   - FLIR processou RAW ou JPEG?
   - Sistema processou qual arquivo?

3. **Configurações de paleta**
   - Escala de temperatura
   - Limites min/max

4. **Calibração da câmera**
   - Emissividade configurada
   - Temperatura refletida

## 💡 Dicas e Melhores Práticas

### Nomenclatura de ROIs

No FLIR Thermal Studio, use nomes **descritivos e padronizados**:

✅ **Bom:**
- "Joelho Direito"
- "C5 Esquerdo"
- "Tender Point Occipital Dir"

❌ **Evitar:**
- "Sp1", "Ar2"
- "ROI 01", "Região A"

**Por quê?** Facilita mapeamento automático e identificação anatômica.

### Organização de Exports

Estruture seus exports FLIR:

```
exports_flir/
├── 2024-01-15_paciente_joao/
│   ├── joelhos.html
│   ├── coluna.html
│   └── extremidades.html
├── 2024-01-16_paciente_maria/
│   └── fibromialgia_18points.html
└── ...
```

### Versionamento de Templates

Ao importar do FLIR, adicione metadados:

```python
template.metadata['flir_export_date'] = '2024-01-15'
template.metadata['flir_version'] = '6.15.0'
template.metadata['original_html'] = 'joelhos.html'
```

## 🔮 Próximos Passos

### Fase 1 - Interface (Próxima)
- [ ] Botão "Importar FLIR HTML" na UI
- [ ] Preview de medições antes de importar
- [ ] Seleção de quais ROIs importar

### Fase 2 - Integração Automática
- [ ] Detectar automaticamente arquivos HTML na pasta
- [ ] Sugerir importação ao processar imagem
- [ ] Link entre imagem térmica e export FLIR

### Fase 3 - Análise Avançada
- [ ] Gráficos de validação (FLIR vs Sistema)
- [ ] Histórico de precisão ao longo do tempo
- [ ] Alertas automáticos para discrepâncias

### Fase 4 - Claude AI Enhancement
- [ ] Incluir medições FLIR no prompt automaticamente
- [ ] AI menciona quando há referência FLIR disponível
- [ ] AI explica discrepâncias se detectadas

## 📚 Referências

- **FLIR Thermal Studio**: Software oficial para análise termográfica
- **BeautifulSoup4**: Biblioteca Python para parsing HTML
- **Sistema de Templates**: Ver `TEMPLATES_ANATOMICOS.md`

---

**Status:** ✅ Parser implementado e funcional
**Próximo:** Interface de importação na UI
**Versão:** 1.0
**Data:** 2026-01-21
