"""
Parser para extrair medições de ROIs de arquivos HTML exportados do FLIR Thermal Studio.

Permite importar dados de referência do FLIR para:
- Validar cálculos do sistema
- Enriquecer prompts do Claude AI
- Criar templates anatômicos a partir de medições FLIR
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from bs4 import BeautifulSoup
import logging
import re

from core.anatomical_template import AnatomicalTemplate, AnatomicalROI

logger = logging.getLogger(__name__)


@dataclass
class FLIRMeasurement:
    """Medição de ROI extraída do FLIR Thermal Studio."""
    roi_name: str
    max_temp: float
    mean_temp: float
    min_temp: float

    def __str__(self):
        return f"{self.roi_name}: Mean={self.mean_temp:.2f}°C (Min={self.min_temp:.2f}, Max={self.max_temp:.2f})"


@dataclass
class FLIRImageData:
    """Dados de uma imagem no export FLIR."""
    filename: str
    measurements: List[FLIRMeasurement]
    file_info: Dict[str, str]  # Informações adicionais (resolução, etc.)

    def __str__(self):
        return f"FLIR Image: {self.filename} ({len(self.measurements)} ROIs)"


@dataclass
class FLIRExportData:
    """Dados completos de um export HTML do FLIR Thermal Studio."""
    images: List[FLIRImageData]
    source_file: str

    def get_all_measurements(self) -> List[FLIRMeasurement]:
        """Retorna todas as medições de todas as imagens."""
        all_measurements = []
        for image in self.images:
            all_measurements.extend(image.measurements)
        return all_measurements

    def get_measurements_by_image(self, filename: str) -> Optional[FLIRImageData]:
        """Busca medições de uma imagem específica."""
        for image in self.images:
            if image.filename == filename:
                return image
        return None

    def __str__(self):
        return f"FLIR Export: {len(self.images)} images, {len(self.get_all_measurements())} total ROIs"


class FLIRHTMLParser:
    """
    Parser para arquivos HTML exportados do FLIR Thermal Studio.

    Extrai:
    - Nome dos arquivos de imagem
    - Medições de ROIs (nome, temperatura máxima, média, mínima)
    - Informações adicionais do arquivo
    """

    def __init__(self):
        """Inicializa o parser."""
        self.soup = None
        self.source_file = ""

    def parse_file(self, html_path: Path) -> FLIRExportData:
        """
        Faz parsing de um arquivo HTML do FLIR.

        Args:
            html_path: Caminho para arquivo HTML

        Returns:
            FLIRExportData com todas as imagens e medições
        """
        logger.info(f"Fazendo parsing de arquivo FLIR: {html_path}")

        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.source_file = str(html_path)

        # Extrai todas as seções (cada seção = uma imagem)
        sections = self.soup.find_all('section')
        logger.info(f"  Encontradas {len(sections)} seções (imagens)")

        images = []
        for section in sections:
            image_data = self._parse_section(section)
            if image_data:
                images.append(image_data)

        result = FLIRExportData(
            images=images,
            source_file=self.source_file
        )

        logger.info(f"✅ Parsing concluído: {result}")
        return result

    def _parse_section(self, section) -> Optional[FLIRImageData]:
        """
        Faz parsing de uma seção (imagem individual).

        Args:
            section: Tag <section> do BeautifulSoup

        Returns:
            FLIRImageData ou None se falhar
        """
        try:
            # Extrai informações do arquivo
            file_info = self._extract_file_info(section)
            filename = file_info.get('File name', 'Unknown')

            # Extrai medições
            measurements = self._extract_measurements(section)

            if not measurements:
                logger.warning(f"  Seção '{filename}': Nenhuma medição encontrada")
                return None

            logger.info(f"  ✅ {filename}: {len(measurements)} ROIs")

            return FLIRImageData(
                filename=filename,
                measurements=measurements,
                file_info=file_info
            )

        except Exception as e:
            logger.error(f"  ❌ Erro ao processar seção: {e}")
            return None

    def _extract_file_info(self, section) -> Dict[str, str]:
        """
        Extrai informações do arquivo da tabela "File information".

        Args:
            section: Tag <section>

        Returns:
            Dicionário com informações (File name, Resolution, etc.)
        """
        file_info = {}

        # Procura tabela com título "File information"
        tables = section.find_all('table')

        for table in tables:
            # Verifica se é a tabela de informações do arquivo
            caption = table.find('caption')
            if caption and 'File information' in caption.get_text():
                rows = table.find_all('tr')

                for row in rows:
                    cells = row.find_all(['th', 'td'])
                    if len(cells) == 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        file_info[key] = value

                break

        return file_info

    def _extract_measurements(self, section) -> List[FLIRMeasurement]:
        """
        Extrai medições da tabela "Measurements".

        Args:
            section: Tag <section>

        Returns:
            Lista de FLIRMeasurement
        """
        measurements = []

        # Procura tabela com título "Measurements"
        tables = section.find_all('table')

        for table in tables:
            caption = table.find('caption')
            if caption and 'Measurements' in caption.get_text():
                # Encontrou tabela de medições
                rows = table.find_all('tr')

                # Primeira linha é header (Name, Max, Mean, Min)
                # Próximas linhas são medições

                for row in rows[1:]:  # Pula header
                    cells = row.find_all('td')

                    if len(cells) >= 4:
                        try:
                            roi_name = cells[0].get_text(strip=True)
                            max_temp = self._parse_temperature(cells[1].get_text(strip=True))
                            mean_temp = self._parse_temperature(cells[2].get_text(strip=True))
                            min_temp = self._parse_temperature(cells[3].get_text(strip=True))

                            if roi_name and max_temp is not None:
                                measurement = FLIRMeasurement(
                                    roi_name=roi_name,
                                    max_temp=max_temp,
                                    mean_temp=mean_temp,
                                    min_temp=min_temp
                                )
                                measurements.append(measurement)

                        except Exception as e:
                            logger.warning(f"    Erro ao processar linha de medição: {e}")
                            continue

                break

        return measurements

    def _parse_temperature(self, temp_str: str) -> Optional[float]:
        """
        Faz parsing de string de temperatura.

        Aceita formatos:
        - "34.5 °C"
        - "34,5 °C"
        - "34.5"

        Args:
            temp_str: String com temperatura

        Returns:
            Temperatura em float ou None se inválido
        """
        try:
            # Remove símbolo de grau e °C
            temp_str = temp_str.replace('°C', '').replace('°', '').strip()

            # Substitui vírgula por ponto
            temp_str = temp_str.replace(',', '.')

            return float(temp_str)

        except (ValueError, AttributeError):
            return None

    def to_anatomical_template(
        self,
        export_data: FLIRExportData,
        template_name: Optional[str] = None,
        category: str = "flir_import"
    ) -> AnatomicalTemplate:
        """
        Converte dados FLIR para AnatomicalTemplate.

        Cria template com uma ROI para cada medição FLIR.
        Coordenadas ficarão vazias (para serem desenhadas depois).

        Args:
            export_data: Dados extraídos do FLIR
            template_name: Nome do template (opcional)
            category: Categoria do template

        Returns:
            AnatomicalTemplate com ROIs
        """
        if template_name is None:
            template_name = f"Import FLIR - {Path(export_data.source_file).stem}"

        template = AnatomicalTemplate(
            name=template_name,
            description=f"Importado de {export_data.source_file}",
            category=category
        )

        # Adiciona metadados
        template.metadata['source'] = 'flir_thermal_studio'
        template.metadata['source_file'] = export_data.source_file
        template.metadata['total_images'] = len(export_data.images)

        # Cria ROI para cada medição
        all_measurements = export_data.get_all_measurements()

        for measurement in all_measurements:
            roi = AnatomicalROI(
                name=measurement.roi_name,
                anatomical_location=f"ROI importada do FLIR: {measurement.roi_name}",
                coordinates=[],  # Será preenchido ao desenhar
                region_type="flir_import",
                expected_temp_range=(measurement.min_temp, measurement.max_temp),
                notes=f"FLIR Reference - Mean: {measurement.mean_temp:.2f}°C, Min: {measurement.min_temp:.2f}°C, Max: {measurement.max_temp:.2f}°C"
            )
            template.add_roi(roi)

        logger.info(f"✅ Template criado com {len(all_measurements)} ROIs")
        return template

    def create_validation_report(
        self,
        flir_data: FLIRExportData,
        system_temperatures: Dict[str, float]
    ) -> str:
        """
        Cria relatório comparando medições FLIR vs Sistema.

        Args:
            flir_data: Dados extraídos do FLIR
            system_temperatures: Temperaturas calculadas pelo sistema {roi_name: temp}

        Returns:
            String com relatório formatado
        """
        lines = []
        lines.append("=" * 80)
        lines.append("RELATÓRIO DE VALIDAÇÃO: FLIR vs Sistema")
        lines.append("=" * 80)
        lines.append("")

        all_measurements = flir_data.get_all_measurements()

        lines.append(f"Total de ROIs no FLIR: {len(all_measurements)}")
        lines.append(f"Total de ROIs no Sistema: {len(system_temperatures)}")
        lines.append("")

        # Comparações
        lines.append("COMPARAÇÕES DETALHADAS:")
        lines.append("-" * 80)
        lines.append(f"{'ROI Name':<30} {'FLIR Mean':<12} {'Sistema':<12} {'Diferença':<12} {'Status'}")
        lines.append("-" * 80)

        matches = 0
        differences = []

        for measurement in all_measurements:
            roi_name = measurement.roi_name
            flir_temp = measurement.mean_temp

            if roi_name in system_temperatures:
                system_temp = system_temperatures[roi_name]
                diff = abs(flir_temp - system_temp)
                differences.append(diff)

                if diff < 0.5:
                    status = "✅ OK"
                    matches += 1
                elif diff < 1.0:
                    status = "⚠️  Leve"
                else:
                    status = "❌ Divergente"

                lines.append(
                    f"{roi_name:<30} {flir_temp:>6.2f}°C    {system_temp:>6.2f}°C    "
                    f"{diff:>6.2f}°C    {status}"
                )
            else:
                lines.append(f"{roi_name:<30} {flir_temp:>6.2f}°C    {'N/A':<12} {'---':<12} ❓ Não encontrada")

        # Estatísticas
        lines.append("")
        lines.append("ESTATÍSTICAS:")
        lines.append("-" * 80)
        lines.append(f"ROIs correspondentes: {matches}/{len(all_measurements)}")

        if differences:
            import numpy as np
            lines.append(f"Diferença média: {np.mean(differences):.2f}°C")
            lines.append(f"Diferença máxima: {np.max(differences):.2f}°C")
            lines.append(f"Diferença mínima: {np.min(differences):.2f}°C")
            lines.append(f"Desvio padrão: {np.std(differences):.2f}°C")

        return "\n".join(lines)


def parse_flir_html(html_path: Path) -> FLIRExportData:
    """
    Função helper para fazer parsing de arquivo HTML FLIR.

    Args:
        html_path: Caminho para arquivo HTML

    Returns:
        FLIRExportData com dados extraídos
    """
    parser = FLIRHTMLParser()
    return parser.parse_file(html_path)


if __name__ == "__main__":
    # Teste básico
    import sys

    if len(sys.argv) > 1:
        html_file = Path(sys.argv[1])

        if html_file.exists():
            parser = FLIRHTMLParser()
            data = parser.parse_file(html_file)

            print("\n" + str(data))
            print("\nMedições extraídas:")
            for image in data.images:
                print(f"\n📷 {image.filename}:")
                for m in image.measurements:
                    print(f"  {m}")

            # Cria template
            template = parser.to_anatomical_template(data)
            print(f"\n✅ Template criado: {template.name}")
            print(f"   {len(template.rois)} ROIs")
        else:
            print(f"❌ Arquivo não encontrado: {html_file}")
    else:
        print("Uso: python flir_html_parser.py <arquivo.html>")
