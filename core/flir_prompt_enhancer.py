"""
Enriquecedor de prompts do Claude AI com dados FLIR de referência.

Quando disponíveis medições FLIR, adiciona ao prompt:
- Medições de referência do FLIR
- Comparação FLIR vs Sistema
- Contexto de validação
"""

from typing import Dict, List, Optional
from pathlib import Path

from core.flir_html_parser import FLIRExportData
from core.flir_validator import FLIRValidator, ValidationReport
from core.anatomical_template import MultiPointAnalysisResult


class FLIRPromptEnhancer:
    """
    Enriquece prompts do Claude AI com dados FLIR quando disponíveis.
    """

    def __init__(self):
        """Inicializa o enhancer."""
        self.validator = FLIRValidator()

    def enhance_professional_report_prompt(
        self,
        base_prompt: str,
        flir_data: Optional[FLIRExportData],
        system_temperatures: Dict[str, float],
        image_name: str
    ) -> str:
        """
        Adiciona dados FLIR ao prompt de geração de laudo profissional.

        Args:
            base_prompt: Prompt base original
            flir_data: Dados FLIR (None se não disponível)
            system_temperatures: Temperaturas calculadas pelo sistema
            image_name: Nome da imagem sendo analisada

        Returns:
            Prompt enriquecido com dados FLIR
        """
        if flir_data is None:
            return base_prompt

        # Valida medições
        validation_report = self.validator.validate(
            flir_data,
            system_temperatures,
            fuzzy_match=True
        )

        # Adiciona seção de referência FLIR ao prompt
        flir_section = self._generate_flir_section(
            flir_data,
            validation_report,
            image_name
        )

        # Insere antes da seção de instruções finais
        enhanced_prompt = base_prompt + "\n\n" + flir_section

        return enhanced_prompt

    def _generate_flir_section(
        self,
        flir_data: FLIRExportData,
        validation_report: ValidationReport,
        image_name: str
    ) -> str:
        """
        Gera seção de dados FLIR para o prompt.

        Args:
            flir_data: Dados FLIR
            validation_report: Resultado da validação
            image_name: Nome da imagem

        Returns:
            Texto formatado para inclusão no prompt
        """
        lines = []

        lines.append("=" * 80)
        lines.append("DADOS DE REFERÊNCIA FLIR THERMAL STUDIO")
        lines.append("=" * 80)
        lines.append("")

        lines.append(
            "As medições abaixo foram obtidas do **FLIR Thermal Studio** (software "
            "profissional de análise termográfica) e servem como **referência de precisão** "
            "para validação dos dados calculados pelo sistema."
        )
        lines.append("")

        # Busca imagem correspondente
        matching_image = self._find_matching_image(flir_data, image_name)

        if matching_image:
            lines.append(f"### Imagem: {matching_image.filename}")
            lines.append("")

            # Tabela de medições FLIR vs Sistema
            lines.append("| ROI | FLIR Mean | FLIR Range | Sistema | Diferença | Status |")
            lines.append("|-----|-----------|------------|---------|-----------|--------|")

            for measurement in matching_image.measurements:
                # Busca validação correspondente
                validation = next(
                    (v for v in validation_report.validations
                     if v.roi_name == measurement.roi_name),
                    None
                )

                if validation:
                    status_symbol = {
                        "ok": "✅",
                        "warning": "⚠️",
                        "error": "❌"
                    }.get(validation.status, "?")

                    lines.append(
                        f"| {measurement.roi_name} | "
                        f"{measurement.mean_temp:.2f}°C | "
                        f"{measurement.min_temp:.2f}-{measurement.max_temp:.2f}°C | "
                        f"{validation.system_temp:.2f}°C | "
                        f"{validation.difference:+.2f}°C | "
                        f"{status_symbol} |"
                    )
                else:
                    lines.append(
                        f"| {measurement.roi_name} | "
                        f"{measurement.mean_temp:.2f}°C | "
                        f"{measurement.min_temp:.2f}-{measurement.max_temp:.2f}°C | "
                        f"N/D | N/D | ❓ |"
                    )

        else:
            # Mostra todas as medições disponíveis
            lines.append("### Todas as medições FLIR disponíveis:")
            lines.append("")

            for image in flir_data.images:
                lines.append(f"**{image.filename}**:")
                for measurement in image.measurements:
                    lines.append(
                        f"- {measurement.roi_name}: Mean={measurement.mean_temp:.2f}°C "
                        f"(Range: {measurement.min_temp:.2f}-{measurement.max_temp:.2f}°C)"
                    )
                lines.append("")

        # Resumo da validação
        lines.append("")
        lines.append("### Validação")
        lines.append("")
        lines.append(f"- **Precisão geral**: {validation_report.get_accuracy_percentage():.1f}%")
        lines.append(f"- **ROIs correspondentes**: {validation_report.matched_rois}/{validation_report.total_rois}")

        if validation_report.statistics:
            stats = validation_report.statistics
            lines.append(
                f"- **Diferença média**: {stats['mean_abs_difference']:.2f}°C "
                f"(máxima: {stats['max_abs_difference']:.2f}°C)"
            )

        status_counts = validation_report.get_status_counts()
        if status_counts['error'] > 0 or status_counts['warning'] > 0:
            lines.append("")
            lines.append("**⚠️ ATENÇÃO:**")
            if status_counts['error'] > 0:
                lines.append(
                    f"- {status_counts['error']} ROI(s) com diferença > 1.0°C "
                    f"(possível divergência significativa)"
                )
            if status_counts['warning'] > 0:
                lines.append(
                    f"- {status_counts['warning']} ROI(s) com diferença entre 0.5-1.0°C "
                    f"(verificar)"
                )

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("**INSTRUÇÕES PARA O LAUDO:**")
        lines.append("")
        lines.append(
            "1. **Use preferencialmente as medições FLIR** quando disponíveis, "
            "pois são de equipamento profissional calibrado"
        )
        lines.append(
            "2. Se houver **discrepâncias significativas** (> 1.0°C), mencione no laudo "
            "que foi utilizada referência FLIR"
        )
        lines.append(
            "3. **Não mencione detalhes técnicos** da validação no laudo final "
            "(é informação interna)"
        )
        lines.append(
            "4. Simplesmente use os **valores mais precisos disponíveis** para a análise clínica"
        )

        return "\n".join(lines)

    def _find_matching_image(
        self,
        flir_data: FLIRExportData,
        image_name: str
    ) -> Optional[any]:
        """
        Encontra imagem FLIR correspondente ao nome fornecido.

        Args:
            flir_data: Dados FLIR
            image_name: Nome da imagem procurada

        Returns:
            FLIRImageData ou None
        """
        # Extrai nome base sem extensão
        image_base = Path(image_name).stem.lower()

        for image in flir_data.images:
            flir_base = Path(image.filename).stem.lower()

            # Match exato
            if image_base == flir_base:
                return image

            # Match parcial
            if image_base in flir_base or flir_base in image_base:
                return image

        return None

    def create_validation_summary_for_ui(
        self,
        validation_report: ValidationReport
    ) -> str:
        """
        Cria resumo breve da validação para exibir na UI.

        Args:
            validation_report: Relatório de validação

        Returns:
            Texto formatado para UI
        """
        status_counts = validation_report.get_status_counts()
        accuracy = validation_report.get_accuracy_percentage()

        lines = []
        lines.append("📊 Validação FLIR:")
        lines.append(f"   Precisão: {accuracy:.1f}%")
        lines.append(
            f"   ✅ {status_counts['ok']}  "
            f"⚠️ {status_counts['warning']}  "
            f"❌ {status_counts['error']}"
        )

        if validation_report.statistics:
            stats = validation_report.statistics
            lines.append(
                f"   Diff média: {stats['mean_abs_difference']:.2f}°C "
                f"(máx: {stats['max_abs_difference']:.2f}°C)"
            )

        return "\n".join(lines)


def enhance_prompt_with_flir(
    base_prompt: str,
    flir_html_path: Optional[Path],
    system_temperatures: Dict[str, float],
    image_name: str
) -> tuple[str, Optional[ValidationReport]]:
    """
    Função helper para enriquecer prompt com dados FLIR.

    Args:
        base_prompt: Prompt original
        flir_html_path: Caminho para HTML FLIR (None se não disponível)
        system_temperatures: Temperaturas do sistema
        image_name: Nome da imagem

    Returns:
        (prompt_enriquecido, validation_report)
    """
    if flir_html_path is None or not flir_html_path.exists():
        return base_prompt, None

    # Parse FLIR HTML
    from core.flir_html_parser import parse_flir_html

    try:
        flir_data = parse_flir_html(flir_html_path)
    except Exception as e:
        print(f"⚠️ Erro ao parsear FLIR HTML: {e}")
        return base_prompt, None

    # Enriquece prompt
    enhancer = FLIRPromptEnhancer()
    enhanced_prompt = enhancer.enhance_professional_report_prompt(
        base_prompt,
        flir_data,
        system_temperatures,
        image_name
    )

    # Valida
    validator = FLIRValidator()
    validation_report = validator.validate(flir_data, system_temperatures)

    return enhanced_prompt, validation_report


if __name__ == "__main__":
    print("FLIRPromptEnhancer module loaded successfully")
    print("Use: from core.flir_prompt_enhancer import enhance_prompt_with_flir")
