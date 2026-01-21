"""
Modelo de dados para templates anatômicos com múltiplas ROIs.
Permite criar documentos com várias regiões de interesse identificadas anatomicamente.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import json
from pathlib import Path


@dataclass
class AnatomicalROI:
    """
    Representa uma ROI (Region of Interest) com localização anatômica específica.
    """
    name: str  # Ex: "Joelho direito", "C5 esquerdo", "Tender point occipital"
    anatomical_location: str  # Descrição anatômica detalhada
    coordinates: List[Tuple[int, int]]  # Pontos do polígono
    region_type: str  # "dermatome", "tender_point", "joint", "extremity", "custom"
    expected_temp_range: Optional[Tuple[float, float]] = None  # Faixa esperada (min, max)
    notes: str = ""  # Observações específicas

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return {
            'name': self.name,
            'anatomical_location': self.anatomical_location,
            'coordinates': self.coordinates,
            'region_type': self.region_type,
            'expected_temp_range': self.expected_temp_range,
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnatomicalROI':
        """Desserializa de dicionário."""
        return cls(
            name=data['name'],
            anatomical_location=data['anatomical_location'],
            coordinates=data['coordinates'],
            region_type=data['region_type'],
            expected_temp_range=data.get('expected_temp_range'),
            notes=data.get('notes', '')
        )


@dataclass
class AnatomicalTemplate:
    """
    Template anatômico completo com múltiplas ROIs.
    Representa um documento/protocolo de análise termográfica.
    """
    template_id: Optional[int] = None
    name: str = ""  # Ex: "Protocolo Fibromialgia - 18 Tender Points"
    description: str = ""  # Descrição do template
    category: str = "custom"  # "fibromyalgia", "dermatomes", "joints", "custom"
    reference_image_path: Optional[str] = None  # Imagem de referência
    rois: List[AnatomicalROI] = field(default_factory=list)
    comparison_groups: List[List[str]] = field(default_factory=list)  # Grupos para comparação
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_date: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_roi(self, roi: AnatomicalROI) -> None:
        """Adiciona uma ROI ao template."""
        self.rois.append(roi)
        self.modified_date = datetime.now().isoformat()

    def remove_roi(self, roi_name: str) -> bool:
        """Remove uma ROI pelo nome."""
        for i, roi in enumerate(self.rois):
            if roi.name == roi_name:
                del self.rois[i]
                self.modified_date = datetime.now().isoformat()
                return True
        return False

    def get_roi_by_name(self, name: str) -> Optional[AnatomicalROI]:
        """Busca ROI pelo nome."""
        for roi in self.rois:
            if roi.name == name:
                return roi
        return None

    def add_comparison_group(self, roi_names: List[str]) -> None:
        """
        Adiciona grupo de ROIs para comparação.
        Ex: ["C5 esquerdo", "C5 direito"] para comparar lateralidade
        Ex: ["C5 esquerdo", "C6 esquerdo", "C7 esquerdo"] para comparar dermátomos
        """
        self.comparison_groups.append(roi_names)
        self.modified_date = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'reference_image_path': self.reference_image_path,
            'rois': [roi.to_dict() for roi in self.rois],
            'comparison_groups': self.comparison_groups,
            'created_date': self.created_date,
            'modified_date': self.modified_date,
            'metadata': self.metadata
        }

    def to_json(self) -> str:
        """Serializa para JSON."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnatomicalTemplate':
        """Desserializa de dicionário."""
        template = cls(
            template_id=data.get('template_id'),
            name=data['name'],
            description=data.get('description', ''),
            category=data.get('category', 'custom'),
            reference_image_path=data.get('reference_image_path'),
            comparison_groups=data.get('comparison_groups', []),
            created_date=data.get('created_date', datetime.now().isoformat()),
            modified_date=data.get('modified_date', datetime.now().isoformat()),
            metadata=data.get('metadata', {})
        )

        # Reconstrói ROIs
        for roi_data in data.get('rois', []):
            template.add_roi(AnatomicalROI.from_dict(roi_data))

        return template

    @classmethod
    def from_json(cls, json_str: str) -> 'AnatomicalTemplate':
        """Desserializa de JSON."""
        return cls.from_dict(json.loads(json_str))

    def save_to_file(self, filepath: Path) -> None:
        """Salva template em arquivo JSON."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())

    @classmethod
    def load_from_file(cls, filepath: Path) -> 'AnatomicalTemplate':
        """Carrega template de arquivo JSON."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return cls.from_json(f.read())


@dataclass
class MultiPointAnalysisResult:
    """
    Resultado da análise multi-ponto.
    Contém temperaturas de todos os pontos e matriz de comparações.
    """
    template_name: str
    image_name: str
    roi_temperatures: Dict[str, float]  # {nome_roi: temperatura}
    roi_pixel_counts: Dict[str, int]  # {nome_roi: número de pixels}
    comparison_matrix: Dict[str, Dict[str, float]]  # {roi1: {roi2: delta_t}}
    group_comparisons: List[Dict[str, Any]]  # Resultados por grupo de comparação
    overall_stats: Dict[str, float]  # Estatísticas gerais
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def get_delta_t(self, roi1: str, roi2: str) -> Optional[float]:
        """Obtém delta T entre duas ROIs."""
        if roi1 in self.comparison_matrix and roi2 in self.comparison_matrix[roi1]:
            return self.comparison_matrix[roi1][roi2]
        return None

    def get_max_delta_t(self) -> Tuple[str, str, float]:
        """Retorna o par de ROIs com maior delta T."""
        max_delta = 0.0
        max_pair = ("", "")

        for roi1, comparisons in self.comparison_matrix.items():
            for roi2, delta in comparisons.items():
                if abs(delta) > max_delta:
                    max_delta = abs(delta)
                    max_pair = (roi1, roi2)

        return max_pair[0], max_pair[1], max_delta

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return {
            'template_name': self.template_name,
            'image_name': self.image_name,
            'roi_temperatures': self.roi_temperatures,
            'roi_pixel_counts': self.roi_pixel_counts,
            'comparison_matrix': self.comparison_matrix,
            'group_comparisons': self.group_comparisons,
            'overall_stats': self.overall_stats,
            'timestamp': self.timestamp
        }


def create_fibromyalgia_18_points_template() -> AnatomicalTemplate:
    """
    Cria template com os 18 tender points clássicos da fibromialgia (critérios ACR 1990).
    """
    template = AnatomicalTemplate(
        name="Fibromialgia - 18 Tender Points (ACR 1990)",
        description="Template com os 18 tender points clássicos para avaliação de fibromialgia conforme critérios do ACR 1990",
        category="fibromyalgia"
    )

    # Lista dos 18 tender points (bilateral = 9 pares)
    tender_points = [
        # Occipital (bilateral)
        ("Occipital Esquerdo", "Inserção do músculo suboccipital esquerdo"),
        ("Occipital Direito", "Inserção do músculo suboccipital direito"),

        # Cervical baixo (bilateral)
        ("Cervical Baixo Esquerdo", "Aspectos anteriores dos espaços intertransversos C5-C7 esquerdo"),
        ("Cervical Baixo Direito", "Aspectos anteriores dos espaços intertransversos C5-C7 direito"),

        # Trapézio (bilateral)
        ("Trapézio Esquerdo", "Ponto médio da borda superior do músculo trapézio esquerdo"),
        ("Trapézio Direito", "Ponto médio da borda superior do músculo trapézio direito"),

        # Supraespinal (bilateral)
        ("Supraespinal Esquerdo", "Origem do músculo supraespinal acima da espinha da escápula esquerda"),
        ("Supraespinal Direito", "Origem do músculo supraespinal acima da espinha da escápula direita"),

        # Segunda costela (bilateral)
        ("Segunda Costela Esquerda", "Segunda junção costocondral esquerda"),
        ("Segunda Costela Direita", "Segunda junção costocondral direita"),

        # Epicôndilo lateral (bilateral)
        ("Epicôndilo Lateral Esquerdo", "2cm distal ao epicôndilo lateral do cotovelo esquerdo"),
        ("Epicôndilo Lateral Direito", "2cm distal ao epicôndilo lateral do cotovelo direito"),

        # Glúteo (bilateral)
        ("Glúteo Esquerdo", "Quadrante superior externo da nádega esquerda"),
        ("Glúteo Direito", "Quadrante superior externo da nádega direita"),

        # Trocanter maior (bilateral)
        ("Trocanter Maior Esquerdo", "Posterior à proeminência trocantérica esquerda"),
        ("Trocanter Maior Direito", "Posterior à proeminência trocantérica direita"),

        # Joelho (bilateral)
        ("Joelho Esquerdo", "Almofada de gordura medial proximal à linha articular do joelho esquerdo"),
        ("Joelho Direito", "Almofada de gordura medial proximal à linha articular do joelho direito"),
    ]

    # Adiciona cada tender point como ROI
    # Nota: Coordenadas serão definidas pelo usuário ao desenhar
    for name, location in tender_points:
        roi = AnatomicalROI(
            name=name,
            anatomical_location=location,
            coordinates=[],  # Será preenchido ao desenhar
            region_type="tender_point",
            notes="Tender point clássico ACR 1990"
        )
        template.add_roi(roi)

    # Adiciona grupos de comparação (pares bilaterais)
    comparison_pairs = [
        ["Occipital Esquerdo", "Occipital Direito"],
        ["Cervical Baixo Esquerdo", "Cervical Baixo Direito"],
        ["Trapézio Esquerdo", "Trapézio Direito"],
        ["Supraespinal Esquerdo", "Supraespinal Direito"],
        ["Segunda Costela Esquerda", "Segunda Costela Direita"],
        ["Epicôndilo Lateral Esquerdo", "Epicôndilo Lateral Direito"],
        ["Glúteo Esquerdo", "Glúteo Direito"],
        ["Trocanter Maior Esquerdo", "Trocanter Maior Direito"],
        ["Joelho Esquerdo", "Joelho Direito"],
    ]

    for pair in comparison_pairs:
        template.add_comparison_group(pair)

    return template


if __name__ == "__main__":
    # Teste: criar template de fibromialgia
    template = create_fibromyalgia_18_points_template()

    print("=== Template Criado ===")
    print(f"Nome: {template.name}")
    print(f"Categoria: {template.category}")
    print(f"Total de ROIs: {len(template.rois)}")
    print(f"Grupos de comparação: {len(template.comparison_groups)}")

    print("\nROIs:")
    for roi in template.rois:
        print(f"  - {roi.name}: {roi.anatomical_location}")

    # Salva em arquivo
    template.save_to_file(Path("template_fibromyalgia_18points.json"))
    print("\n✓ Template salvo em: template_fibromyalgia_18points.json")
