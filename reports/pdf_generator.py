"""
Gerador de PDFs profissionais para laudos médicos termográficos.
Utiliza ReportLab para criar documentos formatados com cabeçalho, rodapé e logo.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image as RLImage, KeepTogether
)
from reportlab.lib import colors
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Gera PDFs profissionais de laudos médicos."""

    def __init__(self):
        """Inicializa o gerador de PDF."""
        self.pagesize = A4
        self.width, self.height = self.pagesize

        # Margens
        self.margin_left = 2.5 * cm
        self.margin_right = 2.5 * cm
        self.margin_top = 3.0 * cm
        self.margin_bottom = 2.5 * cm

        # Estilos
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()

    def _create_custom_styles(self):
        """Cria estilos personalizados para o documento."""
        # Título principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a5490'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Subtítulo
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=6,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))

        # Corpo de texto
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            leading=14
        ))

        # Texto pequeno (rodapé)
        self.styles.add(ParagraphStyle(
            name='SmallText',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        ))

        # Informações do paciente
        self.styles.add(ParagraphStyle(
            name='PatientInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=3
        ))

    def _header(self, canvas, doc, physician_data: Optional[Dict] = None):
        """
        Desenha cabeçalho em todas as páginas.

        Args:
            canvas: Canvas do ReportLab
            doc: Documento
            physician_data: Dados do médico (nome, CRM, especialidade, etc.)
        """
        canvas.saveState()

        # Logo (se existir)
        logo_path = Path('assets/logo.png')
        if logo_path.exists():
            try:
                canvas.drawImage(
                    str(logo_path),
                    self.margin_left,
                    self.height - 2.5 * cm,
                    width=3 * cm,
                    height=1.5 * cm,
                    preserveAspectRatio=True
                )
            except Exception as e:
                logger.warning(f"Erro ao carregar logo: {e}")

        # Nome do médico/clínica
        canvas.setFont('Helvetica-Bold', 12)
        if physician_data:
            physician_name = physician_data.get('name', 'Termografia Médica')
            canvas.drawRightString(
                self.width - self.margin_right,
                self.height - 1.5 * cm,
                physician_name
            )

            # CRM e especialidade
            canvas.setFont('Helvetica', 9)
            crm = physician_data.get('crm', '')
            specialty = physician_data.get('specialty', 'Termografia Médica')

            if crm:
                canvas.drawRightString(
                    self.width - self.margin_right,
                    self.height - 1.9 * cm,
                    f"CRM: {crm} - {specialty}"
                )
            else:
                canvas.drawRightString(
                    self.width - self.margin_right,
                    self.height - 1.9 * cm,
                    specialty
                )

        # Linha separadora
        canvas.setStrokeColor(colors.HexColor('#1a5490'))
        canvas.setLineWidth(1)
        canvas.line(
            self.margin_left,
            self.height - 2.8 * cm,
            self.width - self.margin_right,
            self.height - 2.8 * cm
        )

        canvas.restoreState()

    def _footer(self, canvas, doc):
        """
        Desenha rodapé em todas as páginas.

        Args:
            canvas: Canvas do ReportLab
            doc: Documento
        """
        canvas.saveState()

        # Linha separadora
        canvas.setStrokeColor(colors.grey)
        canvas.setLineWidth(0.5)
        canvas.line(
            self.margin_left,
            2.2 * cm,
            self.width - self.margin_right,
            2.2 * cm
        )

        # Texto do rodapé
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)

        footer_text = "Laudo gerado por Sistema de Termografia Médica"
        canvas.drawCentredString(
            self.width / 2.0,
            1.8 * cm,
            footer_text
        )

        # Data e hora de geração
        generation_time = datetime.now().strftime('%d/%m/%Y às %H:%M')
        canvas.drawCentredString(
            self.width / 2.0,
            1.4 * cm,
            f"Gerado em {generation_time}"
        )

        # Número da página
        page_num = f"Página {canvas.getPageNumber()}"
        canvas.drawRightString(
            self.width - self.margin_right,
            1.0 * cm,
            page_num
        )

        canvas.restoreState()

    def generate_report(self, output_path: str, report_data: Dict[str, Any],
                       physician_data: Optional[Dict] = None,
                       include_images: bool = True) -> bool:
        """
        Gera PDF do laudo médico.

        Args:
            output_path: Caminho para salvar o PDF
            report_data: Dados do laudo (paciente, exame, texto do laudo, etc.)
            physician_data: Dados do médico responsável
            include_images: Se True, inclui imagens termográficas no PDF

        Returns:
            True se gerado com sucesso, False caso contrário
        """
        try:
            # Cria documento
            doc = SimpleDocTemplate(
                output_path,
                pagesize=self.pagesize,
                leftMargin=self.margin_left,
                rightMargin=self.margin_right,
                topMargin=self.margin_top,
                bottomMargin=self.margin_bottom
            )

            # Elementos do documento
            story = []

            # Título
            story.append(Paragraph(
                "LAUDO TERMOGRÁFICO",
                self.styles['CustomTitle']
            ))
            story.append(Spacer(1, 0.5 * cm))

            # Dados do paciente
            patient_data = report_data.get('patient', {})
            exam_data = report_data.get('exam', {})

            patient_info = [
                ['<b>Paciente:</b>', patient_data.get('name', 'Não informado')],
                ['<b>Data de Nascimento:</b>', patient_data.get('birth_date', 'Não informado')],
                ['<b>Prontuário:</b>', patient_data.get('medical_record', 'Não informado')],
                ['<b>Data do Exame:</b>', exam_data.get('exam_date', datetime.now().strftime('%d/%m/%Y'))],
                ['<b>Tipo de Exame:</b>', exam_data.get('exam_type', 'Termografia')],
            ]

            # Tabela de informações do paciente
            patient_table = Table(patient_info, colWidths=[4.5 * cm, 11 * cm])
            patient_table.setStyle(TableStyle([
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
                ('FONT', (1, 0), (1, -1), 'Helvetica', 9),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))

            story.append(patient_table)
            story.append(Spacer(1, 0.5 * cm))

            # Indicação clínica
            if exam_data.get('clinical_indication'):
                story.append(Paragraph(
                    "INDICAÇÃO CLÍNICA",
                    self.styles['CustomHeading']
                ))
                story.append(Paragraph(
                    exam_data['clinical_indication'],
                    self.styles['CustomBody']
                ))
                story.append(Spacer(1, 0.3 * cm))

            # Texto do laudo
            report_text = report_data.get('report_text', '')
            if report_text:
                # Divide o texto em seções se houver marcadores
                sections = self._parse_report_sections(report_text)

                for section in sections:
                    if section['is_heading']:
                        story.append(Paragraph(
                            section['text'],
                            self.styles['CustomHeading']
                        ))
                    else:
                        story.append(Paragraph(
                            section['text'],
                            self.styles['CustomBody']
                        ))

            # Imagens (se solicitado)
            if include_images and report_data.get('images'):
                story.append(PageBreak())
                story.append(Paragraph(
                    "IMAGENS TERMOGRÁFICAS",
                    self.styles['CustomTitle']
                ))
                story.append(Spacer(1, 0.5 * cm))

                for img_data in report_data['images']:
                    img_path = img_data.get('path')
                    if img_path and Path(img_path).exists():
                        try:
                            img = RLImage(img_path, width=15 * cm, height=10 * cm)
                            story.append(img)
                            story.append(Paragraph(
                                img_data.get('caption', 'Imagem termográfica'),
                                self.styles['SmallText']
                            ))
                            story.append(Spacer(1, 0.5 * cm))
                        except Exception as e:
                            logger.warning(f"Erro ao incluir imagem {img_path}: {e}")

            # Assinatura (se houver dados do médico)
            if physician_data:
                story.append(Spacer(1, 1.5 * cm))
                story.append(Paragraph("_" * 50, self.styles['CustomBody']))
                story.append(Paragraph(
                    f"<b>{physician_data.get('name', '')}</b>",
                    self.styles['CustomBody']
                ))
                if physician_data.get('crm'):
                    story.append(Paragraph(
                        f"CRM: {physician_data['crm']}",
                        self.styles['CustomBody']
                    ))

            # Gera PDF
            doc.build(
                story,
                onFirstPage=lambda c, d: self._header(c, d, physician_data),
                onLaterPages=lambda c, d: self._header(c, d, physician_data),
            )

            logger.info(f"PDF gerado com sucesso: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Erro ao gerar PDF: {e}")
            return False

    def _parse_report_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse do texto do laudo em seções.

        Args:
            text: Texto completo do laudo

        Returns:
            Lista de seções com tipo (heading ou body)
        """
        sections = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detecta se é um cabeçalho (texto em maiúsculas, ou começa com ##, ou tem **texto**)
            is_heading = False

            if line.isupper() and len(line) < 100:
                is_heading = True
            elif line.startswith('##'):
                line = line.replace('##', '').strip()
                is_heading = True
            elif line.startswith('**') and line.endswith('**'):
                line = line.replace('**', '').strip()
                is_heading = True

            sections.append({
                'text': line,
                'is_heading': is_heading
            })

        return sections


class PDFGeneratorError(Exception):
    """Exceção para erros na geração de PDF."""
    pass


if __name__ == '__main__':
    # Teste básico
    print("=== Teste do PDFGenerator ===\n")

    generator = PDFGenerator()

    # Dados de teste
    report_data = {
        'patient': {
            'name': 'João Silva',
            'birth_date': '15/05/1980',
            'medical_record': '12345'
        },
        'exam': {
            'exam_date': '15/01/2024',
            'exam_type': 'Termografia de Dermátomos',
            'clinical_indication': 'Dor cervical irradiada para membro superior esquerdo'
        },
        'report_text': """
## DADOS DO EXAME
Exame realizado em 15/01/2024

## ACHADOS TERMOGRÁFICOS
Assimetria térmica detectada em dermátomo C5 esquerdo.
ΔT de 1.3°C em relação ao lado contralateral.

## CONCLUSÃO
Achados compatíveis com processo inflamatório em dermátomo C5 à esquerda.
        """
    }

    physician_data = {
        'name': 'Dr. Jorge Cecílio Daher Jr.',
        'crm': 'CRM-GO 6108',
        'specialty': 'Endocrinologia e Metabologia'
    }

    success = generator.generate_report(
        'test_report.pdf',
        report_data,
        physician_data
    )

    if success:
        print("✓ PDF de teste gerado: test_report.pdf")
    else:
        print("✗ Erro ao gerar PDF")
