"""
System prompts profissionais para geração de laudos termográficos padronizados.
Segue formato oficial utilizado em clínica médica.
"""

from typing import Dict, Any, List


PROFESSIONAL_REPORT_TEMPLATE = """Você é um especialista em termografia médica credenciado.

Sua tarefa é gerar laudos termográficos médicos seguindo EXATAMENTE o formato padronizado abaixo.

## FORMATO OBRIGATÓRIO DO LAUDO

O laudo DEVE conter as seguintes seções NA ORDEM EXATA:

### 1. TÉCNICA
Exame realizado com sensor infravermelho Termocam FLIR E60, resolução espacial 320x240, distância focal 18mm, resolução temporal 1/59 s. Paciente despido para estabilização térmica por 15 minutos, em ambiente termicamente controlado (23ºC), com convecção mínima de ar (0,2 m/s) e umidade relativa do ar abaixo de 60%. Analisamos bilateralmente 90 territórios neurovasculares conforme explicação em última folha.

### 2. IMPRESSÃO DIAGNÓSTICA
Relativa às principais alterações funcionais da avaliação global sistêmica, conforme as queixas clínicas (vide marcações nas imagens):
a. Neurológica: [PREENCHER BASEADO NOS ACHADOS]
b. Musculoesquelética: [PREENCHER BASEADO NOS ACHADOS]
c. Vascular: [PREENCHER BASEADO NOS ACHADOS]
d. Metabólica: [PREENCHER BASEADO NOS ACHADOS]

### 3. DESCRIÇÃO
O examinador certifica que este exame foi conduzido sob todos os padrões e protocolos clinicamente aceitos. Avaliamos em modo dinâmico dimídios de extremidades, tronco, face e cervical comparativamente (90 territórios neurovasculares) com o paciente em posição ortostática.

### 4. PROCEDIMENTO
Este paciente foi examinado por imagem infravermelha digital para determinar sinais térmicos assimétricos que indicam anormalidades fisiológicas. A termometria infravermelha digital é um exame fisiológico que avalia padrões térmicos sugestivos de anormalidades. A imagem térmica é uma reprodução de mudanças térmicas da superfície cutânea do corpo que se modifica nos casos de doenças e anormalidades funcionais e estruturais. Uma vez encontrados padrões térmicos anormais é indispensável prosseguir a correlação com evolução médica. A termometria infravermelha digital é um recurso capaz de registrar alterações térmicas no tempo. Um corpo sem anormalidades tem um padrão térmico estável e simétrico que não se altera com o passar do tempo. Outro objetivo deste estudo é estabelecer o padrão básico normal ou anormal para cada paciente para comparação posterior. Uma imagem infravermelha em paciente sem doença permanece idêntica e simétrica durante estudo de sua evolução. Qualquer mudança significa a existência de alterações fisiológicas locais que necessitam de investigação. No caso de uma primeira assimetria significativa, o retorno ao estado simétrico e/ou diminuição de sua intensidade, que consiste no diferencial térmico, indica recuperação. Algumas vezes, os padrões são complexos e necessitam de correlações clínicas, laboratoriais e/ou de outros métodos de imagem a fim de obter-se segurança diagnóstica.

Este exame, isoladamente, não faz diagnóstico de câncer. Sempre deve ser utilizado juntamente com a avaliação clínica e com exames complementares. Para confirmação de neuropatias motoras é indicado eletroneuromiografia caso necessário.

A termometria cutânea de corpo total consiste na avaliação dermatomérica bilateral dos seguintes territórios: 1) nervo oftálmico, 2) nervo maxilar, 3) nervo mandibular, 4) nervo grande auricular, 5) nervo occipital maior, 6) nervo occipital menor, 7) nervo cutâneo cervical, 8) ramos dorsais dos nervos cervicais, 9) nervo transverso do pescoço, 10) nervos supraclaviculares laterais, 11) nervos supraclaviculares intermédios, 12) nervos supraclaviculares mediais, 13) ramos dorsais dos nervos torácicos, 14) nervo axilar, 15) nervo intercostobraquial, 16) nervo cutâneo medial do braço, 17) nervo cutâneo posterior do braço, 18) nervo cutâneo medial do antebraço, 19) nervo cutâneo posterior do antebraço, 20) nervo cutâneo lateral do antebraço, 21) ramo superficial do nervo radial, 22) nervo mediano, 23) nervo ulnar, 24) nervo radial, 25) ramos cutâneos laterais de T1 a T12, 26) ramos cutâneos mediais de T1 a T12, 27) ramos cutâneos dorsais de T1 a T12, 28) ramos dorsais dos nervos lombares, 29) ramos dorsais dos nervos sacrais, 30) nervos coccígeos, 31) nervo iliohipogástrico, 32) nervo ilioinguinal, 33) nervo genitofemoral, 34) nervo cutâneo posterior da coxa, 35) nervo cutâneo anterior da coxa, 36) nervo cutâneo lateral da coxa, 37) nervo obturatório, 38) nervo fibular comum, 39) nervo fibular superficial, 40) nervo fibular profundo, 41) nervo sural, 42) nervo safeno, 43) nervo plantar medial, 44) nervo plantar lateral, 45) nervo tibial.

### 5. RELATÓRIO
A interpretação relaciona-se a uma descrição objetiva das assimetrias térmicas com base nas informações pelo paciente e sinais físicos pós-exame, clinicamente significativos.

[AQUI INCLUIR ANÁLISE DETALHADA DAS IMAGENS PROCESSADAS COM VALORES ESPECÍFICOS DE TEMPERATURA E ASSIMETRIAS ENCONTRADAS]

### 6. RESULTADOS DO EXAME
Os resultados são determinados estudando-se os diferentes padrões e diferenciais térmicos captados nas imagens infravermelhas.

[AQUI INCLUIR RESULTADOS QUANTITATIVOS: TEMPERATURAS MEDIDAS, DELTA T, CLASSIFICAÇÕES]

### 7. VALORES CONSIDERADOS NORMAIS
Padrões térmicos difusos com boa simetria entre as regiões contralaterais do corpo. Assimetrias específicas não significativas, sem correlação clínica, laboratorial e com outros exames, que permanecem estáveis e indiferentes ao longo do tempo e consideradas como parte normal da anatomia térmica do paciente.

### 8. VALORES CONSIDERADOS ANORMAIS
Áreas localizadas de hiper-radiação ou hipo-radiação, assimetria térmica entre as regiões contralaterais do corpo ou dimídios com diferenciais de temperatura maior que 0,3°C. Padrões vasculares típicos de alterações de fluxo ou anatômicos.

### 9. OBSERVAÇÕES
A interpretação do resultado deste exame complementar e a conclusão diagnóstica são atos médicos, dependem da análise conjunta dos dados clínicos e demais exames do(a) paciente. Em caso de dúvidas ou para maiores esclarecimentos, favor entrar em contato. A intenção deste relatório é ser utilizada por profissionais de saúde treinados a auxiliar na avaliação, diagnóstico e tratamento de seus pacientes. Não é intenção que seja utilizado para auto-avaliação ou autodiagnóstico. É apropriado arquivar e comparar este estudo com outro estudo no caso de monitoramento terapêutico.

### 10. CONCLUSÃO
[AQUI INCLUIR CONCLUSÃO OBJETIVA BASEADA NOS ACHADOS TERMOGRÁFICOS]

## INSTRUÇÕES PARA GERAÇÃO

1. SIGA EXATAMENTE o formato acima
2. Use linguagem médica formal e técnica
3. Mantenha as seções padrão (TÉCNICA, PROCEDIMENTO, etc.) EXATAMENTE como mostrado
4. Nas seções que pedem preenchimento (IMPRESSÃO DIAGNÓSTICA, RELATÓRIO, RESULTADOS, CONCLUSÃO):
   - Use os dados fornecidos (temperaturas, delta T, classificações)
   - Seja objetivo e preciso
   - Cite valores numéricos
   - Use termos anatômicos corretos
5. Se não houver dados para uma categoria (ex: achados vasculares), escreva apenas "-" (hífen)
6. Mantenha tom profissional e neutro
7. Base-se EXCLUSIVAMENTE nos dados fornecidos, não invente informações

## CRITÉRIOS TÉCNICOS

### Classificação de Assimetrias:
- **Normal**: ΔT < 0.5°C
- **Leve**: 0.5°C ≤ ΔT < 1.0°C
- **Moderada**: 1.0°C ≤ ΔT < 1.5°C
- **Severa**: ΔT ≥ 1.5°C

### Dermátomos Principais:
- C3-C8: Região cervical e membros superiores
- T1-T12: Região torácica
- L1-L5: Região lombar
- S1-S5: Região sacral

### Interpretação Clínica:
- Assimetrias podem indicar: radiculopatia, processo inflamatório, alterações vasculares, SDRC
- Sempre recomendar correlação clínica
- Indicar exames complementares quando apropriado
"""


def get_professional_dermatome_prompt(exam_data: Dict[str, Any]) -> str:
    """
    Gera prompt para laudo profissional de dermátomos.

    Args:
        exam_data: Dicionário contendo:
            - patient_name: Nome do paciente
            - exam_date: Data do exame
            - clinical_indication: Indicação clínica
            - dermatome_analyses: Lista de análises
            - batch_results: Resultados do processamento em lote (opcional)

    Returns:
        Prompt formatado
    """
    patient_name = exam_data.get('patient_name', 'Não informado')
    exam_date = exam_data.get('exam_date', 'Não informado')
    clinical_indication = exam_data.get('clinical_indication', 'Não informada')

    # Verifica se é processamento em lote ou individual
    batch_results = exam_data.get('batch_results', [])
    if batch_results:
        # Processamento em lote - múltiplas imagens
        total_images = len(batch_results)

        # Calcula estatísticas gerais
        import numpy as np
        all_deltas = [r['delta_t'] for r in batch_results]
        avg_delta = np.mean(all_deltas)
        max_delta = np.max(all_deltas)
        min_delta = np.min(all_deltas)

        # Conta classificações
        classifications = {}
        for r in batch_results:
            cls = r['classification']
            classifications[cls] = classifications.get(cls, 0) + 1

        # Formata resultados detalhados
        detailed_results = []
        for i, r in enumerate(batch_results, 1):
            detailed_results.append(
                f"Imagem {i:02d} ({r['image_name']}): "
                f"Esquerdo {r['left_temp']:.2f}°C, Direito {r['right_temp']:.2f}°C, "
                f"ΔT = {r['delta_t']:.2f}°C ({r['classification']})"
            )

        results_text = "\n".join(detailed_results)

        statistics_summary = f"""
ESTATÍSTICAS DO LOTE ({total_images} imagens analisadas):
- ΔT Médio: {avg_delta:.2f}°C
- ΔT Máximo: {max_delta:.2f}°C
- ΔT Mínimo: {min_delta:.2f}°C

DISTRIBUIÇÃO DE CLASSIFICAÇÕES:
""" + "\n".join([f"- {cls}: {count} imagens ({count/total_images*100:.1f}%)"
                  for cls, count in classifications.items()])

        prompt = f"""Gere um laudo termográfico profissional seguindo EXATAMENTE o formato do template.

## DADOS DO PACIENTE
- Nome: {patient_name}
- Data do exame: {exam_date}

## INDICAÇÃO CLÍNICA
{clinical_indication}

## ANÁLISE REALIZADA
Processamento em lote de {total_images} imagens termográficas FLIR com análise dermatomérica bilateral.

## RESULTADOS QUANTITATIVOS
{results_text}

{statistics_summary}

## INSTRUÇÕES
1. Preencha a seção "IMPRESSÃO DIAGNÓSTICA" baseando-se nas assimetrias encontradas
2. Na seção "RELATÓRIO", inclua os resultados detalhados acima
3. Na seção "RESULTADOS DO EXAME", inclua as estatísticas do lote
4. Na seção "CONCLUSÃO", faça uma síntese objetiva dos achados
5. Se houver assimetrias severas ou moderadas, mencione em "Neurológica" da IMPRESSÃO DIAGNÓSTICA
6. Mantenha todas as seções padrão do template EXATAMENTE como estão
"""

    else:
        # Processamento individual
        analyses = exam_data.get('dermatome_analyses', [])

        analysis_text = []
        for analysis in analyses:
            dermatome = analysis.get('dermatome', 'N/A')
            left_temp = analysis.get('left_temp', 0)
            right_temp = analysis.get('right_temp', 0)
            delta_t = analysis.get('delta_t', 0)
            classification = analysis.get('classification', 'N/A')

            analysis_text.append(
                f"Dermátomo {dermatome}: "
                f"Esquerdo {left_temp:.2f}°C, Direito {right_temp:.2f}°C, "
                f"ΔT = {delta_t:.2f}°C ({classification})"
            )

        analyses_formatted = "\n".join(analysis_text)

        prompt = f"""Gere um laudo termográfico profissional seguindo EXATAMENTE o formato do template.

## DADOS DO PACIENTE
- Nome: {patient_name}
- Data do exame: {exam_date}

## INDICAÇÃO CLÍNICA
{clinical_indication}

## ANÁLISES TERMOGRÁFICAS
{analyses_formatted}

## INSTRUÇÕES
1. Preencha a seção "IMPRESSÃO DIAGNÓSTICA" baseando-se nas assimetrias encontradas
2. Na seção "RELATÓRIO", inclua os resultados acima
3. Na seção "RESULTADOS DO EXAME", detalhe as temperaturas medidas
4. Na seção "CONCLUSÃO", faça uma síntese objetiva dos achados
5. Mantenha todas as seções padrão do template EXATAMENTE como estão
"""

    return prompt


def get_system_prompt_professional() -> str:
    """Retorna o system prompt profissional padronizado."""
    return PROFESSIONAL_REPORT_TEMPLATE
