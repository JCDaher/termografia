"""
Módulo para detecção automática de pontos/regiões quentes em imagens térmicas.

Este módulo implementa algoritmos para identificar automaticamente áreas de
interesse (hotspots) em dados térmicos, sem necessidade de desenhar ROIs manualmente.

Author: Dr. Jorge Cecílio Daher Jr.
"""

import numpy as np
import cv2
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class HotspotDetector:
    """Detector automático de regiões quentes em imagens térmicas."""

    def __init__(
        self,
        percentile_threshold: float = 80.0,
        min_region_size: int = 100,
        max_regions: int = 2
    ):
        """
        Inicializa o detector de hotspots.

        Args:
            percentile_threshold: Percentil de temperatura para considerar como "quente" (0-100)
            min_region_size: Tamanho mínimo da região em pixels
            max_regions: Número máximo de regiões a detectar
        """
        self.percentile_threshold = percentile_threshold
        self.min_region_size = min_region_size
        self.max_regions = max_regions

    def detect_hotspots(
        self,
        thermal_data: np.ndarray,
        method: str = 'percentile'
    ) -> List[Dict]:
        """
        Detecta automaticamente regiões quentes na imagem térmica.

        Args:
            thermal_data: Array numpy com dados de temperatura
            method: Método de detecção ('percentile', 'otsu', 'adaptive')

        Returns:
            Lista de dicionários com informações sobre cada região detectada:
            {
                'bbox': (x, y, w, h),  # Bounding box
                'centroid': (cx, cy),   # Centro da região
                'area': int,            # Área em pixels
                'temp_mean': float,     # Temperatura média
                'temp_max': float,      # Temperatura máxima
                'position': str,        # 'left' ou 'right'
                'contour': np.ndarray   # Contorno da região
            }
        """
        if thermal_data is None or thermal_data.size == 0:
            logger.warning("Dados térmicos inválidos para detecção")
            return []

        logger.info(f"Detectando hotspots com método '{method}'")
        logger.info(f"  Dados térmicos: shape={thermal_data.shape}, "
                   f"temp_range=[{np.min(thermal_data):.2f}, {np.max(thermal_data):.2f}]°C")

        # Criar máscara binária de regiões quentes
        if method == 'percentile':
            mask = self._threshold_percentile(thermal_data)
        elif method == 'otsu':
            mask = self._threshold_otsu(thermal_data)
        elif method == 'adaptive':
            mask = self._threshold_adaptive(thermal_data)
        else:
            raise ValueError(f"Método desconhecido: {method}")

        # Limpar ruído na máscara
        mask = self._clean_mask(mask)

        # Encontrar componentes conectados (regiões)
        regions = self._find_regions(mask, thermal_data)

        # Filtrar por tamanho mínimo
        regions = [r for r in regions if r['area'] >= self.min_region_size]

        # Ordenar por temperatura média (maior primeiro)
        regions.sort(key=lambda r: r['temp_mean'], reverse=True)

        # Limitar ao número máximo de regiões
        regions = regions[:self.max_regions]

        # Classificar posição (esquerda/direita)
        regions = self._classify_positions(regions, thermal_data.shape[1])

        logger.info(f"  ✅ {len(regions)} região(ões) quente(s) detectada(s)")
        for i, region in enumerate(regions):
            logger.info(f"    Região {i+1}: {region['position']}, "
                       f"temp_média={region['temp_mean']:.2f}°C, "
                       f"área={region['area']} pixels")

        return regions

    def _threshold_percentile(self, thermal_data: np.ndarray) -> np.ndarray:
        """
        Cria máscara usando threshold baseado em percentil.

        Args:
            thermal_data: Dados térmicos

        Returns:
            Máscara binária (255 = quente, 0 = frio)
        """
        threshold_temp = np.percentile(thermal_data, self.percentile_threshold)
        logger.info(f"  Threshold (percentil {self.percentile_threshold}): {threshold_temp:.2f}°C")

        mask = (thermal_data >= threshold_temp).astype(np.uint8) * 255
        return mask

    def _threshold_otsu(self, thermal_data: np.ndarray) -> np.ndarray:
        """
        Cria máscara usando método de Otsu (threshold automático).

        Args:
            thermal_data: Dados térmicos

        Returns:
            Máscara binária
        """
        # Normalizar para 0-255 para Otsu
        normalized = cv2.normalize(thermal_data, None, 0, 255, cv2.NORM_MINMAX)
        normalized = normalized.astype(np.uint8)

        # Aplicar Otsu
        threshold_value, mask = cv2.threshold(
            normalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        # Converter threshold de volta para temperatura
        temp_range = np.max(thermal_data) - np.min(thermal_data)
        threshold_temp = np.min(thermal_data) + (threshold_value / 255.0) * temp_range
        logger.info(f"  Threshold (Otsu): {threshold_temp:.2f}°C")

        return mask

    def _threshold_adaptive(self, thermal_data: np.ndarray) -> np.ndarray:
        """
        Cria máscara usando threshold adaptativo local.

        Args:
            thermal_data: Dados térmicos

        Returns:
            Máscara binária
        """
        # Normalizar para 0-255
        normalized = cv2.normalize(thermal_data, None, 0, 255, cv2.NORM_MINMAX)
        normalized = normalized.astype(np.uint8)

        # Aplicar threshold adaptativo
        mask = cv2.adaptiveThreshold(
            normalized,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,  # Tamanho da vizinhança
            -5   # Constante subtraída da média
        )

        logger.info(f"  Threshold adaptativo aplicado")
        return mask

    def _clean_mask(self, mask: np.ndarray) -> np.ndarray:
        """
        Remove ruído da máscara usando operações morfológicas.

        Args:
            mask: Máscara binária

        Returns:
            Máscara limpa
        """
        # Elemento estruturante
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

        # Erosão seguida de dilatação (opening) - remove ruído pequeno
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Dilatação seguida de erosão (closing) - preenche buracos
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        return mask

    def _find_regions(
        self,
        mask: np.ndarray,
        thermal_data: np.ndarray
    ) -> List[Dict]:
        """
        Encontra regiões conectadas na máscara.

        Args:
            mask: Máscara binária
            thermal_data: Dados térmicos originais

        Returns:
            Lista de regiões detectadas
        """
        # Encontrar contornos
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        regions = []
        for contour in contours:
            # Calcular área
            area = cv2.contourArea(contour)
            if area < self.min_region_size:
                continue

            # Bounding box
            x, y, w, h = cv2.boundingRect(contour)

            # Centróide
            M = cv2.moments(contour)
            if M['m00'] > 0:
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])
            else:
                cx, cy = x + w // 2, y + h // 2

            # Criar máscara para esta região específica
            region_mask = np.zeros_like(mask)
            cv2.drawContours(region_mask, [contour], 0, 255, -1)

            # Extrair temperaturas da região
            region_temps = thermal_data[region_mask == 255]

            if len(region_temps) == 0:
                continue

            regions.append({
                'bbox': (x, y, w, h),
                'centroid': (cx, cy),
                'area': int(area),
                'temp_mean': float(np.mean(region_temps)),
                'temp_max': float(np.max(region_temps)),
                'temp_min': float(np.min(region_temps)),
                'contour': contour,
                'position': None  # Será preenchido depois
            })

        return regions

    def _classify_positions(
        self,
        regions: List[Dict],
        image_width: int
    ) -> List[Dict]:
        """
        Classifica regiões como 'left' ou 'right' baseado na posição horizontal.

        Args:
            regions: Lista de regiões
            image_width: Largura da imagem

        Returns:
            Lista de regiões com campo 'position' preenchido
        """
        center_x = image_width / 2

        for region in regions:
            cx, _ = region['centroid']
            region['position'] = 'left' if cx < center_x else 'right'

        return regions

    def detect_left_right_hotspots(
        self,
        thermal_data: np.ndarray,
        method: str = 'percentile'
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Detecta as duas principais regiões quentes (esquerda e direita) e retorna
        suas temperaturas médias.

        Args:
            thermal_data: Dados térmicos
            method: Método de detecção

        Returns:
            Tupla (temp_esquerda, temp_direita) ou (None, None) se não detectar
        """
        regions = self.detect_hotspots(thermal_data, method)

        if not regions:
            return None, None

        # Separar por posição
        left_regions = [r for r in regions if r['position'] == 'left']
        right_regions = [r for r in regions if r['position'] == 'right']

        # Pegar a região mais quente de cada lado
        temp_left = left_regions[0]['temp_mean'] if left_regions else None
        temp_right = right_regions[0]['temp_mean'] if right_regions else None

        return temp_left, temp_right
