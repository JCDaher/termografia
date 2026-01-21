"""
Analisador de múltiplos pontos para termografia.
Processa templates anatômicos e gera análises comparativas multi-ponto.
"""

import numpy as np
import cv2
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

from core.anatomical_template import (
    AnatomicalTemplate,
    AnatomicalROI,
    MultiPointAnalysisResult
)

logger = logging.getLogger(__name__)


class MultiPointAnalyzer:
    """
    Analisador que processa múltiplas ROIs e gera análises comparativas.
    """

    def __init__(self):
        """Inicializa o analisador."""
        pass

    def analyze_template(
        self,
        template: AnatomicalTemplate,
        thermal_data: np.ndarray,
        visible_image: Optional[np.ndarray] = None,
        image_name: str = "Unknown"
    ) -> MultiPointAnalysisResult:
        """
        Analisa todas as ROIs de um template em uma imagem térmica.

        Args:
            template: Template anatômico com ROIs
            thermal_data: Dados térmicos (array 2D com temperaturas)
            visible_image: Imagem visível (opcional, para escalonamento)
            image_name: Nome da imagem sendo processada

        Returns:
            MultiPointAnalysisResult com todas as temperaturas e comparações
        """
        logger.info(f"Analisando template '{template.name}' na imagem '{image_name}'")
        logger.info(f"  Template com {len(template.rois)} ROIs")
        logger.info(f"  Dados térmicos: shape={thermal_data.shape}")

        # Calcula fatores de escala se houver imagem visível
        if visible_image is not None:
            visible_h, visible_w = visible_image.shape[:2]
            thermal_h, thermal_w = thermal_data.shape[:2]
            scale_x = thermal_w / visible_w
            scale_y = thermal_h / visible_h
            logger.info(f"  Escala: x={scale_x:.4f}, y={scale_y:.4f}")
        else:
            scale_x = scale_y = 1.0

        # Processa cada ROI e calcula temperatura
        roi_temperatures = {}
        roi_pixel_counts = {}

        for roi in template.rois:
            if not roi.coordinates:
                logger.warning(f"  ROI '{roi.name}' sem coordenadas, pulando...")
                continue

            # Escala coordenadas
            scaled_points = [
                (int(x * scale_x), int(y * scale_y))
                for x, y in roi.coordinates
            ]

            # Garante que pontos estão dentro dos limites
            thermal_h, thermal_w = thermal_data.shape[:2]
            scaled_points = [
                (max(0, min(x, thermal_w-1)), max(0, min(y, thermal_h-1)))
                for x, y in scaled_points
            ]

            # Cria máscara para a ROI
            mask = np.zeros(thermal_data.shape[:2], dtype=np.uint8)
            pts = np.array(scaled_points, dtype=np.int32)
            cv2.fillPoly(mask, [pts], 255)

            # Extrai temperaturas da região
            roi_region = thermal_data[mask == 255]

            if len(roi_region) > 0:
                avg_temp = float(np.mean(roi_region))
                roi_temperatures[roi.name] = avg_temp
                roi_pixel_counts[roi.name] = len(roi_region)
                logger.info(f"  ✅ {roi.name}: {avg_temp:.2f}°C ({len(roi_region)} pixels)")
            else:
                logger.warning(f"  ❌ {roi.name}: Nenhum pixel capturado")

        # Gera matriz de comparação (todos vs todos)
        comparison_matrix = self._build_comparison_matrix(roi_temperatures)

        # Analisa grupos de comparação definidos no template
        group_comparisons = self._analyze_comparison_groups(
            template.comparison_groups,
            roi_temperatures
        )

        # Calcula estatísticas gerais
        overall_stats = self._calculate_overall_stats(roi_temperatures, comparison_matrix)

        result = MultiPointAnalysisResult(
            template_name=template.name,
            image_name=image_name,
            roi_temperatures=roi_temperatures,
            roi_pixel_counts=roi_pixel_counts,
            comparison_matrix=comparison_matrix,
            group_comparisons=group_comparisons,
            overall_stats=overall_stats
        )

        logger.info(f"✅ Análise concluída: {len(roi_temperatures)} ROIs processadas")
        return result

    def _build_comparison_matrix(
        self,
        roi_temperatures: Dict[str, float]
    ) -> Dict[str, Dict[str, float]]:
        """
        Constrói matriz de comparação (todos os pontos vs todos os pontos).

        Args:
            roi_temperatures: Dicionário {nome_roi: temperatura}

        Returns:
            Matriz: {roi1: {roi2: delta_t}}
        """
        matrix = {}

        roi_names = list(roi_temperatures.keys())

        for roi1 in roi_names:
            matrix[roi1] = {}
            for roi2 in roi_names:
                if roi1 != roi2:
                    delta_t = roi_temperatures[roi1] - roi_temperatures[roi2]
                    matrix[roi1][roi2] = delta_t

        return matrix

    def _analyze_comparison_groups(
        self,
        comparison_groups: List[List[str]],
        roi_temperatures: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Analisa cada grupo de comparação definido no template.

        Args:
            comparison_groups: Lista de grupos (cada grupo é lista de nomes de ROIs)
            roi_temperatures: Temperaturas de cada ROI

        Returns:
            Lista de resultados por grupo
        """
        results = []

        for group in comparison_groups:
            # Filtra apenas ROIs que têm temperatura medida
            valid_rois = [roi for roi in group if roi in roi_temperatures]

            if len(valid_rois) < 2:
                logger.warning(f"Grupo {group} tem menos de 2 ROIs válidas")
                continue

            # Calcula temperaturas do grupo
            temps = [roi_temperatures[roi] for roi in valid_rois]

            # Calcula delta T máximo no grupo
            max_delta = max(temps) - min(temps)

            # Identifica ROIs com temp máxima e mínima
            max_roi = valid_rois[temps.index(max(temps))]
            min_roi = valid_rois[temps.index(min(temps))]

            # Classifica assimetria (se for grupo bilateral)
            if len(valid_rois) == 2:
                delta_t = abs(temps[0] - temps[1])
                if delta_t < 0.5:
                    classification = "Normal"
                elif delta_t < 1.0:
                    classification = "Leve"
                elif delta_t < 1.5:
                    classification = "Moderada"
                else:
                    classification = "Severa"
            else:
                classification = None

            group_result = {
                'group_rois': valid_rois,
                'temperatures': {roi: roi_temperatures[roi] for roi in valid_rois},
                'max_delta_t': max_delta,
                'max_temp_roi': max_roi,
                'min_temp_roi': min_roi,
                'avg_temp': np.mean(temps),
                'classification': classification
            }

            results.append(group_result)

        return results

    def _calculate_overall_stats(
        self,
        roi_temperatures: Dict[str, float],
        comparison_matrix: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """
        Calcula estatísticas gerais da análise.

        Args:
            roi_temperatures: Temperaturas de cada ROI
            comparison_matrix: Matriz de comparações

        Returns:
            Dicionário com estatísticas
        """
        if not roi_temperatures:
            return {}

        temps = list(roi_temperatures.values())

        # Extrai todos os deltas da matriz
        all_deltas = []
        for roi1_comparisons in comparison_matrix.values():
            all_deltas.extend(roi1_comparisons.values())

        stats = {
            'total_rois': len(roi_temperatures),
            'avg_temperature': np.mean(temps),
            'min_temperature': np.min(temps),
            'max_temperature': np.max(temps),
            'temp_range': np.max(temps) - np.min(temps),
            'std_temperature': np.std(temps),
        }

        if all_deltas:
            stats['avg_delta_t'] = np.mean([abs(d) for d in all_deltas])
            stats['max_delta_t'] = np.max([abs(d) for d in all_deltas])

        return stats

    def generate_comparison_table(
        self,
        result: MultiPointAnalysisResult,
        format: str = "markdown"
    ) -> str:
        """
        Gera tabela de comparação formatada.

        Args:
            result: Resultado da análise
            format: Formato da tabela ("markdown", "html", "text")

        Returns:
            String com tabela formatada
        """
        if format == "markdown":
            return self._generate_markdown_table(result)
        elif format == "html":
            return self._generate_html_table(result)
        else:
            return self._generate_text_table(result)

    def _generate_markdown_table(self, result: MultiPointAnalysisResult) -> str:
        """Gera tabela em formato Markdown."""
        lines = []

        lines.append(f"# Análise Multi-Ponto: {result.template_name}")
        lines.append(f"**Imagem:** {result.image_name}\n")

        # Tabela de temperaturas individuais
        lines.append("## Temperaturas por ROI\n")
        lines.append("| ROI | Temperatura | Pixels |")
        lines.append("|-----|-------------|--------|")

        for roi_name in sorted(result.roi_temperatures.keys()):
            temp = result.roi_temperatures[roi_name]
            pixels = result.roi_pixel_counts.get(roi_name, 0)
            lines.append(f"| {roi_name} | {temp:.2f}°C | {pixels} |")

        # Estatísticas gerais
        lines.append("\n## Estatísticas Gerais\n")
        stats = result.overall_stats
        lines.append(f"- **Total de ROIs:** {stats.get('total_rois', 0)}")
        lines.append(f"- **Temperatura Média:** {stats.get('avg_temperature', 0):.2f}°C")
        lines.append(f"- **Amplitude:** {stats.get('temp_range', 0):.2f}°C")
        lines.append(f"- **ΔT Médio:** {stats.get('avg_delta_t', 0):.2f}°C")
        lines.append(f"- **ΔT Máximo:** {stats.get('max_delta_t', 0):.2f}°C")

        # Comparações por grupo
        if result.group_comparisons:
            lines.append("\n## Comparações Bilaterais\n")
            lines.append("| Grupo | ROI 1 | Temp 1 | ROI 2 | Temp 2 | ΔT | Classificação |")
            lines.append("|-------|-------|--------|-------|--------|-----|---------------|")

            for comp in result.group_comparisons:
                if comp['classification']:  # Apenas grupos bilaterais
                    rois = comp['group_rois']
                    temps = comp['temperatures']
                    if len(rois) == 2:
                        delta = abs(temps[rois[0]] - temps[rois[1]])
                        lines.append(
                            f"| {' / '.join(rois)} | {rois[0]} | {temps[rois[0]]:.2f}°C | "
                            f"{rois[1]} | {temps[rois[1]]:.2f}°C | {delta:.2f}°C | "
                            f"{comp['classification']} |"
                        )

        return "\n".join(lines)

    def _generate_text_table(self, result: MultiPointAnalysisResult) -> str:
        """Gera tabela em formato texto simples."""
        lines = []

        lines.append("=" * 70)
        lines.append(f"ANÁLISE MULTI-PONTO: {result.template_name}")
        lines.append(f"Imagem: {result.image_name}")
        lines.append("=" * 70)
        lines.append("")

        # Temperaturas
        lines.append("TEMPERATURAS POR ROI:")
        lines.append("-" * 70)
        for roi_name in sorted(result.roi_temperatures.keys()):
            temp = result.roi_temperatures[roi_name]
            pixels = result.roi_pixel_counts.get(roi_name, 0)
            lines.append(f"  {roi_name:40s} {temp:6.2f}°C  ({pixels:5d} pixels)")

        # Estatísticas
        lines.append("")
        lines.append("ESTATÍSTICAS GERAIS:")
        lines.append("-" * 70)
        stats = result.overall_stats
        lines.append(f"  Total de ROIs processadas: {stats.get('total_rois', 0)}")
        lines.append(f"  Temperatura média:         {stats.get('avg_temperature', 0):.2f}°C")
        lines.append(f"  Amplitude térmica:         {stats.get('temp_range', 0):.2f}°C")
        lines.append(f"  ΔT médio:                  {stats.get('avg_delta_t', 0):.2f}°C")
        lines.append(f"  ΔT máximo:                 {stats.get('max_delta_t', 0):.2f}°C")

        return "\n".join(lines)

    def _generate_html_table(self, result: MultiPointAnalysisResult) -> str:
        """Gera tabela em formato HTML."""
        # Implementação futura se necessário
        return self._generate_markdown_table(result)
