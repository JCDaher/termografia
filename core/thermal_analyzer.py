"""
Analisador térmico para detecção de assimetrias e análise BTT.
Calcula ΔT entre ROIs e classifica assimetrias térmicas.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class AsymmetryResult:
    """Resultado de análise de assimetria térmica."""
    delta_t: float  # Diferença de temperatura em °C
    classification: str  # Normal, Leve, Moderada, Severa
    left_temp: float  # Temperatura média do lado esquerdo
    right_temp: float  # Temperatura média do lado direito
    clinical_significance: str  # Significado clínico
    confidence: float  # Nível de confiança (0-1)


@dataclass
class BTTResult:
    """Resultado de análise BTT (Brain Thermal Tunnel)."""
    regions: Dict[str, float]  # Temperaturas por região
    asymmetries: List[Dict[str, Any]]  # Assimetrias detectadas
    thermal_pattern: str  # Descrição do padrão térmico
    headache_correlation: Optional[str]  # Correlação com cefaleia
    max_delta_t: float  # Maior ΔT encontrado


class ThermalAnalyzer:
    """Analisador de dados térmicos para aplicações médicas."""

    # Limites de classificação de assimetria (em °C)
    THRESHOLD_NORMAL = 0.5
    THRESHOLD_MILD = 1.0
    THRESHOLD_MODERATE = 1.5

    # Dermátomos cervicais
    CERVICAL_DERMATOMES = {
        'C3': 'Região posterior do pescoço e ombro superior',
        'C4': 'Região superior do ombro',
        'C5': 'Região lateral do braço',
        'C6': 'Antebraço lateral e polegar',
        'C7': 'Antebraço posterior e dedos médios',
        'C8': 'Antebraço medial e dedo mínimo',
        'T1': 'Região medial do braço'
    }

    # Regiões BTT
    BTT_REGIONS = {
        'frontal': 'Região frontal',
        'parietal_left': 'Parietal esquerdo',
        'parietal_right': 'Parietal direito',
        'temporal_left': 'Temporal esquerdo',
        'temporal_right': 'Temporal direito',
        'occipital': 'Região occipital'
    }

    def __init__(self):
        """Inicializa o analisador térmico."""
        self.analysis_history = []

    def analyze_asymmetry(self, left_temp: float, right_temp: float,
                         dermatome: Optional[str] = None) -> AsymmetryResult:
        """
        Analisa assimetria térmica entre lados esquerdo e direito.

        Args:
            left_temp: Temperatura média do lado esquerdo (°C)
            right_temp: Temperatura média do lado direito (°C)
            dermatome: Nome do dermátomo (opcional)

        Returns:
            Resultado da análise de assimetria
        """
        # Calcula ΔT (sempre positivo)
        delta_t = abs(left_temp - right_temp)

        # Classifica assimetria
        classification = self._classify_asymmetry(delta_t)

        # Determina significado clínico
        clinical_significance = self._get_clinical_significance(
            delta_t, classification, dermatome
        )

        # Calcula confiança (baseado em critérios clínicos)
        confidence = self._calculate_confidence(delta_t, classification)

        result = AsymmetryResult(
            delta_t=delta_t,
            classification=classification,
            left_temp=left_temp,
            right_temp=right_temp,
            clinical_significance=clinical_significance,
            confidence=confidence
        )

        # Registra histórico
        self.analysis_history.append(result)

        return result

    def _classify_asymmetry(self, delta_t: float) -> str:
        """
        Classifica assimetria baseado no ΔT.

        Critérios:
        - Normal: ΔT < 0.5°C
        - Leve: 0.5°C ≤ ΔT < 1.0°C
        - Moderada: 1.0°C ≤ ΔT < 1.5°C
        - Severa: ΔT ≥ 1.5°C

        Args:
            delta_t: Diferença de temperatura

        Returns:
            Classificação da assimetria
        """
        if delta_t < self.THRESHOLD_NORMAL:
            return "Normal"
        elif delta_t < self.THRESHOLD_MILD:
            return "Leve"
        elif delta_t < self.THRESHOLD_MODERATE:
            return "Moderada"
        else:
            return "Severa"

    def _get_clinical_significance(self, delta_t: float, classification: str,
                                   dermatome: Optional[str] = None) -> str:
        """
        Determina o significado clínico da assimetria.

        Args:
            delta_t: Diferença de temperatura
            classification: Classificação da assimetria
            dermatome: Dermátomo analisado

        Returns:
            Descrição do significado clínico
        """
        base_text = ""

        if classification == "Normal":
            base_text = "Assimetria dentro dos limites de normalidade. "
            base_text += "Não indica processo inflamatório ou radiculopatia significativa."

        elif classification == "Leve":
            base_text = "Assimetria térmica leve detectada. "
            base_text += "Pode indicar processo inflamatório inicial ou irritação radicular leve. "
            base_text += "Recomenda-se correlação clínica e acompanhamento."

        elif classification == "Moderada":
            base_text = "Assimetria térmica moderada. "
            base_text += "Sugere processo inflamatório ativo ou radiculopatia. "
            base_text += "Indica necessidade de investigação clínica complementar."

        else:  # Severa
            base_text = "Assimetria térmica severa detectada. "
            base_text += "Indica processo inflamatório significativo ou radiculopatia importante. "
            base_text += "Recomenda-se avaliação médica urgente e investigação complementar."

        # Adiciona informação sobre dermátomo se disponível
        if dermatome and dermatome in self.CERVICAL_DERMATOMES:
            base_text += f"\n\nDermátomo {dermatome}: {self.CERVICAL_DERMATOMES[dermatome]}."

        return base_text

    def _calculate_confidence(self, delta_t: float, classification: str) -> float:
        """
        Calcula nível de confiança da análise.

        Args:
            delta_t: Diferença de temperatura
            classification: Classificação

        Returns:
            Confiança entre 0 e 1
        """
        # Quanto maior o ΔT, maior a confiança
        # Ajustado para não ultrapassar 1.0
        confidence = min(delta_t / 2.0, 1.0)

        # Se está próximo dos limites de classificação, reduz confiança
        thresholds = [self.THRESHOLD_NORMAL, self.THRESHOLD_MILD, self.THRESHOLD_MODERATE]
        for threshold in thresholds:
            if abs(delta_t - threshold) < 0.1:
                confidence *= 0.85

        return round(confidence, 2)

    def analyze_roi_statistics(self, thermal_data: np.ndarray,
                              roi_mask: np.ndarray) -> Dict[str, float]:
        """
        Calcula estatísticas detalhadas de uma ROI.

        Args:
            thermal_data: Dados térmicos (array 2D)
            roi_mask: Máscara da ROI

        Returns:
            Dicionário com estatísticas
        """
        # Extrai temperaturas da ROI
        roi_temps = thermal_data[roi_mask > 0]

        if len(roi_temps) == 0:
            return {
                'mean': 0.0,
                'median': 0.0,
                'std': 0.0,
                'min': 0.0,
                'max': 0.0,
                'q25': 0.0,
                'q75': 0.0,
                'count': 0
            }

        return {
            'mean': float(np.mean(roi_temps)),
            'median': float(np.median(roi_temps)),
            'std': float(np.std(roi_temps)),
            'min': float(np.min(roi_temps)),
            'max': float(np.max(roi_temps)),
            'q25': float(np.percentile(roi_temps, 25)),
            'q75': float(np.percentile(roi_temps, 75)),
            'count': len(roi_temps)
        }

    def analyze_btt(self, region_temps: Dict[str, float],
                   headache_info: Optional[Dict[str, Any]] = None) -> BTTResult:
        """
        Analisa padrão térmico BTT (Brain Thermal Tunnel) para cefaleia.

        Args:
            region_temps: Dicionário com temperaturas das regiões BTT
            headache_info: Informações sobre cefaleia (tipo, localização, intensidade)

        Returns:
            Resultado da análise BTT
        """
        # Valida regiões
        required_regions = ['frontal', 'parietal_left', 'parietal_right', 'occipital']
        for region in required_regions:
            if region not in region_temps:
                logger.warning(f"Região BTT ausente: {region}")

        # Detecta assimetrias entre lados
        asymmetries = []

        # Parietal L vs R
        if 'parietal_left' in region_temps and 'parietal_right' in region_temps:
            parietal_delta = abs(region_temps['parietal_left'] - region_temps['parietal_right'])
            if parietal_delta >= self.THRESHOLD_NORMAL:
                asymmetries.append({
                    'regions': 'Parietal L/R',
                    'delta_t': parietal_delta,
                    'classification': self._classify_asymmetry(parietal_delta)
                })

        # Temporal L vs R
        if 'temporal_left' in region_temps and 'temporal_right' in region_temps:
            temporal_delta = abs(region_temps['temporal_left'] - region_temps['temporal_right'])
            if temporal_delta >= self.THRESHOLD_NORMAL:
                asymmetries.append({
                    'regions': 'Temporal L/R',
                    'delta_t': temporal_delta,
                    'classification': self._classify_asymmetry(temporal_delta)
                })

        # Calcula maior ΔT
        max_delta = 0.0
        for asym in asymmetries:
            if asym['delta_t'] > max_delta:
                max_delta = asym['delta_t']

        # Analisa padrão térmico
        thermal_pattern = self._analyze_thermal_pattern(region_temps, asymmetries)

        # Correlação com cefaleia
        headache_correlation = None
        if headache_info:
            headache_correlation = self._correlate_headache(
                region_temps, asymmetries, headache_info
            )

        return BTTResult(
            regions=region_temps,
            asymmetries=asymmetries,
            thermal_pattern=thermal_pattern,
            headache_correlation=headache_correlation,
            max_delta_t=max_delta
        )

    def _analyze_thermal_pattern(self, region_temps: Dict[str, float],
                                asymmetries: List[Dict[str, Any]]) -> str:
        """
        Analisa o padrão térmico geral.

        Args:
            region_temps: Temperaturas das regiões
            asymmetries: Assimetrias detectadas

        Returns:
            Descrição do padrão térmico
        """
        pattern_parts = []

        # Temperatura média geral
        temps = list(region_temps.values())
        avg_temp = np.mean(temps)
        pattern_parts.append(f"Temperatura média: {avg_temp:.1f}°C")

        # Gradiente frontal-occipital
        if 'frontal' in region_temps and 'occipital' in region_temps:
            gradient = region_temps['frontal'] - region_temps['occipital']
            if abs(gradient) > 0.5:
                direction = "maior" if gradient > 0 else "menor"
                pattern_parts.append(
                    f"Gradiente frontal-occipital: região frontal {direction} que occipital ({abs(gradient):.1f}°C)"
                )

        # Número de assimetrias
        if asymmetries:
            pattern_parts.append(f"{len(asymmetries)} assimetria(s) detectada(s)")
        else:
            pattern_parts.append("Padrão térmico simétrico bilateral")

        return ". ".join(pattern_parts) + "."

    def _correlate_headache(self, region_temps: Dict[str, float],
                          asymmetries: List[Dict[str, Any]],
                          headache_info: Dict[str, Any]) -> str:
        """
        Correlaciona padrão térmico com sintomas de cefaleia.

        Args:
            region_temps: Temperaturas das regiões
            asymmetries: Assimetrias detectadas
            headache_info: Informações sobre cefaleia

        Returns:
            Descrição da correlação
        """
        correlation_parts = []

        headache_type = headache_info.get('type', 'não especificada')
        pain_location = headache_info.get('location', 'não especificada')
        pain_intensity = headache_info.get('intensity', 0)

        correlation_parts.append(f"Tipo de cefaleia: {headache_type}")
        correlation_parts.append(f"Localização da dor: {pain_location}")
        correlation_parts.append(f"Intensidade: {pain_intensity}/10")

        # Correlação com assimetrias
        if asymmetries:
            correlation_parts.append("\nAssimetrias detectadas:")
            for asym in asymmetries:
                correlation_parts.append(
                    f"- {asym['regions']}: ΔT = {asym['delta_t']:.1f}°C ({asym['classification']})"
                )

            # Análise de correlação topográfica
            if 'temporal' in pain_location.lower():
                temporal_asyms = [a for a in asymmetries if 'Temporal' in a['regions']]
                if temporal_asyms:
                    correlation_parts.append(
                        "\n✓ Correlação positiva: Assimetria térmica em região temporal "
                        "corresponde à localização da dor relatada."
                    )
        else:
            correlation_parts.append(
                "\nNenhuma assimetria térmica significativa detectada. "
                "Considerar outras etiologias não vasculares para a cefaleia."
            )

        return "\n".join(correlation_parts)

    def generate_dermatome_report(self, analyses: List[AsymmetryResult],
                                 dermatome_names: List[str]) -> str:
        """
        Gera relatório de análise de dermátomos.

        Args:
            analyses: Lista de resultados de análise
            dermatome_names: Nomes dos dermátomos correspondentes

        Returns:
            Relatório formatado
        """
        if len(analyses) != len(dermatome_names):
            raise ValueError("Número de análises deve corresponder ao número de dermátomos")

        report_lines = []
        report_lines.append("=== ANÁLISE DE DERMÁTOMOS ===\n")

        for analysis, dermatome in zip(analyses, dermatome_names):
            report_lines.append(f"Dermátomo {dermatome}:")
            report_lines.append(f"  Temperatura Esquerda: {analysis.left_temp:.2f}°C")
            report_lines.append(f"  Temperatura Direita: {analysis.right_temp:.2f}°C")
            report_lines.append(f"  ΔT: {analysis.delta_t:.2f}°C")
            report_lines.append(f"  Classificação: {analysis.classification}")
            report_lines.append(f"  Confiança: {analysis.confidence:.0%}")
            report_lines.append("")

        # Resumo
        report_lines.append("=== RESUMO ===")
        severe_count = sum(1 for a in analyses if a.classification == "Severa")
        moderate_count = sum(1 for a in analyses if a.classification == "Moderada")
        mild_count = sum(1 for a in analyses if a.classification == "Leve")

        if severe_count > 0:
            report_lines.append(f"⚠️  {severe_count} assimetria(s) severa(s) detectada(s)")
        if moderate_count > 0:
            report_lines.append(f"⚠️  {moderate_count} assimetria(s) moderada(s) detectada(s)")
        if mild_count > 0:
            report_lines.append(f"ℹ️  {mild_count} assimetria(s) leve(s) detectada(s)")

        if severe_count == 0 and moderate_count == 0 and mild_count == 0:
            report_lines.append("✓ Todos os dermátomos dentro da normalidade")

        return "\n".join(report_lines)


class ThermalAnalyzerError(Exception):
    """Exceção para erros do analisador térmico."""
    pass


if __name__ == '__main__':
    # Teste básico
    print("=== Teste do ThermalAnalyzer ===\n")

    analyzer = ThermalAnalyzer()

    # Teste de assimetria
    print("1. Teste de assimetria térmica:")
    result = analyzer.analyze_asymmetry(34.5, 35.8, "C5")
    print(f"   ΔT: {result.delta_t:.2f}°C")
    print(f"   Classificação: {result.classification}")
    print(f"   Confiança: {result.confidence:.0%}\n")

    # Teste BTT
    print("2. Teste de análise BTT:")
    btt_temps = {
        'frontal': 35.2,
        'parietal_left': 34.8,
        'parietal_right': 35.5,
        'temporal_left': 35.0,
        'temporal_right': 35.1,
        'occipital': 34.9
    }

    headache = {
        'type': 'Enxaqueca',
        'location': 'Temporal esquerda',
        'intensity': 7
    }

    btt_result = analyzer.analyze_btt(btt_temps, headache)
    print(f"   Padrão térmico: {btt_result.thermal_pattern}")
    print(f"   Assimetrias: {len(btt_result.asymmetries)}")
    print(f"   Máximo ΔT: {btt_result.max_delta_t:.2f}°C")

    print("\nTeste concluído!")
