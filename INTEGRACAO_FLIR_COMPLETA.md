# Integração Completa FLIR + Sistema de Templates

## 📋 Visão Geral

Este documento descreve a **integração completa** entre:

1. **Parser FLIR HTML** - Extrai medições do FLIR Thermal Studio
2. **Sistema de Templates Anatômicos** - Templates multi-ponto reutilizáveis
3. **Validador FLIR** - Compara sistema vs FLIR
4. **Enriquecedor de Prompts** - Adiciona dados FLIR ao Claude AI

## 🎯 Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUXO COMPLETO                            │
└─────────────────────────────────────────────────────────────┘

1. CAPTURA NO FLIR THERMAL STUDIO
   ├─ Processar imagem térmica
   ├─ Desenhar ROIs anatomicamente identificadas
   ├─ Exportar relatório HTML com medições
   └─ Salvar arquivo HTML
                    ↓
2. IMPORTAÇÃO NO SISTEMA
   ├─ Parser FLIR HTML extrai medições
   ├─ Converte para AnatomicalTemplate
   ├─ Salva template para reutilização
   └─ ROIs prontas para análise
                    ↓
3. PROCESSAMENTO DA IMAGEM
   ├─ Sistema processa imagem térmica
   ├─ Aplica template nas ROIs
   ├─ Calcula temperaturas de cada ROI
   └─ Gera MultiPointAnalysisResult
                    ↓
4. VALIDAÇÃO
   ├─ Compara medições sistema vs FLIR
   ├─ Calcula diferenças e estatísticas
   ├─ Classifica: OK / Warning / Error
   └─ Gera ValidationReport
                    ↓
5. ENRIQUECIMENTO DO PROMPT
   ├─ Adiciona dados FLIR ao prompt
   ├─ Inclui validação e comparações
   ├─ Fornece contexto ao Claude AI
   └─ AI usa dados mais precisos
                    ↓
6. GERAÇÃO DO LAUDO
   ├─ Claude AI recebe dados enriquecidos
   ├─ Usa medições FLIR quando disponíveis
   ├─ Gera laudo profissional preciso
   └─ Menciona validação se necessário
```

## 📦 Módulos Criados

### 1. `core/flir_html_parser.py`

**Responsabilidade**: Parser de arquivos HTML do FLIR Thermal Studio.

**Classes principais**:
- `FLIRMeasurement`: Medição individual (ROI + temperaturas)
- `FLIRImageData`: Dados de uma imagem (filename + medições)
- `FLIRExportData`: Export completo (múltiplas imagens)
- `FLIRHTMLParser`: Parser principal

**Uso**:
```python
from core.flir_html_parser import parse_flir_html

# Parse HTML
flir_data = parse_flir_html(Path("export_flir.html"))

# Acessa medições
for image in flir_data.images:
    print(f"Imagem: {image.filename}")
    for m in image.measurements:
        print(f"  {m.roi_name}: {m.mean_temp:.2f}°C")

# Converte para template
template = parser.to_anatomical_template(flir_data)
template.save_to_file(Path("template.json"))
```

### 2. `core/flir_validator.py`

**Responsabilidade**: Validação de medições sistema vs FLIR.

**Classes principais**:
- `ValidationResult`: Resultado individual de validação
- `ValidationReport`: Relatório completo
- `FLIRValidator`: Validador principal

**Uso**:
```python
from core.flir_validator import FLIRValidator

validator = FLIRValidator(
    tolerance_ok=0.5,      # < 0.5°C = OK
    tolerance_warning=1.0  # < 1.0°C = Warning, > 1.0°C = Error
)

# Valida
report = validator.validate(flir_data, system_temperatures)

print(f"Precisão: {report.get_accuracy_percentage():.1f}%")
print(validator.generate_text_report(report))
```

### 3. `core/flir_prompt_enhancer.py`

**Responsabilidade**: Enriquecimento de prompts do Claude AI.

**Classes principais**:
- `FLIRPromptEnhancer`: Enhancer principal

**Uso**:
```python
from core.flir_prompt_enhancer import enhance_prompt_with_flir

# Enriquece prompt
enhanced_prompt, validation_report = enhance_prompt_with_flir(
    base_prompt=original_prompt,
    flir_html_path=Path("export.html"),
    system_temperatures=result.roi_temperatures,
    image_name="IR_0001.jpg"
)

# Usa prompt enriquecido com Claude
response = claude_api.generate(enhanced_prompt)
```

### 4. `core/anatomical_template.py` (Já existente)

**Templates anatômicos multi-ponto** - Ver `TEMPLATES_ANATOMICOS.md`

### 5. `core/multipoint_analyzer.py` (Já existente)

**Análise multi-ponto** - Ver `TEMPLATES_ANATOMICOS.md`

## 🚀 Casos de Uso Completos

### Caso 1: Importar medições FLIR e criar template

```python
from pathlib import Path
from core.flir_html_parser import FLIRHTMLParser

# 1. Parse HTML FLIR
parser = FLIRHTMLParser()
flir_data = parser.parse_file(Path("fibromialgia_18points.html"))

print(f"Importado: {len(flir_data.get_all_measurements())} medições")

# 2. Converte para template
template = parser.to_anatomical_template(
    flir_data,
    template_name="Fibromialgia 18 Tender Points - Paciente João",
    category="fibromyalgia"
)

# 3. Enriquece com descrições anatômicas
for roi in template.rois:
    if "Joelho" in roi.name:
        roi.anatomical_location = "Articulação femorotibial - região medial"
        roi.region_type = "tender_point"
    # ... mais enriquecimentos

# 4. Salva template
template.save_to_file(Path("templates/fibro_paciente_joao.json"))

print(f"✅ Template salvo com {len(template.rois)} ROIs")
```

### Caso 2: Processar imagem com validação FLIR

```python
from core.multipoint_analyzer import MultiPointAnalyzer
from core.flir_html_parser import parse_flir_html
from core.flir_validator import FLIRValidator

# 1. Carrega template
template = AnatomicalTemplate.load_from_file("templates/fibro_joao.json")

# 2. Processa imagem
analyzer = MultiPointAnalyzer()
result = analyzer.analyze_template(
    template=template,
    thermal_data=thermal_data,
    visible_image=visible_image,
    image_name="IR_0001.jpg"
)

print(f"Processadas {len(result.roi_temperatures)} ROIs")

# 3. Parse dados FLIR de referência
flir_data = parse_flir_html(Path("flir_export.html"))

# 4. Valida
validator = FLIRValidator()
validation = validator.validate(flir_data, result.roi_temperatures)

print(validation)
print(f"\nPrecisão: {validation.get_accuracy_percentage():.1f}%")

# 5. Gera relatório detalhado
print(validator.generate_text_report(validation))
```

### Caso 3: Gerar laudo com dados FLIR

```python
from core.flir_prompt_enhancer import enhance_prompt_with_flir
from api.prompts_professional import build_professional_report_prompt

# 1. Processa imagem (como caso 2)
result = analyzer.analyze_template(...)

# 2. Cria prompt base
base_prompt = build_professional_report_prompt(
    image_name="IR_0001.jpg",
    roi_data=result.roi_temperatures,
    # ... outros dados
)

# 3. Enriquece com FLIR
enhanced_prompt, validation = enhance_prompt_with_flir(
    base_prompt=base_prompt,
    flir_html_path=Path("flir_export.html"),
    system_temperatures=result.roi_temperatures,
    image_name="IR_0001.jpg"
)

print("✅ Prompt enriquecido com dados FLIR")
print(f"   Validação: {validation.get_accuracy_percentage():.1f}%")

# 4. Gera laudo com Claude AI
from api.api_client import generate_professional_report

report = generate_professional_report(enhanced_prompt)

print("\n" + report)
```

### Caso 4: Workflow completo - Do FLIR ao laudo

```python
"""
Workflow completo:
1. Importa medições FLIR
2. Cria template
3. Processa imagem
4. Valida vs FLIR
5. Gera laudo enriquecido
"""

from pathlib import Path
from core.flir_html_parser import FLIRHTMLParser
from core.multipoint_analyzer import MultiPointAnalyzer
from core.flir_validator import FLIRValidator
from core.flir_prompt_enhancer import enhance_prompt_with_flir
from api.prompts_professional import build_professional_report_prompt

# === PASSO 1: Importar FLIR ===
print("1️⃣ Importando medições FLIR...")

parser = FLIRHTMLParser()
flir_data = parser.parse_file(Path("exports/fibro_joao.html"))
template = parser.to_anatomical_template(flir_data)
template.save_to_file(Path("templates/fibro_joao.json"))

print(f"   ✅ {len(template.rois)} ROIs importadas")

# === PASSO 2: Processar Imagem ===
print("\n2️⃣ Processando imagem térmica...")

analyzer = MultiPointAnalyzer()
result = analyzer.analyze_template(
    template=template,
    thermal_data=thermal_data,
    visible_image=visible_image,
    image_name="IR_Fibro_Joao.jpg"
)

print(f"   ✅ {len(result.roi_temperatures)} ROIs analisadas")

# === PASSO 3: Validar vs FLIR ===
print("\n3️⃣ Validando vs FLIR...")

validator = FLIRValidator()
validation = validator.validate(flir_data, result.roi_temperatures)

print(f"   ✅ Precisão: {validation.get_accuracy_percentage():.1f}%")
print(f"   {validation.get_status_counts()}")

# === PASSO 4: Gerar Laudo ===
print("\n4️⃣ Gerando laudo profissional...")

base_prompt = build_professional_report_prompt(
    image_name="IR_Fibro_Joao.jpg",
    roi_data=result.roi_temperatures,
    # ... outros dados
)

enhanced_prompt, _ = enhance_prompt_with_flir(
    base_prompt=base_prompt,
    flir_html_path=Path("exports/fibro_joao.html"),
    system_temperatures=result.roi_temperatures,
    image_name="IR_Fibro_Joao.jpg"
)

# Gera com Claude AI
report = generate_professional_report(enhanced_prompt)

print("   ✅ Laudo gerado")
print("\n" + "=" * 80)
print(report)
print("=" * 80)

# === PASSO 5: Salvar Resultados ===
print("\n5️⃣ Salvando resultados...")

# Salva validação
with open("reports/validation_fibro_joao.txt", "w") as f:
    f.write(validator.generate_text_report(validation))

# Salva laudo
with open("reports/laudo_fibro_joao.md", "w") as f:
    f.write(report)

print("   ✅ Arquivos salvos em reports/")
print("\n🎉 Workflow completo!")
```

## 📊 Formato dos Dados

### Dados FLIR (HTML → Python)

```python
FLIRExportData(
    source_file="fibro.html",
    images=[
        FLIRImageData(
            filename="IR_0001.jpg",
            file_info={
                "File name": "IR_0001.jpg",
                "Resolution": "640 × 480",
                ...
            },
            measurements=[
                FLIRMeasurement(
                    roi_name="Joelho Direito",
                    max_temp=35.5,
                    mean_temp=34.2,
                    min_temp=32.8
                ),
                ...
            ]
        )
    ]
)
```

### Validação (FLIR vs Sistema)

```python
ValidationReport(
    validations=[
        ValidationResult(
            roi_name="Joelho Direito",
            flir_temp=34.2,
            system_temp=34.18,
            difference=-0.02,
            relative_error=-0.06,
            status="ok",
            flir_range=(32.8, 35.5)
        ),
        ...
    ],
    total_rois=18,
    matched_rois=18,
    unmatched_flir=[],
    unmatched_system=[],
    statistics={
        'mean_abs_difference': 0.08,
        'max_abs_difference': 0.25,
        ...
    }
)
```

## ⚙️ Configuração e Integração com UI

### Adicionar à Interface PyQt6

Para integrar com a interface gráfica existente:

```python
# Em ui/thermal_analyzer_ui.py

from core.flir_html_parser import parse_flir_html
from core.flir_validator import FLIRValidator
from core.flir_prompt_enhancer import enhance_prompt_with_flir

class ThermalAnalyzerUI:
    def __init__(self):
        # ... código existente
        self.flir_html_path = None
        self.flir_data = None

    def add_import_flir_button(self):
        """Adiciona botão 'Importar FLIR HTML'."""
        btn = QPushButton("📥 Importar FLIR HTML")
        btn.clicked.connect(self.import_flir_html)
        # Adicionar ao layout

    def import_flir_html(self):
        """Dialog para importar HTML FLIR."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Export FLIR HTML",
            "",
            "HTML Files (*.html *.htm)"
        )

        if file_path:
            try:
                self.flir_html_path = Path(file_path)
                self.flir_data = parse_flir_html(self.flir_html_path)

                QMessageBox.information(
                    self,
                    "FLIR Importado",
                    f"✅ Importadas {len(self.flir_data.get_all_measurements())} "
                    f"medições de {len(self.flir_data.images)} imagem(ns)"
                )
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"❌ Erro ao importar: {e}")

    def generate_report_with_flir(self):
        """Gera laudo usando dados FLIR se disponível."""
        # Cria prompt base
        base_prompt = build_professional_report_prompt(...)

        # Enriquece com FLIR se disponível
        if self.flir_data:
            enhanced_prompt, validation = enhance_prompt_with_flir(
                base_prompt,
                self.flir_html_path,
                self.current_temperatures,
                self.current_image_name
            )

            # Mostra validação na UI
            validation_text = self.create_validation_summary(validation)
            self.status_label.setText(validation_text)

            # Usa prompt enriquecido
            report = generate_professional_report(enhanced_prompt)
        else:
            # Usa prompt normal
            report = generate_professional_report(base_prompt)

        return report
```

## 🔍 Troubleshooting

### Problema: ROIs não correspondem

**Sintoma**: `unmatched_flir` ou `unmatched_system` não vazios

**Solução**:
1. Verifique nomes das ROIs no FLIR e no template
2. Use `fuzzy_match=True` no validador
3. Padronize nomenclatura: "Joelho Direito" vs "joelho_dir"

### Problema: Diferenças grandes (> 1.0°C)

**Sintoma**: Muitos erros na validação

**Possíveis causas**:
1. ROIs desenhadas em posições diferentes
2. Imagem FLIR é RAW, sistema usa JPEG
3. Diferentes algoritmos de interpolação
4. Área da ROI diferente

**Solução**:
1. Redesenhar ROIs idênticamente
2. Exportar imagem RAW do FLIR
3. Aceitar diferença pequena como normal
4. Ajustar tolerâncias do validador

## 📚 Documentação Relacionada

- **`TEMPLATES_ANATOMICOS.md`**: Sistema de templates multi-ponto
- **`FLIR_HTML_IMPORT.md`**: Detalhes do parser FLIR
- **`DETECCAO_FIBROMIALGIA.md`**: Detecção de padrões de fibromialgia

## 🎯 Próximos Passos

### Curto Prazo (Implementar agora)
- [x] Parser FLIR HTML
- [x] Validador FLIR vs Sistema
- [x] Enriquecedor de prompts
- [ ] Integração com UI (botões, dialogs)
- [ ] Testes automatizados

### Médio Prazo
- [ ] Cache de validações
- [ ] Histórico de precisão
- [ ] Gráficos de validação
- [ ] Export de relatórios PDF

### Longo Prazo
- [ ] Machine Learning para correção automática
- [ ] Integração direta com FLIR SDK
- [ ] Importação de múltiplos formatos
- [ ] Dashboard de qualidade

---

**Versão:** 1.0
**Data:** 2026-01-21
**Status:** ✅ Sistema completo e funcional
**Autor:** Sistema de Termografia Médica
