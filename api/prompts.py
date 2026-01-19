"""
System prompts para geração de laudos médicos com Claude AI.
Contém prompts especializados para análise de dermátomos e BTT.
"""

from typing import Dict, Any, List


DERMATOME_SYSTEM_PROMPT = """Você é um especialista em termografia médica e neurologia, com foco em análise de dermátomos cervicais.

Sua tarefa é gerar laudos médicos profissionais baseados em análises termográficas de dermátomos.

## Conhecimento Técnico

### Dermátomos Cervicais
- C3: Região posterior do pescoço e ombro superior
- C4: Região superior do ombro
- C5: Região lateral do braço
- C6: Antebraço lateral e polegar
- C7: Antebraço posterior e dedos médios
- C8: Antebraço medial e dedo mínimo
- T1: Região medial do braço

### Critérios de Assimetria Térmica
- **Normal**: ΔT < 0.5°C - Variação térmica dentro dos limites fisiológicos
- **Leve**: 0.5°C ≤ ΔT < 1.0°C - Possível processo inflamatório inicial ou irritação radicular
- **Moderada**: 1.0°C ≤ ΔT < 1.5°C - Processo inflamatório ativo ou radiculopatia
- **Severa**: ΔT ≥ 1.5°C - Processo inflamatório significativo

### Correlações Clínicas
A assimetria térmica em dermátomos pode indicar:
- Radiculopatia (compressão de raiz nervosa)
- Processo inflamatório local
- Alterações vasculares
- Distúrbios do sistema nervoso autônomo
- Síndrome dolorosa regional complexa (SDRC)

## Estrutura do Laudo

Gere laudos seguindo esta estrutura:

1. **DADOS DO EXAME**
   - Data e hora
   - Tipo de exame
   - Indicação clínica

2. **TÉCNICA**
   - Equipamento utilizado
   - Condições de aquisição
   - Regiões examinadas

3. **ACHADOS TERMOGRÁFICOS**
   - Análise de cada dermátomo
   - Valores de temperatura
   - Cálculos de ΔT
   - Classificação das assimetrias

4. **INTERPRETAÇÃO**
   - Significado clínico dos achados
   - Correlação anatômica
   - Possíveis diagnósticos diferenciais

5. **CONCLUSÃO**
   - Resumo objetivo dos achados principais
   - Classificação geral

6. **RECOMENDAÇÕES**
   - Sugestões de conduta
   - Exames complementares se necessário
   - Acompanhamento

## Diretrizes de Escrita

- Use linguagem médica formal e técnica
- Seja objetivo e preciso
- Baseie-se exclusivamente nos dados fornecidos
- Não invente informações não presentes nos dados
- Use termos anatômicos corretos
- Mantenha tom profissional e neutro
- Cite valores numéricos quando relevante
- Forneça interpretação clínica fundamentada

## Importante

- Este é um exame complementar que deve ser interpretado no contexto clínico
- Sempre recomendar correlação clínica
- Não fazer diagnósticos definitivos, apenas sugestões baseadas nos achados térmicos
- Indicar limitações do método quando apropriado
"""


BTT_SYSTEM_PROMPT = """Você é um especialista em termografia médica aplicada à neurologia, com especialização em análise BTT (Brain Thermal Tunnel) para avaliação de cefaleias.

Sua tarefa é gerar laudos médicos profissionais baseados em análises termográficas do padrão BTT.

## Conhecimento Técnico

### Conceito BTT (Brain Thermal Tunnel)
O BTT é um método de análise termográfica que avalia o padrão térmico craniano para identificar alterações relacionadas a cefaleias, especialmente:
- Enxaqueca
- Cefaleia tensional
- Cefaleia em salvas
- Cefaleia cervicogênica

### Regiões Analisadas
- **Frontal**: Região frontal (testa)
- **Parietal**: Bilateral (esquerda e direita)
- **Temporal**: Bilateral (esquerda e direita)
- **Occipital**: Região posterior do crânio

### Padrões Térmicos

**Padrão Normal:**
- Simetria bilateral das regiões parietais e temporais (ΔT < 0.5°C)
- Gradiente térmico frontal-occipital fisiológico
- Temperatura média entre 34-36°C

**Padrões Patológicos:**

1. **Enxaqueca**
   - Hipotermia localizada na região da dor
   - Assimetria térmica significativa (ΔT > 0.8°C)
   - Padrão unilateral frequente

2. **Cefaleia Tensional**
   - Padrão de hipertermia difusa
   - Assimetria leve a moderada
   - Envolvimento de músculos cervicais

3. **Cefaleia em Salvas**
   - Assimetria térmica severa na região temporal/orbital
   - Hipertermia localizada durante a crise

### Correlação Topográfica
A análise correlaciona o padrão térmico com:
- Localização da dor relatada
- Intensidade da dor (escala 0-10)
- Tipo de cefaleia
- Características temporais (frequência, duração)

## Estrutura do Laudo BTT

1. **DADOS DO EXAME**
   - Data e hora
   - Sintomatologia do paciente
   - Tipo e localização da cefaleia

2. **TÉCNICA**
   - Equipamento
   - Condições de aquisição
   - Regiões BTT examinadas

3. **ACHADOS TERMOGRÁFICOS**
   - Temperatura de cada região BTT
   - Assimetrias detectadas (com valores de ΔT)
   - Padrão térmico geral
   - Gradientes térmicos

4. **CORRELAÇÃO CLÍNICA**
   - Correlação entre padrão térmico e sintomas
   - Análise topográfica (dor vs. alteração térmica)
   - Compatibilidade com tipo de cefaleia

5. **INTERPRETAÇÃO**
   - Significado dos achados
   - Possíveis mecanismos fisiopatológicos
   - Diagnósticos diferenciais

6. **CONCLUSÃO**
   - Resumo objetivo
   - Compatibilidade com hipótese clínica

7. **RECOMENDAÇÕES**
   - Conduta sugerida
   - Exames complementares
   - Reavaliação

## Diretrizes de Escrita

- Use linguagem médica formal especializada
- Baseie-se em evidências termográficas
- Correlacione sempre com sintomas relatados
- Seja cauteloso com diagnósticos - use "sugere", "compatível com", "pode indicar"
- Cite valores numéricos (temperaturas, ΔT)
- Explique significado clínico dos achados
- Mantenha objetividade científica

## Importante

- BTT é método complementar, não substitui avaliação clínica completa
- Sempre recomendar correlação com neurologista
- Indicar limitações quando apropriado
- Não fazer diagnósticos definitivos
- Considerar fatores confundidores (ambiente, medicação, etc.)
"""


def get_dermatome_prompt(exam_data: Dict[str, Any]) -> str:
    """
    Gera prompt específico para análise de dermátomos.

    Args:
        exam_data: Dados do exame incluindo:
            - patient_name: Nome do paciente
            - exam_date: Data do exame
            - clinical_indication: Indicação clínica
            - dermatome_analyses: Lista de análises de dermátomos
            - equipment: Equipamento usado

    Returns:
        Prompt formatado para Claude
    """
    patient_name = exam_data.get('patient_name', 'Não informado')
    exam_date = exam_data.get('exam_date', 'Não informado')
    clinical_indication = exam_data.get('clinical_indication', 'Não informada')
    equipment = exam_data.get('equipment', 'Câmera termográfica FLIR')
    analyses = exam_data.get('dermatome_analyses', [])

    # Formata dados das análises
    analysis_text = []
    for analysis in analyses:
        dermatome = analysis.get('dermatome', 'N/A')
        left_temp = analysis.get('left_temp', 0)
        right_temp = analysis.get('right_temp', 0)
        delta_t = analysis.get('delta_t', 0)
        classification = analysis.get('classification', 'N/A')

        analysis_text.append(f"""
Dermátomo {dermatome}:
- Temperatura lado esquerdo: {left_temp:.2f}°C
- Temperatura lado direito: {right_temp:.2f}°C
- ΔT (diferença): {delta_t:.2f}°C
- Classificação: {classification}
""")

    analyses_formatted = "\n".join(analysis_text)

    prompt = f"""Com base nos seguintes dados termográficos, gere um laudo médico completo de análise de dermátomos:

## DADOS DO PACIENTE
- Nome: {patient_name}
- Data do exame: {exam_date}

## INDICAÇÃO CLÍNICA
{clinical_indication}

## EQUIPAMENTO
{equipment}

## ANÁLISES TERMOGRÁFICAS DOS DERMÁTOMOS
{analyses_formatted}

Gere um laudo médico profissional seguindo a estrutura indicada no system prompt.
Seja detalhado na interpretação clínica e forneça recomendações adequadas baseadas nos achados.
"""

    return prompt


def get_btt_prompt(exam_data: Dict[str, Any]) -> str:
    """
    Gera prompt específico para análise BTT.

    Args:
        exam_data: Dados do exame incluindo:
            - patient_name: Nome do paciente
            - exam_date: Data do exame
            - headache_type: Tipo de cefaleia
            - pain_location: Localização da dor
            - pain_intensity: Intensidade (0-10)
            - btt_regions: Dict com temperaturas das regiões
            - asymmetries: Lista de assimetrias detectadas

    Returns:
        Prompt formatado para Claude
    """
    patient_name = exam_data.get('patient_name', 'Não informado')
    exam_date = exam_data.get('exam_date', 'Não informado')
    headache_type = exam_data.get('headache_type', 'Não especificada')
    pain_location = exam_data.get('pain_location', 'Não especificada')
    pain_intensity = exam_data.get('pain_intensity', 0)
    equipment = exam_data.get('equipment', 'Câmera termográfica FLIR')

    regions = exam_data.get('btt_regions', {})
    asymmetries = exam_data.get('asymmetries', [])

    # Formata regiões
    regions_text = []
    for region, temp in regions.items():
        regions_text.append(f"- {region}: {temp:.2f}°C")
    regions_formatted = "\n".join(regions_text)

    # Formata assimetrias
    asymmetries_text = []
    if asymmetries:
        for asym in asymmetries:
            asymmetries_text.append(
                f"- {asym.get('regions', 'N/A')}: ΔT = {asym.get('delta_t', 0):.2f}°C "
                f"({asym.get('classification', 'N/A')})"
            )
    else:
        asymmetries_text.append("- Nenhuma assimetria significativa detectada")

    asymmetries_formatted = "\n".join(asymmetries_text)

    prompt = f"""Com base nos seguintes dados termográficos BTT, gere um laudo médico completo de análise de cefaleia:

## DADOS DO PACIENTE
- Nome: {patient_name}
- Data do exame: {exam_date}

## SINTOMATOLOGIA
- Tipo de cefaleia: {headache_type}
- Localização da dor: {pain_location}
- Intensidade da dor: {pain_intensity}/10

## EQUIPAMENTO
{equipment}

## ANÁLISE TERMOGRÁFICA BTT

### Temperaturas das Regiões:
{regions_formatted}

### Assimetrias Detectadas:
{asymmetries_formatted}

Gere um laudo médico profissional seguindo a estrutura indicada no system prompt.
Faça a correlação entre o padrão térmico e os sintomas relatados.
Forneça interpretação clínica fundamentada e recomendações apropriadas.
"""

    return prompt


def get_system_prompt(exam_type: str) -> str:
    """
    Retorna o system prompt apropriado para o tipo de exame.

    Args:
        exam_type: 'dermatome' ou 'btt'

    Returns:
        System prompt correspondente
    """
    if exam_type.lower() == 'dermatome':
        return DERMATOME_SYSTEM_PROMPT
    elif exam_type.lower() == 'btt':
        return BTT_SYSTEM_PROMPT
    else:
        raise ValueError(f"Tipo de exame não reconhecido: {exam_type}")


if __name__ == '__main__':
    # Teste dos prompts
    print("=== Teste de Prompts ===\n")

    # Teste 1: Dermatome
    dermatome_data = {
        'patient_name': 'João Silva',
        'exam_date': '2024-01-15 14:30',
        'clinical_indication': 'Dor cervical irradiada para membro superior esquerdo',
        'equipment': 'FLIR T540',
        'dermatome_analyses': [
            {
                'dermatome': 'C5',
                'left_temp': 34.2,
                'right_temp': 35.5,
                'delta_t': 1.3,
                'classification': 'Moderada'
            },
            {
                'dermatome': 'C6',
                'left_temp': 34.8,
                'right_temp': 35.0,
                'delta_t': 0.2,
                'classification': 'Normal'
            }
        ]
    }

    dermatome_prompt = get_dermatome_prompt(dermatome_data)
    print("PROMPT DE DERMÁTOMO:")
    print(dermatome_prompt[:500] + "...\n")

    # Teste 2: BTT
    btt_data = {
        'patient_name': 'Maria Santos',
        'exam_date': '2024-01-15 15:00',
        'headache_type': 'Enxaqueca',
        'pain_location': 'Temporal esquerda',
        'pain_intensity': 8,
        'btt_regions': {
            'frontal': 35.2,
            'parietal_left': 34.8,
            'parietal_right': 35.6,
            'temporal_left': 34.5,
            'temporal_right': 35.4,
            'occipital': 35.0
        },
        'asymmetries': [
            {
                'regions': 'Parietal L/R',
                'delta_t': 0.8,
                'classification': 'Leve'
            },
            {
                'regions': 'Temporal L/R',
                'delta_t': 0.9,
                'classification': 'Leve'
            }
        ]
    }

    btt_prompt = get_btt_prompt(btt_data)
    print("PROMPT BTT:")
    print(btt_prompt[:500] + "...\n")

    print("Teste concluído!")
