"""
Processador de imagens FLIR radiométricas.
Extrai dados de temperatura de imagens FLIR .jpg e gera heatmaps.
"""

import numpy as np
import cv2
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import logging
from PIL import Image
from PIL.ExifTags import TAGS
import json
import struct

try:
    from flirimageextractor import FlirImageExtractor
    FLIR_EXTRACTOR_AVAILABLE = True
except ImportError:
    FLIR_EXTRACTOR_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("flirimageextractor não disponível - instale com 'pip install flirimageextractor'")

logger = logging.getLogger(__name__)


class FLIRProcessor:
    """Processador para imagens FLIR radiométricas."""

    def __init__(self):
        """Inicializa o processador FLIR."""
        # Parâmetros padrão
        self.default_emissivity = 0.98  # Emissividade da pele humana
        self.default_distance = 1.0  # Distância padrão em metros

    def load_flir_image(self, image_path: str) -> Dict[str, Any]:
        """
        Carrega uma imagem FLIR e extrai dados térmicos.

        Args:
            image_path: Caminho para o arquivo FLIR .jpg

        Returns:
            Dicionário com dados da imagem e metadados
        """
        try:
            path = Path(image_path)
            if not path.exists():
                raise FLIRProcessorError(f"Arquivo não encontrado: {image_path}")

            # Carrega a imagem
            img = cv2.imread(str(path))
            if img is None:
                raise FLIRProcessorError(f"Não foi possível carregar a imagem: {image_path}")

            # Extrai metadados EXIF
            metadata = self._extract_exif_metadata(path)

            # Extrai dados térmicos brutos (se disponível)
            thermal_data = self._extract_thermal_data(path)

            # Se não conseguiu extrair dados térmicos, usa a imagem visível como fallback
            if thermal_data is None:
                logger.warning("Dados térmicos não encontrados, usando imagem visível como aproximação")
                thermal_data = self._estimate_thermal_from_visible(img)

            # Calcula estatísticas
            stats = self._calculate_statistics(thermal_data)

            return {
                'image_path': str(path),
                'visible_image': img,
                'thermal_data': thermal_data,
                'metadata': metadata,
                'statistics': stats,
                'resolution': (img.shape[1], img.shape[0])  # (width, height)
            }

        except Exception as e:
            logger.error(f"Erro ao carregar imagem FLIR: {e}")
            raise FLIRProcessorError(f"Erro ao carregar imagem FLIR: {e}")

    def _extract_exif_metadata(self, image_path: Path) -> Dict[str, Any]:
        """
        Extrai metadados EXIF da imagem FLIR.

        Args:
            image_path: Caminho para a imagem

        Returns:
            Dicionário com metadados
        """
        metadata = {
            'camera_model': 'Unknown',
            'emissivity': self.default_emissivity,
            'ambient_temp': 23.0,  # Temperatura ambiente padrão
            'distance': self.default_distance,
            'humidity': None
        }

        try:
            with Image.open(image_path) as img:
                exif_data = img._getexif()
                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag == 'Model':
                            metadata['camera_model'] = value
                        elif tag == 'Make':
                            metadata['camera_make'] = value

        except Exception as e:
            logger.warning(f"Não foi possível extrair EXIF: {e}")

        return metadata

    def _extract_thermal_data(self, image_path: Path) -> Optional[np.ndarray]:
        """
        Extrai dados térmicos reais da imagem FLIR usando flirimageextractor.

        Args:
            image_path: Caminho para a imagem

        Returns:
            Array numpy com temperaturas em °C ou None se não encontrado
        """
        if not FLIR_EXTRACTOR_AVAILABLE:
            logger.warning("flirimageextractor não está instalada - não é possível extrair dados térmicos reais")
            return None

        try:
            logger.info(f"Extraindo dados térmicos FLIR de: {image_path.name}")

            # Cria extrator FLIR
            flir = FlirImageExtractor()

            # Processa a imagem
            flir.process_image(str(image_path))

            # Extrai dados térmicos em Celsius
            thermal_np = flir.get_thermal_np()

            if thermal_np is not None:
                logger.info(f"✅ Dados térmicos extraídos com sucesso!")
                logger.info(f"   Shape: {thermal_np.shape}, dtype: {thermal_np.dtype}")
                logger.info(f"   Temperatura min: {np.min(thermal_np):.2f}°C")
                logger.info(f"   Temperatura max: {np.max(thermal_np):.2f}°C")
                logger.info(f"   Temperatura média: {np.mean(thermal_np):.2f}°C")

                return thermal_np.astype(np.float32)
            else:
                logger.warning("flirimageextractor não conseguiu extrair dados térmicos (retornou None)")
                return None

        except Exception as e:
            logger.error(f"Erro ao extrair dados térmicos com flirimageextractor: {e}", exc_info=True)
            return None

    def _estimate_thermal_from_visible(self, img: np.ndarray) -> np.ndarray:
        """
        Estima dados térmicos a partir da imagem visível (fallback).
        Usa a intensidade da imagem como proxy para temperatura.

        Args:
            img: Imagem BGR do OpenCV

        Returns:
            Array numpy com temperaturas estimadas em °C
        """
        # Converte para grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Normaliza para faixa de temperatura típica de termografia médica (28-38°C)
        min_temp = 28.0
        max_temp = 38.0

        # Converte valores de pixel (0-255) para temperatura
        thermal_data = (gray / 255.0) * (max_temp - min_temp) + min_temp

        return thermal_data.astype(np.float32)

    def _calculate_statistics(self, thermal_data: np.ndarray) -> Dict[str, float]:
        """
        Calcula estatísticas dos dados térmicos.

        Args:
            thermal_data: Array com temperaturas

        Returns:
            Dicionário com estatísticas
        """
        return {
            'min_temp': float(np.min(thermal_data)),
            'max_temp': float(np.max(thermal_data)),
            'mean_temp': float(np.mean(thermal_data)),
            'median_temp': float(np.median(thermal_data)),
            'std_temp': float(np.std(thermal_data))
        }

    def generate_heatmap(self, thermal_data: np.ndarray,
                        colormap: int = cv2.COLORMAP_JET,
                        min_temp: Optional[float] = None,
                        max_temp: Optional[float] = None) -> np.ndarray:
        """
        Gera heatmap colorido a partir de dados térmicos.

        Args:
            thermal_data: Array com temperaturas em °C
            colormap: Colormap do OpenCV (padrão: COLORMAP_JET)
            min_temp: Temperatura mínima para escala (None = auto)
            max_temp: Temperatura máxima para escala (None = auto)

        Returns:
            Imagem BGR com heatmap
        """
        # Define limites da escala
        if min_temp is None:
            min_temp = np.min(thermal_data)
        if max_temp is None:
            max_temp = np.max(thermal_data)

        # Normaliza para 0-255
        normalized = ((thermal_data - min_temp) / (max_temp - min_temp) * 255)
        normalized = np.clip(normalized, 0, 255).astype(np.uint8)

        # Aplica colormap
        heatmap = cv2.applyColorMap(normalized, colormap)

        return heatmap

    def extract_roi_temperatures(self, thermal_data: np.ndarray,
                                 roi_mask: np.ndarray) -> Dict[str, float]:
        """
        Extrai estatísticas de temperatura de uma ROI.

        Args:
            thermal_data: Array com temperaturas
            roi_mask: Máscara binária da ROI (mesma dimensão que thermal_data)

        Returns:
            Dicionário com estatísticas da ROI
        """
        # Extrai temperaturas da ROI
        roi_temps = thermal_data[roi_mask > 0]

        if len(roi_temps) == 0:
            return {
                'min_temp': 0.0,
                'max_temp': 0.0,
                'mean_temp': 0.0,
                'median_temp': 0.0,
                'std_temp': 0.0,
                'pixel_count': 0
            }

        return {
            'min_temp': float(np.min(roi_temps)),
            'max_temp': float(np.max(roi_temps)),
            'mean_temp': float(np.mean(roi_temps)),
            'median_temp': float(np.median(roi_temps)),
            'std_temp': float(np.std(roi_temps)),
            'pixel_count': len(roi_temps)
        }

    def create_roi_mask(self, image_shape: Tuple[int, int],
                       coordinates: list) -> np.ndarray:
        """
        Cria máscara de ROI a partir de coordenadas de polígono.

        Args:
            image_shape: (height, width) da imagem
            coordinates: Lista de tuplas (x, y) definindo o polígono

        Returns:
            Máscara binária (0 ou 255)
        """
        mask = np.zeros(image_shape, dtype=np.uint8)

        # Converte coordenadas para array numpy
        pts = np.array(coordinates, dtype=np.int32)

        # Desenha polígono preenchido
        cv2.fillPoly(mask, [pts], 255)

        return mask

    def draw_roi_on_image(self, image: np.ndarray, coordinates: list,
                         color: Tuple[int, int, int] = (0, 255, 0),
                         thickness: int = 2) -> np.ndarray:
        """
        Desenha ROI sobre a imagem.

        Args:
            image: Imagem BGR
            coordinates: Lista de tuplas (x, y)
            color: Cor BGR
            thickness: Espessura da linha

        Returns:
            Imagem com ROI desenhada
        """
        img_copy = image.copy()
        pts = np.array(coordinates, dtype=np.int32)
        cv2.polylines(img_copy, [pts], True, color, thickness)
        return img_copy

    def add_temperature_overlay(self, heatmap: np.ndarray,
                               thermal_data: np.ndarray,
                               show_min_max: bool = True) -> np.ndarray:
        """
        Adiciona overlay com informações de temperatura no heatmap.

        Args:
            heatmap: Imagem heatmap
            thermal_data: Dados térmicos
            show_min_max: Se True, mostra min/max na imagem

        Returns:
            Heatmap com overlay
        """
        result = heatmap.copy()

        if show_min_max:
            # Encontra posição de min e max
            min_pos = np.unravel_index(np.argmin(thermal_data), thermal_data.shape)
            max_pos = np.unravel_index(np.argmax(thermal_data), thermal_data.shape)

            min_temp = thermal_data[min_pos]
            max_temp = thermal_data[max_pos]

            # Desenha círculos
            cv2.circle(result, (min_pos[1], min_pos[0]), 10, (255, 0, 0), 2)
            cv2.circle(result, (max_pos[1], max_pos[0]), 10, (0, 0, 255), 2)

            # Adiciona texto
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(result, f"Min: {min_temp:.1f}C",
                       (min_pos[1] + 15, min_pos[0]), font, 0.5, (255, 255, 255), 1)
            cv2.putText(result, f"Max: {max_temp:.1f}C",
                       (max_pos[1] + 15, max_pos[0]), font, 0.5, (255, 255, 255), 1)

        return result

    def save_heatmap(self, heatmap: np.ndarray, output_path: str) -> None:
        """
        Salva heatmap em arquivo.

        Args:
            heatmap: Imagem heatmap
            output_path: Caminho de saída
        """
        try:
            cv2.imwrite(output_path, heatmap)
            logger.info(f"Heatmap salvo em: {output_path}")
        except Exception as e:
            raise FLIRProcessorError(f"Erro ao salvar heatmap: {e}")


class FLIRProcessorError(Exception):
    """Exceção para erros do processador FLIR."""
    pass


if __name__ == '__main__':
    # Teste básico
    print("=== Teste do FLIRProcessor ===\n")

    processor = FLIRProcessor()

    # Cria imagem de teste sintética
    test_thermal = np.random.rand(480, 640) * 10 + 30  # 30-40°C
    print(f"Dados térmicos de teste: {test_thermal.shape}")

    # Gera heatmap
    heatmap = processor.generate_heatmap(test_thermal)
    print(f"Heatmap gerado: {heatmap.shape}")

    # Cria ROI de teste
    roi_coords = [(100, 100), (200, 100), (200, 200), (100, 200)]
    roi_mask = processor.create_roi_mask(test_thermal.shape, roi_coords)
    print(f"ROI mask criada: {roi_mask.shape}")

    # Extrai estatísticas da ROI
    roi_stats = processor.extract_roi_temperatures(test_thermal, roi_mask)
    print(f"Estatísticas ROI: {roi_stats}")

    print("\nTeste concluído!")
