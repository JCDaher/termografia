"""
Interface para visualizar histórico de pacientes e exames anteriores.
Permite busca, comparação e análise de evolução.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTableWidget, QTableWidgetItem, QTextEdit,
    QMessageBox, QSplitter, QGroupBox, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

from database.db_manager import get_db_manager

logger = logging.getLogger(__name__)


class PatientHistoryDialog(QDialog):
    """Dialog para visualizar histórico de pacientes."""

    patient_selected = pyqtSignal(int)  # Emite ID do paciente selecionado
    exam_selected = pyqtSignal(int)  # Emite ID do exame selecionado

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Histórico de Pacientes")
        self.resize(1000, 700)

        self.db_manager = get_db_manager()
        self.current_patient_id = None
        self.current_exam_id = None

        self.init_ui()

    def init_ui(self):
        """Inicializa a interface."""
        layout = QVBoxLayout(self)

        # Barra de busca
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Buscar Paciente:"))

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Digite nome ou prontuário...")
        self.input_search.returnPressed.connect(self.search_patients)
        search_layout.addWidget(self.input_search)

        self.btn_search = QPushButton("🔍 Buscar")
        self.btn_search.clicked.connect(self.search_patients)
        search_layout.addWidget(self.btn_search)

        self.btn_show_all = QPushButton("Mostrar Todos")
        self.btn_show_all.clicked.connect(self.load_all_patients)
        search_layout.addWidget(self.btn_show_all)

        layout.addLayout(search_layout)

        # Splitter principal
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Painel esquerdo - Lista de pacientes
        left_panel = QGroupBox("Pacientes")
        left_layout = QVBoxLayout(left_panel)

        self.table_patients = QTableWidget()
        self.table_patients.setColumnCount(4)
        self.table_patients.setHorizontalHeaderLabels(['ID', 'Nome', 'Prontuário', 'Gênero'])
        self.table_patients.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_patients.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_patients.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table_patients.itemSelectionChanged.connect(self.on_patient_selected)
        self.table_patients.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        left_layout.addWidget(self.table_patients)

        self.lbl_patient_count = QLabel("Total: 0 pacientes")
        left_layout.addWidget(self.lbl_patient_count)

        splitter.addWidget(left_panel)

        # Painel direito - Dados do paciente e exames
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Dados do paciente
        patient_group = QGroupBox("Dados do Paciente")
        patient_layout = QVBoxLayout(patient_group)

        self.text_patient_info = QTextEdit()
        self.text_patient_info.setReadOnly(True)
        self.text_patient_info.setMaximumHeight(120)
        patient_layout.addWidget(self.text_patient_info)

        right_layout.addWidget(patient_group)

        # Exames do paciente
        exams_group = QGroupBox("Exames do Paciente")
        exams_layout = QVBoxLayout(exams_group)

        self.table_exams = QTableWidget()
        self.table_exams.setColumnCount(4)
        self.table_exams.setHorizontalHeaderLabels(['ID', 'Data', 'Tipo', 'Status'])
        self.table_exams.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_exams.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_exams.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table_exams.itemSelectionChanged.connect(self.on_exam_selected)
        self.table_exams.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        exams_layout.addWidget(self.table_exams)

        self.lbl_exam_count = QLabel("Total: 0 exames")
        exams_layout.addWidget(self.lbl_exam_count)

        right_layout.addWidget(exams_group)

        # Detalhes do exame selecionado
        exam_details_group = QGroupBox("Detalhes do Exame")
        exam_details_layout = QVBoxLayout(exam_details_group)

        self.text_exam_details = QTextEdit()
        self.text_exam_details.setReadOnly(True)
        exam_details_layout.addWidget(self.text_exam_details)

        right_layout.addWidget(exam_details_group)

        splitter.addWidget(right_panel)

        # Proporção do splitter
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

        # Botões de ação
        buttons_layout = QHBoxLayout()

        self.btn_load_patient = QPushButton("Carregar Paciente")
        self.btn_load_patient.clicked.connect(self.load_selected_patient)
        self.btn_load_patient.setEnabled(False)
        buttons_layout.addWidget(self.btn_load_patient)

        self.btn_load_exam = QPushButton("Carregar Exame")
        self.btn_load_exam.clicked.connect(self.load_selected_exam)
        self.btn_load_exam.setEnabled(False)
        buttons_layout.addWidget(self.btn_load_exam)

        buttons_layout.addStretch()

        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_close)

        layout.addLayout(buttons_layout)

        # Carrega todos os pacientes inicialmente
        self.load_all_patients()

    def search_patients(self):
        """Busca pacientes por nome ou prontuário."""
        query = self.input_search.text().strip()

        if not query:
            QMessageBox.warning(self, "Aviso", "Digite algo para buscar")
            return

        try:
            patients = self.db_manager.search_patients(query)
            self.populate_patients_table(patients)

        except Exception as e:
            logger.error(f"Erro ao buscar pacientes: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao buscar pacientes: {e}")

    def load_all_patients(self):
        """Carrega todos os pacientes."""
        try:
            # Busca com string vazia retorna todos
            patients = self.db_manager.search_patients("")
            self.populate_patients_table(patients)

        except Exception as e:
            logger.error(f"Erro ao carregar pacientes: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao carregar pacientes: {e}")

    def populate_patients_table(self, patients: List[Dict[str, Any]]):
        """
        Popula a tabela de pacientes.

        Args:
            patients: Lista de dicionários com dados dos pacientes
        """
        self.table_patients.setRowCount(0)

        for patient in patients:
            row = self.table_patients.rowCount()
            self.table_patients.insertRow(row)

            self.table_patients.setItem(row, 0, QTableWidgetItem(str(patient['id'])))
            self.table_patients.setItem(row, 1, QTableWidgetItem(patient['name']))
            self.table_patients.setItem(row, 2, QTableWidgetItem(patient.get('medical_record', '')))
            self.table_patients.setItem(row, 3, QTableWidgetItem(patient.get('gender', '')))

        self.lbl_patient_count.setText(f"Total: {len(patients)} paciente(s)")

        # Limpa seleção de exames
        self.table_exams.setRowCount(0)
        self.text_patient_info.clear()
        self.text_exam_details.clear()
        self.lbl_exam_count.setText("Total: 0 exames")

    def on_patient_selected(self):
        """Callback quando paciente é selecionado."""
        selected_rows = self.table_patients.selectedItems()

        if not selected_rows:
            return

        row = selected_rows[0].row()
        patient_id = int(self.table_patients.item(row, 0).text())

        self.current_patient_id = patient_id
        self.btn_load_patient.setEnabled(True)

        try:
            # Carrega dados do paciente
            patient = self.db_manager.get_patient(patient_id)

            if patient:
                # Mostra informações do paciente
                info_text = f"""
<b>Nome:</b> {patient['name']}<br>
<b>Prontuário:</b> {patient.get('medical_record', 'Não informado')}<br>
<b>Data de Nascimento:</b> {patient.get('birth_date', 'Não informada')}<br>
<b>Gênero:</b> {patient.get('gender', 'Não informado')}<br>
<b>Telefone:</b> {patient.get('phone', 'Não informado')}<br>
<b>Email:</b> {patient.get('email', 'Não informado')}
"""
                self.text_patient_info.setHtml(info_text)

                # Carrega exames do paciente
                exams = self.db_manager.get_patient_exams(patient_id)
                self.populate_exams_table(exams)

        except Exception as e:
            logger.error(f"Erro ao carregar dados do paciente: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao carregar dados: {e}")

    def populate_exams_table(self, exams: List[Dict[str, Any]]):
        """
        Popula a tabela de exames.

        Args:
            exams: Lista de dicionários com dados dos exames
        """
        self.table_exams.setRowCount(0)

        for exam in exams:
            row = self.table_exams.rowCount()
            self.table_exams.insertRow(row)

            # Formata data
            exam_date = exam.get('exam_date', '')
            if exam_date:
                try:
                    dt = datetime.fromisoformat(exam_date)
                    exam_date = dt.strftime('%d/%m/%Y %H:%M')
                except:
                    pass

            self.table_exams.setItem(row, 0, QTableWidgetItem(str(exam['id'])))
            self.table_exams.setItem(row, 1, QTableWidgetItem(exam_date))
            self.table_exams.setItem(row, 2, QTableWidgetItem(exam.get('exam_type', '')))
            self.table_exams.setItem(row, 3, QTableWidgetItem(exam.get('status', '')))

        self.lbl_exam_count.setText(f"Total: {len(exams)} exame(s)")

    def on_exam_selected(self):
        """Callback quando exame é selecionado."""
        selected_rows = self.table_exams.selectedItems()

        if not selected_rows:
            return

        row = selected_rows[0].row()
        exam_id = int(self.table_exams.item(row, 0).text())

        self.current_exam_id = exam_id
        self.btn_load_exam.setEnabled(True)

        try:
            # Carrega detalhes do exame
            exam = self.db_manager.get_exam(exam_id)

            if exam:
                # Formata data
                exam_date = exam.get('exam_date', '')
                if exam_date:
                    try:
                        dt = datetime.fromisoformat(exam_date)
                        exam_date = dt.strftime('%d/%m/%Y às %H:%M')
                    except:
                        pass

                # Busca imagens do exame
                images = self.db_manager.get_exam_images(exam_id)

                # Busca laudos do exame
                reports = self.db_manager.get_exam_reports(exam_id)

                details_text = f"""
<h3>Exame #{exam_id}</h3>

<b>Data:</b> {exam_date}<br>
<b>Tipo:</b> {exam.get('exam_type', 'Não especificado')}<br>
<b>Status:</b> {exam.get('status', 'Em andamento')}<br>
<b>Região Corporal:</b> {exam.get('body_region', 'Não especificada')}<br>

<h4>Indicação Clínica:</h4>
{exam.get('clinical_indication', 'Não informada')}

<h4>Sintomas:</h4>
{exam.get('symptoms', 'Não informados')}

<h4>Imagens:</h4>
Total de {len(images)} imagem(ns) termográfica(s)

<h4>Laudos:</h4>
Total de {len(reports)} laudo(s) gerado(s)
"""
                self.text_exam_details.setHtml(details_text)

        except Exception as e:
            logger.error(f"Erro ao carregar detalhes do exame: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao carregar detalhes: {e}")

    def load_selected_patient(self):
        """Carrega o paciente selecionado."""
        if self.current_patient_id:
            self.patient_selected.emit(self.current_patient_id)
            self.accept()

    def load_selected_exam(self):
        """Carrega o exame selecionado."""
        if self.current_exam_id:
            self.exam_selected.emit(self.current_exam_id)
            self.accept()


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    dialog = PatientHistoryDialog()
    dialog.exec()
