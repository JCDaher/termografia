"""
Editor de laudos médicos com capacidade de revisão e edição.
Permite ao médico revisar, editar e finalizar laudos antes de salvar/exportar.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QGroupBox, QLineEdit, QMessageBox, QSplitter,
    QTabWidget, QWidget, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ReportEditorDialog(QDialog):
    """Dialog para edição e revisão de laudos médicos."""

    report_finalized = pyqtSignal(dict)  # Emite dados do laudo finalizado

    def __init__(self, report_text: str = "", patient_data: Optional[Dict] = None,
                 exam_data: Optional[Dict] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editor de Laudos - Revisão e Edição")
        self.resize(1000, 800)

        self.original_text = report_text
        self.patient_data = patient_data or {}
        self.exam_data = exam_data or {}
        self.modified = False

        self.init_ui()
        self.load_report(report_text)

    def init_ui(self):
        """Inicializa a interface."""
        layout = QVBoxLayout(self)

        # Header com informações do paciente
        header_group = QGroupBox("Informações do Laudo")
        header_layout = QFormLayout(header_group)

        # Campos de metadados do laudo
        self.input_patient_name = QLineEdit()
        self.input_patient_name.setText(self.patient_data.get('name', 'Não informado'))
        self.input_patient_name.setReadOnly(True)

        self.input_exam_date = QLineEdit()
        self.input_exam_date.setText(self.exam_data.get('exam_date', datetime.now().strftime('%d/%m/%Y')))
        self.input_exam_date.setReadOnly(True)

        self.input_exam_type = QLineEdit()
        self.input_exam_type.setText(self.exam_data.get('exam_type', 'Termografia'))
        self.input_exam_type.setReadOnly(True)

        header_layout.addRow("Paciente:", self.input_patient_name)
        header_layout.addRow("Data do Exame:", self.input_exam_date)
        header_layout.addRow("Tipo de Exame:", self.input_exam_type)

        layout.addWidget(header_group)

        # Tabs principais
        self.tabs = QTabWidget()

        # Tab 1: Editor Principal
        editor_tab = self.create_editor_tab()
        self.tabs.addTab(editor_tab, "Editor de Texto")

        # Tab 2: Metadados e Assinatura
        metadata_tab = self.create_metadata_tab()
        self.tabs.addTab(metadata_tab, "Metadados e Assinatura")

        # Tab 3: Pré-visualização
        preview_tab = self.create_preview_tab()
        self.tabs.addTab(preview_tab, "Pré-visualização")

        layout.addWidget(self.tabs)

        # Contador de caracteres
        self.lbl_char_count = QLabel("0 caracteres")
        layout.addWidget(self.lbl_char_count)

        # Botões de ação
        buttons_layout = QHBoxLayout()

        self.btn_restore = QPushButton("🔄 Restaurar Original")
        self.btn_restore.clicked.connect(self.restore_original)
        self.btn_restore.setToolTip("Restaura o texto original gerado pelo Claude")
        buttons_layout.addWidget(self.btn_restore)

        buttons_layout.addStretch()

        self.btn_preview = QPushButton("👁 Atualizar Pré-visualização")
        self.btn_preview.clicked.connect(self.update_preview)
        buttons_layout.addWidget(self.btn_preview)

        self.btn_save = QPushButton("💾 Salvar Laudo")
        self.btn_save.clicked.connect(self.save_report)
        self.btn_save.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;")
        buttons_layout.addWidget(self.btn_save)

        btn_cancel = QPushButton("✖ Cancelar")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        layout.addLayout(buttons_layout)

    def create_editor_tab(self) -> QWidget:
        """Cria a tab do editor principal."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Barra de ferramentas de edição
        toolbar = QHBoxLayout()

        btn_bold = QPushButton("B")
        btn_bold.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        btn_bold.setMaximumWidth(40)
        btn_bold.setToolTip("Negrito (Ctrl+B)")
        btn_bold.clicked.connect(lambda: self.insert_markdown('**', '**'))
        toolbar.addWidget(btn_bold)

        btn_italic = QPushButton("I")
        btn_italic.setFont(QFont("Arial", 10, QFont.Weight.Normal))
        btn_italic.setStyleSheet("font-style: italic;")
        btn_italic.setMaximumWidth(40)
        btn_italic.setToolTip("Itálico (Ctrl+I)")
        btn_italic.clicked.connect(lambda: self.insert_markdown('*', '*'))
        toolbar.addWidget(btn_italic)

        btn_heading = QPushButton("H")
        btn_heading.setMaximumWidth(40)
        btn_heading.setToolTip("Cabeçalho")
        btn_heading.clicked.connect(lambda: self.insert_markdown('## ', ''))
        toolbar.addWidget(btn_heading)

        btn_bullet = QPushButton("• Lista")
        btn_bullet.setToolTip("Lista com marcadores")
        btn_bullet.clicked.connect(lambda: self.insert_markdown('- ', ''))
        toolbar.addWidget(btn_bullet)

        toolbar.addStretch()

        layout.addLayout(toolbar)

        # Instruções
        instructions = QLabel(
            "<i>Dica: Use formatação Markdown para estruturar o laudo. "
            "O texto será formatado automaticamente no PDF.</i>"
        )
        instructions.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(instructions)

        # Editor de texto principal
        self.text_editor = QTextEdit()
        self.text_editor.setFont(QFont("Consolas", 11))
        self.text_editor.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.text_editor)

        return tab

    def create_metadata_tab(self) -> QWidget:
        """Cria a tab de metadados e assinatura."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Dados do médico responsável
        physician_group = QGroupBox("Dados do Médico Responsável")
        physician_layout = QFormLayout(physician_group)

        self.input_physician_name = QLineEdit()
        self.input_physician_name.setPlaceholderText("Nome completo do médico")

        self.input_physician_crm = QLineEdit()
        self.input_physician_crm.setPlaceholderText("CRM-UF 12345")

        self.input_physician_specialty = QLineEdit()
        self.input_physician_specialty.setPlaceholderText("Especialidade médica")

        physician_layout.addRow("Nome do Médico:", self.input_physician_name)
        physician_layout.addRow("CRM:", self.input_physician_crm)
        physician_layout.addRow("Especialidade:", self.input_physician_specialty)

        layout.addWidget(physician_group)

        # Conclusão e Recomendações
        conclusion_group = QGroupBox("Conclusão e Recomendações")
        conclusion_layout = QVBoxLayout(conclusion_group)

        conclusion_layout.addWidget(QLabel("<b>Conclusão:</b>"))
        self.text_conclusion = QTextEdit()
        self.text_conclusion.setMaximumHeight(100)
        self.text_conclusion.setPlaceholderText("Resumo objetivo dos principais achados...")
        conclusion_layout.addWidget(self.text_conclusion)

        conclusion_layout.addWidget(QLabel("<b>Recomendações:</b>"))
        self.text_recommendations = QTextEdit()
        self.text_recommendations.setMaximumHeight(100)
        self.text_recommendations.setPlaceholderText("Sugestões de conduta, exames complementares, acompanhamento...")
        conclusion_layout.addWidget(self.text_recommendations)

        layout.addWidget(conclusion_group)

        # Tipo de laudo
        type_group = QGroupBox("Tipo de Laudo")
        type_layout = QHBoxLayout(type_group)

        self.btn_preliminary = QPushButton("Preliminar")
        self.btn_preliminary.setCheckable(True)
        self.btn_preliminary.setChecked(True)
        self.btn_preliminary.clicked.connect(self.set_preliminary)

        self.btn_final = QPushButton("Final")
        self.btn_final.setCheckable(True)
        self.btn_final.clicked.connect(self.set_final)

        self.btn_complementary = QPushButton("Complementar")
        self.btn_complementary.setCheckable(True)
        self.btn_complementary.clicked.connect(self.set_complementary)

        type_layout.addWidget(self.btn_preliminary)
        type_layout.addWidget(self.btn_final)
        type_layout.addWidget(self.btn_complementary)
        type_layout.addStretch()

        layout.addWidget(type_group)

        layout.addStretch()

        return tab

    def create_preview_tab(self) -> QWidget:
        """Cria a tab de pré-visualização."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        layout.addWidget(QLabel("<b>Pré-visualização do Laudo:</b>"))

        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        layout.addWidget(self.text_preview)

        btn_update = QPushButton("🔄 Atualizar Pré-visualização")
        btn_update.clicked.connect(self.update_preview)
        layout.addWidget(btn_update)

        return tab

    def set_preliminary(self):
        """Define tipo como Preliminar."""
        self.btn_preliminary.setChecked(True)
        self.btn_final.setChecked(False)
        self.btn_complementary.setChecked(False)

    def set_final(self):
        """Define tipo como Final."""
        self.btn_preliminary.setChecked(False)
        self.btn_final.setChecked(True)
        self.btn_complementary.setChecked(False)

    def set_complementary(self):
        """Define tipo como Complementar."""
        self.btn_preliminary.setChecked(False)
        self.btn_final.setChecked(False)
        self.btn_complementary.setChecked(True)

    def insert_markdown(self, prefix: str, suffix: str):
        """
        Insere formatação Markdown no texto selecionado.

        Args:
            prefix: Texto antes da seleção
            suffix: Texto depois da seleção
        """
        cursor = self.text_editor.textCursor()

        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            new_text = f"{prefix}{selected_text}{suffix}"
            cursor.insertText(new_text)
        else:
            cursor.insertText(f"{prefix}{suffix}")
            # Move cursor entre prefix e suffix
            for _ in range(len(suffix)):
                cursor.movePosition(QTextCursor.MoveOperation.Left)
            self.text_editor.setTextCursor(cursor)

    def load_report(self, text: str):
        """
        Carrega texto do laudo no editor.

        Args:
            text: Texto do laudo
        """
        self.text_editor.setPlainText(text)
        self.update_char_count()

    def on_text_changed(self):
        """Callback quando texto é modificado."""
        self.modified = True
        self.update_char_count()

    def update_char_count(self):
        """Atualiza contador de caracteres."""
        text = self.text_editor.toPlainText()
        char_count = len(text)
        word_count = len(text.split())
        self.lbl_char_count.setText(f"{char_count} caracteres | {word_count} palavras")

    def restore_original(self):
        """Restaura o texto original."""
        if self.modified:
            reply = QMessageBox.question(
                self,
                "Confirmar",
                "Deseja realmente restaurar o texto original? Todas as edições serão perdidas.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.text_editor.setPlainText(self.original_text)
                self.modified = False
        else:
            self.text_editor.setPlainText(self.original_text)

    def update_preview(self):
        """Atualiza a pré-visualização do laudo."""
        # Monta o laudo completo
        report_parts = []

        # Cabeçalho
        report_parts.append("=" * 60)
        report_parts.append("LAUDO TERMOGRÁFICO")
        report_parts.append("=" * 60)
        report_parts.append("")

        # Dados do paciente
        report_parts.append(f"Paciente: {self.patient_data.get('name', 'Não informado')}")
        report_parts.append(f"Data do Exame: {self.exam_data.get('exam_date', 'Não informada')}")
        report_parts.append(f"Tipo: {self.exam_data.get('exam_type', 'Termografia')}")
        report_parts.append("")

        # Texto principal
        report_parts.append(self.text_editor.toPlainText())
        report_parts.append("")

        # Conclusão
        conclusion = self.text_conclusion.toPlainText().strip()
        if conclusion:
            report_parts.append("CONCLUSÃO:")
            report_parts.append(conclusion)
            report_parts.append("")

        # Recomendações
        recommendations = self.text_recommendations.toPlainText().strip()
        if recommendations:
            report_parts.append("RECOMENDAÇÕES:")
            report_parts.append(recommendations)
            report_parts.append("")

        # Assinatura
        physician_name = self.input_physician_name.text().strip()
        if physician_name:
            report_parts.append("_" * 50)
            report_parts.append(physician_name)
            crm = self.input_physician_crm.text().strip()
            if crm:
                report_parts.append(f"CRM: {crm}")

        # Atualiza preview
        preview_text = "\n".join(report_parts)
        self.text_preview.setPlainText(preview_text)

        # Muda para tab de preview
        self.tabs.setCurrentIndex(2)

    def get_report_type(self) -> str:
        """Retorna o tipo de laudo selecionado."""
        if self.btn_preliminary.isChecked():
            return "Preliminar"
        elif self.btn_final.isChecked():
            return "Final"
        else:
            return "Complementar"

    def save_report(self):
        """Salva o laudo finalizado."""
        # Valida campos obrigatórios
        if not self.text_editor.toPlainText().strip():
            QMessageBox.warning(self, "Aviso", "O laudo não pode estar vazio")
            return

        # Monta dados do laudo
        report_data = {
            'report_text': self.text_editor.toPlainText(),
            'conclusion': self.text_conclusion.toPlainText().strip(),
            'recommendations': self.text_recommendations.toPlainText().strip(),
            'report_type': self.get_report_type(),
            'physician_name': self.input_physician_name.text().strip(),
            'physician_crm': self.input_physician_crm.text().strip(),
            'physician_specialty': self.input_physician_specialty.text().strip(),
            'modified': self.modified
        }

        # Emite sinal com dados
        self.report_finalized.emit(report_data)
        self.accept()

    def closeEvent(self, event):
        """Evento de fechamento da janela."""
        if self.modified:
            reply = QMessageBox.question(
                self,
                "Confirmar",
                "Há alterações não salvas. Deseja realmente sair?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        event.accept()


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # Dados de teste
    test_report = """
## DADOS DO EXAME
Exame termográfico realizado em 15/01/2024

## ACHADOS TERMOGRÁFICOS
Observa-se assimetria térmica em dermátomo C5 esquerdo.
ΔT de 1.3°C comparado ao lado contralateral.

## INTERPRETAÇÃO
Achados compatíveis com processo inflamatório.
"""

    patient_data = {'name': 'João Silva'}
    exam_data = {
        'exam_date': '15/01/2024',
        'exam_type': 'Termografia de Dermátomos'
    }

    dialog = ReportEditorDialog(test_report, patient_data, exam_data)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("Laudo salvo!")
    else:
        print("Cancelado")
