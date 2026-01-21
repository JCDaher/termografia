"""
Sistema de validação de medições termográficas usando dados FLIR como referência.

Compara cálculos do sistema com medições FLIR Thermal Studio para:
- Validar precisão das medições
- Identificar discrepâncias
- Gerar relatórios de validação
- Enriquecer prompts do Claude AI com dados de referência
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
import logging

from core.flir_html_parser import FLIRExportData, FLIRMeasurement
from core.anatomical_template import MultiPointAnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Resultado da validação de uma ROI individual."""
    roi_name: str
    flir_temp: float  # Temperatura média do FLIR
    system_temp: float  # Temperatura do sistema
    difference: float  # Diferença absoluta
    relative_error: float  # Erro relativo em %
    status: str  # "ok", "warning", "error"
    flir_range: Tuple[float, float]  # (min, max) do FLIR

    def is_within_tolerance(self, tolerance: float = 0.5) -> bool:
        """Verifica se está dentro da tolerância."""
        return abs(self.difference) <= tolerance

    def __str__(self):
        return (
            f"{self.roi_name}: FLIR={self.flir_temp:.2f}°C, "
            f"Sistema={self.system_temp:.2f}°C, "
            f"Diff={self.difference:+.2f}°C ({self.relative_error:+.1f}%) - {self.status.upper()}"
        )


@dataclass
class ValidationReport:
    """Relatório completo de validação."""
    validations: List[ValidationResult]
    total_rois: int
    matched_rois: int
    unmatched_flir: List[str]  # ROIs no FLIR mas não no sistema
    unmatched_system: List[str]  # ROIs no sistema mas não no FLIR
    statistics: Dict[str, float] = field(default_factory=dict)

    def get_accuracy_percentage(self) -> float:
        """Retorna % de ROIs dentro da tolerância."""
        if not self.validations:
            return 0.0
        ok_count = sum(1 for v in self.validations if v.status == "ok")
        return (ok_count / len(self.validations)) * 100

    def get_status_counts(self) -> Dict[str, int]:
        """Retorna contagem por status."""
        counts = {"ok": 0, "warning": 0, "error": 0}
        for v in self.validations:
            counts[v.status] = counts.get(v.status, 0) + 1
        return counts

    def __str__(self):
        status_counts = self.get_status_counts()
        return (
            f"Validation Report: {len(self.validations)} ROIs validated, "
            f"{status_counts['ok']} OK, {status_counts['warning']} warnings, "
            f"{status_counts['error']} errors "
            f"({self.get_accuracy_percentage():.1f}% accuracy)"
        )


class FLIRValidator:
    """
    Validador de medições usando FLIR como referência.
    """

    def __init__(
        self,
        tolerance_ok: float = 0.5,
        tolerance_warning: float = 1.0
    ):
        """
        Inicializa o validador.

        Args:
            tolerance_ok: Diferença máxima para considerar OK (°C)
            tolerance_warning: Diferença máxima para warning (acima disso = error)
        """
        self.tolerance_ok = tolerance_ok
        self.tolerance_warning = tolerance_warning

    def validate(
        self,
        flir_data: FLIRExportData,
        system_temperatures: Dict[str, float],
        fuzzy_match: bool = True
    ) -> ValidationReport:
        """
        Valida medições do sistema contra dados FLIR.

        Args:
            flir_data: Dados extraídos do FLIR
            system_temperatures: Temperaturas do sistema {roi_name: temp}
            fuzzy_match: Se True, tenta matching parcial de nomes

        Returns:
            ValidationReport com resultados
        """
        logger.info("Iniciando validação FLIR vs Sistema")
        logger.info(f"  FLIR: {len(flir_data.get_all_measurements())} medições")
        logger.info(f"  Sistema: {len(system_temperatures)} medições")

        validations = []
        unmatched_flir = []
        unmatched_system = list(system_temperatures.keys())

        # Processa cada medição FLIR
        for measurement in flir_data.get_all_measurements():
            roi_name = measurement.roi_name
            flir_temp = measurement.mean_temp

            # Tenta encontrar correspondência no sistema
            system_temp = None

            # Matching exato
            if roi_name in system_temperatures:
                system_temp = system_temperatures[roi_name]
                if roi_name in unmatched_system:
                    unmatched_system.remove(roi_name)

            # Fuzzy matching se não encontrou
            elif fuzzy_match:
                system_temp, matched_name = self._fuzzy_match(
                    roi_name,
                    system_temperatures
                )
                if matched_name and matched_name in unmatched_system:
                    unmatched_system.remove(matched_name)

            # Cria resultado de validação
            if system_temp is not None:
                result = self._create_validation_result(
                    roi_name,
                    measurement,
                    system_temp
                )
                validations.append(result)
                logger.info(f"  ✓ {result}")
            else:
                unmatched_flir.append(roi_name)
                logger.warning(f"  ✗ ROI não encontrada no sistema: {roi_name}")

        # Calcula estatísticas
        statistics = self._calculate_statistics(validations)

        report = ValidationReport(
            validations=validations,
            total_rois=len(flir_data.get_all_measurements()),
            matched_rois=len(validations),
            unmatched_flir=unmatched_flir,
            unmatched_system=unmatched_system,
            statistics=statistics
        )

        logger.info(f"\n{report}")
        return report

    def _create_validation_result(
        self,
        roi_name: str,
        flir_measurement: FLIRMeasurement,
        system_temp: float
    ) -> ValidationResult:
        """
        Cria resultado de validação para uma ROI.

        Args:
            roi_name: Nome da ROI
            flir_measurement: Medição FLIR completa
            system_temp: Temperatura do sistema

        Returns:
            ValidationResult
        """
        flir_temp = flir_measurement.mean_temp
        difference = system_temp - flir_temp

        # Calcula erro relativo
        if flir_temp != 0:
            relative_error = (difference / flir_temp) * 100
        else:
            relative_error = 0.0

        # Determina status
        abs_diff = abs(difference)
        if abs_diff <= self.tolerance_ok:
            status = "ok"
        elif abs_diff <= self.tolerance_warning:
            status = "warning"
        else:
            status = "error"

        return ValidationResult(
            roi_name=roi_name,
            flir_temp=flir_temp,
            system_temp=system_temp,
            difference=difference,
            relative_error=relative_error,
            status=status,
            flir_range=(flir_measurement.min_temp, flir_measurement.max_temp)
        )

    def _fuzzy_match(
        self,
        target_name: str,
        candidates: Dict[str, float]
    ) -> Tuple[Optional[float], Optional[str]]:
        """
        Tenta matching parcial de nomes de ROI.

        Útil quando nomes não são exatamente iguais mas similares.
        Ex: "Joelho Dir" vs "Joelho Direito"

        Args:
            target_name: Nome procurado
            candidates: Dicionário de candidatos

        Returns:
            (temperatura, nome_correspondente) ou (None, None)
        """
        target_lower = target_name.lower().strip()

        for candidate_name, temp in candidates.items():
            candidate_lower = candidate_name.lower().strip()

            # Verifica se um contém o outro
            if target_lower in candidate_lower or candidate_lower in target_lower:
                logger.info(f"    Fuzzy match: '{target_name}' <-> '{candidate_name}'")
                return temp, candidate_name

        return None, None

    def _calculate_statistics(
        self,
        validations: List[ValidationResult]
    ) -> Dict[str, float]:
        """
        Calcula estatísticas da validação.

        Args:
            validations: Lista de resultados

        Returns:
            Dicionário com estatísticas
        """
        if not validations:
            return {}

        differences = [v.difference for v in validations]
        abs_differences = [abs(d) for d in differences]
        relative_errors = [v.relative_error for v in validations]

        import numpy as np

        stats = {
            'mean_difference': float(np.mean(differences)),
            'mean_abs_difference': float(np.mean(abs_differences)),
            'max_abs_difference': float(np.max(abs_differences)),
            'min_abs_difference': float(np.min(abs_differences)),
            'std_difference': float(np.std(differences)),
            'mean_relative_error': float(np.mean([abs(e) for e in relative_errors])),
            'max_relative_error': float(np.max([abs(e) for e in relative_errors])),
        }

        return stats

    def generate_text_report(self, report: ValidationReport) -> str:
        """
        Gera relatório textual detalhado.

        Args:
            report: Relatório de validação

        Returns:
            String com relatório formatado
        """
        lines = []
        lines.append("=" * 80)
        lines.append("RELATÓRIO DE VALIDAÇÃO: FLIR vs Sistema")
        lines.append("=" * 80)
        lines.append("")

        # Resumo
        lines.append("RESUMO:")
        lines.append("-" * 80)
        lines.append(f"Total de ROIs no FLIR: {report.total_rois}")
        lines.append(f"ROIs correspondentes: {report.matched_rois}")
        lines.append(f"Precisão: {report.get_accuracy_percentage():.1f}%")

        status_counts = report.get_status_counts()
        lines.append(f"\nStatus:")
        lines.append(f"  ✅ OK: {status_counts['ok']}")
        lines.append(f"  ⚠️  Warning: {status_counts['warning']}")
        lines.append(f"  ❌ Error: {status_counts['error']}")

        # Estatísticas
        if report.statistics:
            lines.append("\n" + "=" * 80)
            lines.append("ESTATÍSTICAS:")
            lines.append("-" * 80)
            stats = report.statistics
            lines.append(f"Diferença média: {stats['mean_difference']:+.3f}°C")
            lines.append(f"Diferença média (abs): {stats['mean_abs_difference']:.3f}°C")
            lines.append(f"Diferença máxima: {stats['max_abs_difference']:.3f}°C")
            lines.append(f"Diferença mínima: {stats['min_abs_difference']:.3f}°C")
            lines.append(f"Desvio padrão: {stats['std_difference']:.3f}°C")
            lines.append(f"Erro relativo médio: {stats['mean_relative_error']:.2f}%")
            lines.append(f"Erro relativo máximo: {stats['max_relative_error']:.2f}%")

        # Detalhes por ROI
        lines.append("\n" + "=" * 80)
        lines.append("VALIDAÇÃO DETALHADA:")
        lines.append("-" * 80)
        lines.append(
            f"{'ROI Name':<35} {'FLIR':<10} {'Sistema':<10} {'Diff':<10} {'Status'}"
        )
        lines.append("-" * 80)

        # Ordena por diferença absoluta (maiores primeiro)
        sorted_validations = sorted(
            report.validations,
            key=lambda v: abs(v.difference),
            reverse=True
        )

        for v in sorted_validations:
            status_symbol = {
                "ok": "✅",
                "warning": "⚠️ ",
                "error": "❌"
            }.get(v.status, "?")

            lines.append(
                f"{v.roi_name:<35} "
                f"{v.flir_temp:>6.2f}°C  "
                f"{v.system_temp:>6.2f}°C  "
                f"{v.difference:>+6.2f}°C  "
                f"{status_symbol} {v.status.upper()}"
            )

        # ROIs não correspondentes
        if report.unmatched_flir:
            lines.append("\n" + "=" * 80)
            lines.append("ROIS NO FLIR MAS NÃO NO SISTEMA:")
            lines.append("-" * 80)
            for roi in report.unmatched_flir:
                lines.append(f"  ❓ {roi}")

        if report.unmatched_system:
            lines.append("\n" + "=" * 80)
            lines.append("ROIS NO SISTEMA MAS NÃO NO FLIR:")
            lines.append("-" * 80)
            for roi in report.unmatched_system:
                lines.append(f"  ❓ {roi}")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)

    def generate_prompt_supplement(
        self,
        report: ValidationReport,
        flir_data: FLIRExportData
    ) -> str:
        """
        Gera texto suplementar para enriquecer prompt do Claude AI.

        Args:
            report: Relatório de validação
            flir_data: Dados FLIR completos

        Returns:
            String para adicionar ao prompt
        """
        lines = []
        lines.append("## DADOS DE REFERÊNCIA FLIR THERMAL STUDIO")
        lines.append("")
        lines.append(
            "As seguintes medições foram obtidas do FLIR Thermal Studio "
            "como referência de precisão:"
        )
        lines.append("")

        # Agrupa medições por imagem
        for image in flir_data.images:
            lines.append(f"### Imagem: {image.filename}")
            lines.append("")

            for measurement in image.measurements:
                # Busca validação correspondente
                validation = next(
                    (v for v in report.validations if v.roi_name == measurement.roi_name),
                    None
                )

                if validation:
                    lines.append(
                        f"- **{measurement.roi_name}**: "
                        f"FLIR Mean={measurement.mean_temp:.2f}°C "
                        f"(Range: {measurement.min_temp:.2f}-{measurement.max_temp:.2f}°C), "
                        f"Sistema={validation.system_temp:.2f}°C, "
                        f"Diferença={validation.difference:+.2f}°C"
                    )
                else:
                    lines.append(
                        f"- **{measurement.roi_name}**: "
                        f"FLIR Mean={measurement.mean_temp:.2f}°C "
                        f"(Range: {measurement.min_temp:.2f}-{measurement.max_temp:.2f}°C) "
                        f"[Não encontrada no sistema]"
                    )

            lines.append("")

        # Adiciona observações sobre validação
        lines.append("### Validação")
        lines.append("")
        lines.append(f"- Precisão geral: {report.get_accuracy_percentage():.1f}%")

        if report.statistics:
            stats = report.statistics
            lines.append(
                f"- Diferença média: {stats['mean_abs_difference']:.2f}°C "
                f"(máx: {stats['max_abs_difference']:.2f}°C)"
            )

        lines.append("")
        lines.append(
            "Por favor, considere esses dados de referência FLIR ao gerar o laudo, "
            "especialmente se houver discrepâncias significativas."
        )

        return "\n".join(lines)


def validate_analysis(
    flir_data: FLIRExportData,
    analysis_result: MultiPointAnalysisResult,
    tolerance_ok: float = 0.5,
    tolerance_warning: float = 1.0
) -> ValidationReport:
    """
    Função helper para validar resultado de análise contra dados FLIR.

    Args:
        flir_data: Dados FLIR
        analysis_result: Resultado da análise multi-ponto
        tolerance_ok: Tolerância OK (°C)
        tolerance_warning: Tolerância warning (°C)

    Returns:
        ValidationReport
    """
    validator = FLIRValidator(tolerance_ok, tolerance_warning)
    return validator.validate(flir_data, analysis_result.roi_temperatures)


if __name__ == "__main__":
    # Teste básico
    print("FLIRValidator module loaded successfully")
    print("Use: from core.flir_validator import FLIRValidator, validate_analysis")
