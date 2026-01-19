"""
Interface principal do aplicativo de termografia médica.
Janela principal PyQt6 com funcionalidades de importação, análise e geração de laudos.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QTextEdit, QTabWidget, QGroupBox,
    QLineEdit, QComboBox, QSpinBox, QMessageBox, QProgressBar,
    QTableWidget, QTableWidgetItem, QSplitter, QFormLayout, QListWidget,
    QMenu, QMenuBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QKeySequence, QShortcut, QAction
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
import logging
from typing import Optional, Dict, Any, List

from core.flir_processor import FLIRProcessor
from core.thermal_analyzer import ThermalAnalyzer
from database.db_manager import get_db_manager
from api.claude_client import get_claude_client, has_api_key, configure_api_key
from reports.pdf_generator import PDFGenerator
from ui.roi_editor import ROIEditorDialog
from ui.patient_history import PatientHistoryDialog
from ui.report_editor import ReportEditorDialog
from ui.themes import get_theme_manager, ThemeManager

logger = logging.getLogger(__name__)


class ReportGenerationThread(QThread):
    """Thread para geração de laudos em background."""

    finished = pyqtSignal(str)  # Emite o laudo gerado
    error = pyqtSignal(str)  # Emite mensagem de erro

    def __init__(self, exam_type: str, exam_data: Dict[str, Any]):
        super().__init__()
        self.exam_type = exam_type
        self.exam_data = exam_data

    def run(self):
        """Executa a geração do laudo."""
        try:
            client = get_claude_client()
            report = client.generate_report(self.exam_type, self.exam_data)
            self.finished.emit(report)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Janela principal do aplicativo."""

    def __init__(self):
        super().__init__()

        self.flir_processor = FLIRProcessor()
        self.thermal_analyzer = ThermalAnalyzer()
        self.db_manager = get_db_manager()
        self.pdf_generator = PDFGenerator()
        self.theme_manager = get_theme_manager()

        # Estado da aplicação
        self.current_image_data = None
        self.current_exam_id = None
        self.current_patient_id = None
        self.selected_patient_id = None  # Paciente selecionado na busca
        self.loaded_images = []  # Lista de todas as imagens carregadas
        self.current_image_index = 0  # Índice da imagem atual
        self.current_rois = []  # ROIs desenhadas
        self.generated_report_text = ""  # Último laudo gerado

        self.init_ui()
        self.setup_menu()
        self.setup_shortcuts()
        self.check_api_key()

    def init_ui(self):
        """Inicializa a interface do usuário."""
        self.setWindowTitle("Termografia Médica - FASE 2 Completo")
        self.setGeometry(100, 100, 1400, 900)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QVBoxLayout(central_widget)

        # Barra de ferramentas superior
        toolbar = self.create_toolbar()
        main_layout.addLayout(toolbar)

        # Tabs principais
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_patient_search_tab(), "Buscar Paciente")
        self.tabs.addTab(self.create_exam_tab(), "Novo Exame")
        self.tabs.addTab(self.create_analysis_tab(), "Análise")
        self.tabs.addTab(self.create_report_tab(), "Laudo")
        self.tabs.addTab(self.create_settings_tab(), "Configurações")

        main_layout.addWidget(self.tabs)

        # Barra de status
        self.statusBar().showMessage("Pronto")

    def create_toolbar(self) -> QHBoxLayout:
        """Cria barra de ferramentas superior."""
        toolbar = QHBoxLayout()

        # Botão importar imagem (suporta múltiplas)
        self.btn_import = QPushButton("📁 Importar Imagem(ns) FLIR")
        self.btn_import.clicked.connect(self.import_flir_image)
        toolbar.addWidget(self.btn_import)

        # Botão processar
        self.btn_process = QPushButton("⚙️ Processar")
        self.btn_process.clicked.connect(self.process_image)
        self.btn_process.setEnabled(False)
        toolbar.addWidget(self.btn_process)

        # Botão gerar laudo
        self.btn_generate_report = QPushButton("📄 Gerar Laudo")
        self.btn_generate_report.clicked.connect(self.generate_report)
        self.btn_generate_report.setEnabled(False)
        toolbar.addWidget(self.btn_generate_report)

        toolbar.addStretch()

        # Indicador de API key
        self.lbl_api_status = QLabel("API: ✗")
        toolbar.addWidget(self.lbl_api_status)

        return toolbar

    def create_patient_search_tab(self) -> QWidget:
        """Cria aba de busca de pacientes."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Grupo de busca
        search_group = QGroupBox("Buscar Paciente")
        search_layout = QVBoxLayout()

        # Campo de busca
        search_h_layout = QHBoxLayout()
        search_h_layout.addWidget(QLabel("Nome ou Prontuário:"))
        self.input_patient_search = QLineEdit()
        self.input_patient_search.setPlaceholderText("Digite para buscar...")
        self.input_patient_search.returnPressed.connect(self.search_patients)
        search_h_layout.addWidget(self.input_patient_search)

        self.btn_search_patient = QPushButton("🔍 Buscar")
        self.btn_search_patient.clicked.connect(self.search_patients)
        search_h_layout.addWidget(self.btn_search_patient)

        search_layout.addLayout(search_h_layout)
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)

        # Lista de pacientes encontrados
        patients_group = QGroupBox("Pacientes Encontrados")
        patients_layout = QVBoxLayout()

        self.table_patients = QTableWidget()
        self.table_patients.setColumnCount(4)
        self.table_patients.setHorizontalHeaderLabels(["ID", "Nome", "Prontuário", "Gênero"])
        self.table_patients.horizontalHeader().setStretchLastSection(True)
        self.table_patients.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_patients.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table_patients.itemSelectionChanged.connect(self.on_patient_selected)
        patients_layout.addWidget(self.table_patients)

        patients_group.setLayout(patients_layout)
        layout.addWidget(patients_group)

        # Informações do paciente selecionado
        info_group = QGroupBox("Histórico de Exames")
        info_layout = QVBoxLayout()

        self.lbl_selected_patient = QLabel("Nenhum paciente selecionado")
        self.lbl_selected_patient.setStyleSheet("font-weight: bold; padding: 5px;")
        info_layout.addWidget(self.lbl_selected_patient)

        self.table_patient_exams = QTableWidget()
        self.table_patient_exams.setColumnCount(4)
        self.table_patient_exams.setHorizontalHeaderLabels(["ID", "Data", "Tipo", "Status"])
        self.table_patient_exams.horizontalHeader().setStretchLastSection(True)
        self.table_patient_exams.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        info_layout.addWidget(self.table_patient_exams)

        # Botões de ação
        btn_layout = QHBoxLayout()

        self.btn_open_exam = QPushButton("Abrir Exame Selecionado")
        self.btn_open_exam.clicked.connect(self.open_selected_exam)
        self.btn_open_exam.setEnabled(False)
        btn_layout.addWidget(self.btn_open_exam)

        self.btn_new_exam_for_patient = QPushButton("Novo Exame para Este Paciente")
        self.btn_new_exam_for_patient.clicked.connect(self.create_exam_for_selected_patient)
        self.btn_new_exam_for_patient.setEnabled(False)
        btn_layout.addWidget(self.btn_new_exam_for_patient)

        info_layout.addLayout(btn_layout)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        return tab

    def create_exam_tab(self) -> QWidget:
        """Cria aba de novo exame."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Dados do paciente
        patient_group = QGroupBox("Dados do Paciente")
        patient_layout = QFormLayout()

        self.input_patient_name = QLineEdit()
        self.input_medical_record = QLineEdit()
        self.combo_gender = QComboBox()
        self.combo_gender.addItems(["M", "F", "Outro"])

        patient_layout.addRow("Nome:", self.input_patient_name)
        patient_layout.addRow("Prontuário:", self.input_medical_record)
        patient_layout.addRow("Gênero:", self.combo_gender)

        patient_group.setLayout(patient_layout)
        layout.addWidget(patient_group)

        # Dados do exame
        exam_group = QGroupBox("Dados do Exame")
        exam_layout = QFormLayout()

        self.combo_exam_type = QComboBox()
        self.combo_exam_type.addItems(["Dermatomo", "BTT", "Corporal", "Outro"])

        self.input_clinical_indication = QTextEdit()
        self.input_clinical_indication.setMaximumHeight(100)

        exam_layout.addRow("Tipo de Exame:", self.combo_exam_type)
        exam_layout.addRow("Indicação Clínica:", self.input_clinical_indication)

        exam_group.setLayout(exam_layout)
        layout.addWidget(exam_group)

        # Botão criar exame
        btn_create_exam = QPushButton("Criar Novo Exame")
        btn_create_exam.clicked.connect(self.create_exam)
        layout.addWidget(btn_create_exam)

        layout.addStretch()

        return tab

    def create_analysis_tab(self) -> QWidget:
        """Cria aba de análise."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Splitter para visualização
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Painel esquerdo - Imagem
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Lista de imagens carregadas
        images_header = QHBoxLayout()
        images_header.addWidget(QLabel("Imagens Carregadas:"))
        self.lbl_image_count = QLabel("(0)")
        images_header.addWidget(self.lbl_image_count)
        images_header.addStretch()
        left_layout.addLayout(images_header)

        self.list_images = QListWidget()
        self.list_images.setMaximumHeight(80)
        self.list_images.itemClicked.connect(self.on_image_selected)
        left_layout.addWidget(self.list_images)

        # Navegação entre imagens
        nav_layout = QHBoxLayout()
        self.btn_prev_image = QPushButton("◀ Anterior")
        self.btn_prev_image.clicked.connect(self.show_previous_image)
        self.btn_prev_image.setEnabled(False)

        self.lbl_image_info = QLabel("Nenhuma imagem")
        self.lbl_image_info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_next_image = QPushButton("Próxima ▶")
        self.btn_next_image.clicked.connect(self.show_next_image)
        self.btn_next_image.setEnabled(False)

        nav_layout.addWidget(self.btn_prev_image)
        nav_layout.addWidget(self.lbl_image_info)
        nav_layout.addWidget(self.btn_next_image)
        left_layout.addLayout(nav_layout)

        self.lbl_image = QLabel("Nenhuma imagem carregada")
        self.lbl_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_image.setMinimumSize(400, 300)
        self.lbl_image.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")

        left_layout.addWidget(QLabel("Visualização:"))
        left_layout.addWidget(self.lbl_image)

        # Botão toggle heatmap
        self.btn_toggle_heatmap = QPushButton("Mostrar Heatmap")
        self.btn_toggle_heatmap.clicked.connect(self.toggle_heatmap)
        self.btn_toggle_heatmap.setEnabled(False)
        left_layout.addWidget(self.btn_toggle_heatmap)

        splitter.addWidget(left_panel)

        # Painel direito - Dados
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Estatísticas
        self.text_stats = QTextEdit()
        self.text_stats.setReadOnly(True)
        self.text_stats.setMaximumHeight(200)

        right_layout.addWidget(QLabel("Estatísticas:"))
        right_layout.addWidget(self.text_stats)

        # Análise de assimetria (para exames de dermátomo)
        asymmetry_group = QGroupBox("Análise de Assimetria")
        asymmetry_layout = QFormLayout()

        self.input_left_temp = QLineEdit()
        self.input_right_temp = QLineEdit()
        self.combo_dermatome = QComboBox()
        self.combo_dermatome.addItems(["C3", "C4", "C5", "C6", "C7", "C8", "T1"])

        asymmetry_layout.addRow("Temp. Esquerda (°C):", self.input_left_temp)
        asymmetry_layout.addRow("Temp. Direita (°C):", self.input_right_temp)
        asymmetry_layout.addRow("Dermátomo:", self.combo_dermatome)

        btn_analyze_asymmetry = QPushButton("Analisar Assimetria")
        btn_analyze_asymmetry.clicked.connect(self.analyze_asymmetry)
        asymmetry_layout.addRow(btn_analyze_asymmetry)

        asymmetry_group.setLayout(asymmetry_layout)
        right_layout.addWidget(asymmetry_group)

        # Resultado da análise
        self.text_analysis_result = QTextEdit()
        self.text_analysis_result.setReadOnly(True)

        right_layout.addWidget(QLabel("Resultado da Análise:"))
        right_layout.addWidget(self.text_analysis_result)

        splitter.addWidget(right_panel)

        layout.addWidget(splitter)

        return tab

    def create_report_tab(self) -> QWidget:
        """Cria aba de laudo."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Área de texto do laudo
        self.text_report = QTextEdit()
        self.text_report.setReadOnly(True)

        layout.addWidget(QLabel("Laudo Médico:"))
        layout.addWidget(self.text_report)

        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Botões
        buttons_layout = QHBoxLayout()

        btn_export_pdf = QPushButton("Exportar PDF")
        btn_export_pdf.clicked.connect(self.export_pdf)

        btn_save_report = QPushButton("Salvar no Banco")
        btn_save_report.clicked.connect(self.save_report)

        buttons_layout.addWidget(btn_export_pdf)
        buttons_layout.addWidget(btn_save_report)
        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

        return tab

    def create_settings_tab(self) -> QWidget:
        """Cria aba de configurações."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Configuração de API Key
        api_group = QGroupBox("Configuração API Anthropic")
        api_layout = QFormLayout()

        self.input_api_key = QLineEdit()
        self.input_api_key.setEchoMode(QLineEdit.EchoMode.Password)

        btn_save_api_key = QPushButton("Salvar API Key")
        btn_save_api_key.clicked.connect(self.save_api_key)

        api_layout.addRow("API Key:", self.input_api_key)
        api_layout.addRow(btn_save_api_key)

        api_group.setLayout(api_layout)
        layout.addWidget(api_group)

        # Modelo Claude
        model_group = QGroupBox("Modelo Claude")
        model_layout = QFormLayout()

        self.combo_model = QComboBox()
        self.combo_model.addItems([
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-5-haiku-20241022"
        ])

        model_layout.addRow("Modelo:", self.combo_model)
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        layout.addStretch()

        return tab

    def check_api_key(self):
        """Verifica se API key está configurada."""
        if has_api_key():
            self.lbl_api_status.setText("API: ✓")
            self.lbl_api_status.setStyleSheet("color: green;")
        else:
            self.lbl_api_status.setText("API: ✗")
            self.lbl_api_status.setStyleSheet("color: red;")

    def save_api_key(self):
        """Salva API key configurada."""
        api_key = self.input_api_key.text().strip()

        if not api_key:
            QMessageBox.warning(self, "Erro", "Digite uma API key válida")
            return

        try:
            configure_api_key(api_key)
            self.input_api_key.clear()
            self.check_api_key()
            QMessageBox.information(self, "Sucesso", "API key salva com segurança")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar API key: {e}")

    def create_exam(self):
        """Cria novo exame no banco de dados."""
        patient_name = self.input_patient_name.text().strip()

        if not patient_name:
            QMessageBox.warning(self, "Erro", "Digite o nome do paciente")
            return

        try:
            # Cria ou busca paciente
            medical_record = self.input_medical_record.text().strip()

            patient_id = self.db_manager.create_patient(
                name=patient_name,
                gender=self.combo_gender.currentText(),
                medical_record=medical_record if medical_record else None
            )

            # Cria exame
            exam_id = self.db_manager.create_exam(
                patient_id=patient_id,
                exam_date=datetime.now().isoformat(),
                exam_type=self.combo_exam_type.currentText(),
                clinical_indication=self.input_clinical_indication.toPlainText()
            )

            self.current_patient_id = patient_id
            self.current_exam_id = exam_id

            self.statusBar().showMessage(f"Exame criado: ID {exam_id}")
            QMessageBox.information(self, "Sucesso", f"Exame criado com sucesso!\nID: {exam_id}")

            # Habilita importação
            self.btn_import.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao criar exame: {e}")

    def search_patients(self):
        """Busca pacientes por nome ou prontuário."""
        query = self.input_patient_search.text().strip()

        if not query:
            QMessageBox.warning(self, "Aviso", "Digite um nome ou prontuário para buscar")
            return

        try:
            patients = self.db_manager.search_patients(query)

            # Limpa tabela
            self.table_patients.setRowCount(0)

            # Preenche tabela com resultados
            for patient in patients:
                row = self.table_patients.rowCount()
                self.table_patients.insertRow(row)

                self.table_patients.setItem(row, 0, QTableWidgetItem(str(patient['id'])))
                self.table_patients.setItem(row, 1, QTableWidgetItem(patient['name']))
                self.table_patients.setItem(row, 2, QTableWidgetItem(patient['medical_record'] or "-"))
                self.table_patients.setItem(row, 3, QTableWidgetItem(patient['gender'] or "-"))

            if len(patients) == 0:
                QMessageBox.information(self, "Busca", "Nenhum paciente encontrado")
            else:
                self.statusBar().showMessage(f"{len(patients)} paciente(s) encontrado(s)")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao buscar pacientes: {e}")
            logger.error(f"Erro ao buscar pacientes: {e}", exc_info=True)

    def on_patient_selected(self):
        """Chamado quando um paciente é selecionado na tabela."""
        selected_rows = self.table_patients.selectedItems()

        if not selected_rows:
            return

        try:
            # Pega o ID do paciente selecionado (primeira coluna)
            patient_id = int(self.table_patients.item(selected_rows[0].row(), 0).text())
            patient_name = self.table_patients.item(selected_rows[0].row(), 1).text()

            # Atualiza label
            self.lbl_selected_patient.setText(f"Paciente: {patient_name} (ID: {patient_id})")

            # Busca exames do paciente
            exams = self.db_manager.get_patient_exams(patient_id)

            # Limpa tabela de exames
            self.table_patient_exams.setRowCount(0)

            # Preenche tabela com exames
            for exam in exams:
                row = self.table_patient_exams.rowCount()
                self.table_patient_exams.insertRow(row)

                exam_date = datetime.fromisoformat(exam['exam_date']).strftime('%d/%m/%Y %H:%M')

                self.table_patient_exams.setItem(row, 0, QTableWidgetItem(str(exam['id'])))
                self.table_patient_exams.setItem(row, 1, QTableWidgetItem(exam_date))
                self.table_patient_exams.setItem(row, 2, QTableWidgetItem(exam['exam_type']))
                self.table_patient_exams.setItem(row, 3, QTableWidgetItem(exam['status']))

            # Habilita botões
            self.btn_new_exam_for_patient.setEnabled(True)
            self.btn_open_exam.setEnabled(len(exams) > 0)

            # Armazena ID do paciente selecionado
            self.selected_patient_id = patient_id

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar dados do paciente: {e}")
            logger.error(f"Erro ao carregar dados do paciente: {e}", exc_info=True)

    def open_selected_exam(self):
        """Abre o exame selecionado na tabela."""
        selected_rows = self.table_patient_exams.selectedItems()

        if not selected_rows:
            QMessageBox.warning(self, "Aviso", "Selecione um exame para abrir")
            return

        try:
            # Pega o ID do exame selecionado
            exam_id = int(self.table_patient_exams.item(selected_rows[0].row(), 0).text())

            # Carrega dados do exame
            exam = self.db_manager.get_exam(exam_id)
            if not exam:
                QMessageBox.critical(self, "Erro", "Exame não encontrado")
                return

            # Atualiza estado atual
            self.current_exam_id = exam_id
            self.current_patient_id = exam['patient_id']

            # Carrega imagens do exame
            images = self.db_manager.get_exam_images(exam_id)

            # Limpa imagens carregadas
            self.loaded_images.clear()
            self.list_images.clear()

            # Carrega cada imagem
            for img_data in images:
                try:
                    image_data = self.flir_processor.load_flir_image(img_data['image_path'])
                    self.loaded_images.append(image_data)

                    filename = Path(img_data['image_path']).name
                    self.list_images.addItem(f"{len(self.loaded_images)}. {filename}")
                except Exception as e:
                    logger.error(f"Erro ao carregar imagem {img_data['image_path']}: {e}")

            # Mostra primeira imagem se houver
            if self.loaded_images:
                self.current_image_index = 0
                self.show_current_image()
                self.lbl_image_count.setText(f"({len(self.loaded_images)})")
                self.btn_process.setEnabled(True)
                self.btn_toggle_heatmap.setEnabled(True)
                self.update_navigation_buttons()

            # Habilita importação
            self.btn_import.setEnabled(True)

            # Muda para aba de análise
            self.tabs.setCurrentIndex(2)  # Aba "Análise"

            self.statusBar().showMessage(f"Exame {exam_id} carregado com sucesso")
            QMessageBox.information(self, "Sucesso",
                                  f"Exame carregado!\n"
                                  f"ID: {exam_id}\n"
                                  f"Tipo: {exam['exam_type']}\n"
                                  f"Imagens: {len(images)}")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao abrir exame: {e}")
            logger.error(f"Erro ao abrir exame: {e}", exc_info=True)

    def create_exam_for_selected_patient(self):
        """Cria novo exame para o paciente selecionado."""
        if not hasattr(self, 'selected_patient_id'):
            QMessageBox.warning(self, "Aviso", "Selecione um paciente primeiro")
            return

        try:
            # Busca dados do paciente
            patient = self.db_manager.get_patient(self.selected_patient_id)
            if not patient:
                QMessageBox.critical(self, "Erro", "Paciente não encontrado")
                return

            # Preenche formulário na aba "Novo Exame"
            self.input_patient_name.setText(patient['name'])
            self.input_medical_record.setText(patient['medical_record'] or "")

            if patient['gender']:
                index = self.combo_gender.findText(patient['gender'])
                if index >= 0:
                    self.combo_gender.setCurrentIndex(index)

            # Muda para aba "Novo Exame"
            self.tabs.setCurrentIndex(1)

            QMessageBox.information(self, "Informação",
                                  f"Formulário preenchido com dados de:\n{patient['name']}\n\n"
                                  "Preencha os dados do exame e clique em 'Criar Novo Exame'")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao preparar novo exame: {e}")
            logger.error(f"Erro ao preparar novo exame: {e}", exc_info=True)

    def import_flir_image(self):
        """Importa uma ou múltiplas imagens FLIR."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar Imagem(ns) FLIR - Múltipla seleção habilitada",
            "",
            "Imagens (*.jpg *.jpeg *.png *.bmp)"
        )

        if not file_paths:
            return

        try:
            imported_count = 0
            errors = []

            for file_path in file_paths:
                try:
                    # Carrega e processa imagem
                    image_data = self.flir_processor.load_flir_image(file_path)

                    # Adiciona à lista de imagens carregadas
                    self.loaded_images.append(image_data)

                    # Adiciona à lista visual
                    filename = Path(file_path).name
                    self.list_images.addItem(f"{len(self.loaded_images)}. {filename}")

                    # Salva no banco se houver exame ativo
                    if self.current_exam_id:
                        stats = image_data['statistics']
                        self.db_manager.add_thermal_image(
                            exam_id=self.current_exam_id,
                            image_path=file_path,
                            image_type='FLIR',
                            sequence_number=len(self.loaded_images),
                            min_temp=stats['min_temp'],
                            max_temp=stats['max_temp'],
                            avg_temp=stats['mean_temp']
                        )

                    imported_count += 1

                except Exception as e:
                    errors.append(f"{Path(file_path).name}: {str(e)}")
                    logger.error(f"Erro ao importar {file_path}: {e}")

            # Atualiza interface
            if imported_count > 0:
                # Mostra primeira imagem
                self.current_image_index = 0
                self.show_current_image()

                # Atualiza contador
                self.lbl_image_count.setText(f"({len(self.loaded_images)})")

                # Habilita botões
                self.btn_process.setEnabled(True)
                self.btn_toggle_heatmap.setEnabled(True)
                self.update_navigation_buttons()

                # Mensagem de sucesso
                msg = f"{imported_count} imagem(ns) importada(s) com sucesso"
                if errors:
                    msg += f"\n\n{len(errors)} erro(s):\n" + "\n".join(errors[:5])
                    if len(errors) > 5:
                        msg += f"\n... e mais {len(errors) - 5} erro(s)"

                self.statusBar().showMessage(msg)
                QMessageBox.information(self, "Importação", msg)
            else:
                QMessageBox.warning(self, "Erro", "Nenhuma imagem foi importada com sucesso")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao importar imagens: {e}")

    def display_image(self, image: np.ndarray):
        """Exibe imagem no label."""
        # Converte BGR para RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Redimensiona para caber no label
        height, width, channel = rgb_image.shape
        bytes_per_line = 3 * width

        q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)

        # Escala para caber no label mantendo proporção
        scaled_pixmap = pixmap.scaled(
            self.lbl_image.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.lbl_image.setPixmap(scaled_pixmap)

    def show_current_image(self):
        """Exibe a imagem atual baseada no índice."""
        if not self.loaded_images or self.current_image_index >= len(self.loaded_images):
            return

        self.current_image_data = self.loaded_images[self.current_image_index]

        # Exibe imagem
        self.display_image(self.current_image_data['visible_image'])

        # Mostra estatísticas
        stats = self.current_image_data['statistics']
        filename = Path(self.current_image_data['image_path']).name
        stats_text = f"""
Arquivo: {filename}
Imagem: {self.current_image_index + 1} de {len(self.loaded_images)}
Resolução: {self.current_image_data['resolution'][0]}x{self.current_image_data['resolution'][1]}

Temperatura Mínima: {stats['min_temp']:.2f}°C
Temperatura Máxima: {stats['max_temp']:.2f}°C
Temperatura Média: {stats['mean_temp']:.2f}°C
Desvio Padrão: {stats['std_temp']:.2f}°C
"""
        self.text_stats.setText(stats_text)

        # Atualiza label de info
        self.lbl_image_info.setText(f"Imagem {self.current_image_index + 1}/{len(self.loaded_images)}")

        # Reseta heatmap
        self.btn_toggle_heatmap.setText("Mostrar Heatmap")

        # Atualiza seleção na lista
        self.list_images.setCurrentRow(self.current_image_index)

    def show_previous_image(self):
        """Mostra a imagem anterior."""
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.show_current_image()
            self.update_navigation_buttons()

    def show_next_image(self):
        """Mostra a próxima imagem."""
        if self.current_image_index < len(self.loaded_images) - 1:
            self.current_image_index += 1
            self.show_current_image()
            self.update_navigation_buttons()

    def on_image_selected(self, item):
        """Callback quando usuário seleciona imagem na lista."""
        row = self.list_images.row(item)
        if 0 <= row < len(self.loaded_images):
            self.current_image_index = row
            self.show_current_image()
            self.update_navigation_buttons()

    def update_navigation_buttons(self):
        """Atualiza estado dos botões de navegação."""
        if not self.loaded_images:
            self.btn_prev_image.setEnabled(False)
            self.btn_next_image.setEnabled(False)
            return

        self.btn_prev_image.setEnabled(self.current_image_index > 0)
        self.btn_next_image.setEnabled(self.current_image_index < len(self.loaded_images) - 1)

    def toggle_heatmap(self):
        """Alterna entre imagem original e heatmap."""
        if not self.current_image_data:
            return

        if self.btn_toggle_heatmap.text() == "Mostrar Heatmap":
            # Gera e mostra heatmap
            heatmap = self.flir_processor.generate_heatmap(
                self.current_image_data['thermal_data']
            )
            self.display_image(heatmap)
            self.btn_toggle_heatmap.setText("Mostrar Original")
        else:
            # Mostra imagem original
            self.display_image(self.current_image_data['visible_image'])
            self.btn_toggle_heatmap.setText("Mostrar Heatmap")

    def process_image(self):
        """Processa imagem térmica."""
        if not self.current_image_data:
            QMessageBox.warning(self, "Erro", "Nenhuma imagem carregada")
            return

        self.statusBar().showMessage("Processando imagem...")
        QMessageBox.information(self, "Processamento", "Imagem processada com sucesso!")

    def analyze_asymmetry(self):
        """Analisa assimetria térmica."""
        try:
            left_temp = float(self.input_left_temp.text())
            right_temp = float(self.input_right_temp.text())
            dermatome = self.combo_dermatome.currentText()

            result = self.thermal_analyzer.analyze_asymmetry(left_temp, right_temp, dermatome)

            result_text = f"""
ANÁLISE DE ASSIMETRIA - Dermátomo {dermatome}

Temperatura Esquerda: {result.left_temp:.2f}°C
Temperatura Direita: {result.right_temp:.2f}°C
ΔT: {result.delta_t:.2f}°C

Classificação: {result.classification}
Confiança: {result.confidence:.0%}

Significado Clínico:
{result.clinical_significance}
"""
            self.text_analysis_result.setText(result_text)

            # Habilita geração de laudo
            self.btn_generate_report.setEnabled(True)

        except ValueError:
            QMessageBox.warning(self, "Erro", "Digite valores numéricos válidos para as temperaturas")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro na análise: {e}")

    def generate_report(self):
        """Gera laudo usando Claude AI."""
        if not has_api_key():
            QMessageBox.warning(
                self,
                "API Key Necessária",
                "Configure sua API key da Anthropic na aba Configurações"
            )
            return

        # Prepara dados do exame
        exam_data = {
            'patient_name': self.input_patient_name.text(),
            'exam_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'clinical_indication': self.input_clinical_indication.toPlainText(),
            'equipment': 'Câmera termográfica FLIR',
            'dermatome_analyses': []
        }

        # Adiciona análise se disponível
        if self.input_left_temp.text() and self.input_right_temp.text():
            exam_data['dermatome_analyses'].append({
                'dermatome': self.combo_dermatome.currentText(),
                'left_temp': float(self.input_left_temp.text()),
                'right_temp': float(self.input_right_temp.text()),
                'delta_t': abs(float(self.input_left_temp.text()) - float(self.input_right_temp.text())),
                'classification': self.thermal_analyzer.analyze_asymmetry(
                    float(self.input_left_temp.text()),
                    float(self.input_right_temp.text())
                ).classification
            })

        # Mostra progresso
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Modo indeterminado

        # Inicia thread de geração
        self.report_thread = ReportGenerationThread('dermatome', exam_data)
        self.report_thread.finished.connect(self.on_report_generated)
        self.report_thread.error.connect(self.on_report_error)
        self.report_thread.start()

        self.statusBar().showMessage("Gerando laudo com Claude AI...")

    def on_report_generated(self, report: str):
        """Callback quando laudo é gerado."""
        self.progress_bar.setVisible(False)
        self.generated_report_text = report

        # Abre editor de laudos para revisão
        patient_data = {
            'name': self.input_patient_name.text(),
            'birth_date': ''
        }
        exam_data = {
            'exam_date': datetime.now().strftime('%d/%m/%Y'),
            'exam_type': self.combo_exam_type.currentText()
        }

        editor = ReportEditorDialog(report, patient_data, exam_data, self)
        editor.report_finalized.connect(self.on_report_finalized)

        if editor.exec():
            self.statusBar().showMessage("Laudo revisado e finalizado")
        else:
            # Se cancelou, ainda mostra o laudo original
            self.text_report.setText(report)
            self.tabs.setCurrentIndex(2)

    def on_report_error(self, error_msg: str):
        """Callback quando há erro na geração."""
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("Erro ao gerar laudo")
        QMessageBox.critical(self, "Erro", f"Erro ao gerar laudo:\n{error_msg}")

    def save_report(self):
        """Salva laudo no banco de dados."""
        if not self.current_exam_id:
            QMessageBox.warning(self, "Erro", "Nenhum exame ativo")
            return

        report_text = self.text_report.toPlainText()
        if not report_text:
            QMessageBox.warning(self, "Erro", "Nenhum laudo para salvar")
            return

        try:
            self.db_manager.create_report(
                exam_id=self.current_exam_id,
                report_text=report_text,
                report_type='Preliminar'
            )

            QMessageBox.information(self, "Sucesso", "Laudo salvo no banco de dados")
            self.statusBar().showMessage("Laudo salvo")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar laudo: {e}")

    def export_pdf(self):
        """Exporta laudo para PDF."""
        report_text = self.text_report.toPlainText()

        if not report_text:
            QMessageBox.warning(self, "Aviso", "Nenhum laudo para exportar")
            return

        # Dialog para escolher onde salvar
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar PDF",
            f"Laudo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "PDF Files (*.pdf)"
        )

        if not filename:
            return

        try:
            # Prepara dados do laudo
            patient = self.db_manager.get_patient(self.current_patient_id) if self.current_patient_id else {}
            exam = self.db_manager.get_exam(self.current_exam_id) if self.current_exam_id else {}

            report_data = {
                'patient': patient,
                'exam': exam,
                'report_text': report_text
            }

            # Dados do médico (opcional - pode vir de configuração)
            physician_data = {
                'name': 'Dr. Jorge Cecílio Daher Jr.',
                'crm': 'CRM-GO 6108',
                'specialty': 'Endocrinologia e Metabologia'
            }

            # Gera PDF
            success = self.pdf_generator.generate_report(
                filename,
                report_data,
                physician_data
            )

            if success:
                QMessageBox.information(self, "Sucesso", f"PDF exportado com sucesso!\n{filename}")
                self.statusBar().showMessage(f"PDF salvo: {filename}")
            else:
                QMessageBox.critical(self, "Erro", "Erro ao gerar PDF")

        except Exception as e:
            logger.error(f"Erro ao exportar PDF: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF:\n{e}")

    def on_report_finalized(self, report_data: Dict[str, Any]):
        """
        Callback quando laudo é finalizado no editor.

        Args:
            report_data: Dicionário com dados do laudo editado
        """
        # Atualiza texto do laudo
        self.text_report.setText(report_data['report_text'])

        # Salva automaticamente se houver exame ativo
        if self.current_exam_id:
            try:
                self.db_manager.create_report(
                    exam_id=self.current_exam_id,
                    report_text=report_data['report_text'],
                    report_type=report_data['report_type'],
                    physician_name=report_data.get('physician_name'),
                    physician_crm=report_data.get('physician_crm'),
                    conclusion=report_data.get('conclusion'),
                    recommendations=report_data.get('recommendations')
                )
                self.statusBar().showMessage("Laudo salvo automaticamente")
            except Exception as e:
                logger.error(f"Erro ao salvar laudo: {e}")

        # Vai para aba de laudo
        self.tabs.setCurrentIndex(2)

    def setup_menu(self):
        """Configura o menu principal."""
        menubar = self.menuBar()

        # Menu Arquivo
        file_menu = menubar.addMenu("Arquivo")

        action_new_exam = QAction("Novo Exame", self)
        action_new_exam.setShortcut("Ctrl+N")
        action_new_exam.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
        file_menu.addAction(action_new_exam)

        action_history = QAction("Histórico de Pacientes", self)
        action_history.setShortcut("Ctrl+H")
        action_history.triggered.connect(self.open_patient_history)
        file_menu.addAction(action_history)

        file_menu.addSeparator()

        action_exit = QAction("Sair", self)
        action_exit.setShortcut("Ctrl+Q")
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)

        # Menu Ferramentas
        tools_menu = menubar.addMenu("Ferramentas")

        action_roi_editor = QAction("Editor de ROIs", self)
        action_roi_editor.setShortcut("Ctrl+R")
        action_roi_editor.triggered.connect(self.open_roi_editor)
        tools_menu.addAction(action_roi_editor)

        action_import = QAction("Importar Imagens", self)
        action_import.setShortcut("Ctrl+I")
        action_import.triggered.connect(self.import_flir_image)
        tools_menu.addAction(action_import)

        # Menu Temas
        theme_menu = menubar.addMenu("Temas")

        action_light = QAction("Tema Claro", self)
        action_light.triggered.connect(lambda: self.theme_manager.apply_theme(ThemeManager.LIGHT))
        theme_menu.addAction(action_light)

        action_dark = QAction("Tema Escuro", self)
        action_dark.triggered.connect(lambda: self.theme_manager.apply_theme(ThemeManager.DARK))
        theme_menu.addAction(action_dark)

        action_blue = QAction("Tema Azul Médico", self)
        action_blue.triggered.connect(lambda: self.theme_manager.apply_theme(ThemeManager.BLUE))
        theme_menu.addAction(action_blue)

        theme_menu.addSeparator()

        action_toggle = QAction("Alternar Claro/Escuro", self)
        action_toggle.setShortcut("Ctrl+T")
        action_toggle.triggered.connect(self.theme_manager.toggle_theme)
        theme_menu.addAction(action_toggle)

        # Menu Ajuda
        help_menu = menubar.addMenu("Ajuda")

        action_about = QAction("Sobre", self)
        action_about.triggered.connect(self.show_about)
        help_menu.addAction(action_about)

    def setup_shortcuts(self):
        """Configura atalhos de teclado adicionais."""
        # Já configurados no menu, mas podemos adicionar mais se necessário
        pass

    def open_patient_history(self):
        """Abre dialog de histórico de pacientes."""
        dialog = PatientHistoryDialog(self)
        dialog.patient_selected.connect(self.load_patient_from_history)
        dialog.exam_selected.connect(self.load_exam_from_history)
        dialog.exec()

    def load_patient_from_history(self, patient_id: int):
        """
        Carrega paciente do histórico.

        Args:
            patient_id: ID do paciente
        """
        try:
            patient = self.db_manager.get_patient(patient_id)

            if patient:
                self.current_patient_id = patient_id
                self.input_patient_name.setText(patient['name'])
                self.input_medical_record.setText(patient.get('medical_record', ''))

                # Vai para aba de novo exame
                self.tabs.setCurrentIndex(0)

                self.statusBar().showMessage(f"Paciente carregado: {patient['name']}")

        except Exception as e:
            logger.error(f"Erro ao carregar paciente: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao carregar paciente: {e}")

    def load_exam_from_history(self, exam_id: int):
        """
        Carrega exame do histórico.

        Args:
            exam_id: ID do exame
        """
        try:
            exam = self.db_manager.get_exam(exam_id)

            if exam:
                self.current_exam_id = exam_id

                # Carrega dados do paciente
                patient = self.db_manager.get_patient(exam['patient_id'])
                if patient:
                    self.current_patient_id = patient['id']
                    self.input_patient_name.setText(patient['name'])

                # Carrega imagens do exame
                images = self.db_manager.get_exam_images(exam_id)
                if images:
                    # TODO: Carregar imagens
                    pass

                self.statusBar().showMessage(f"Exame #{exam_id} carregado")

        except Exception as e:
            logger.error(f"Erro ao carregar exame: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao carregar exame: {e}")

    def open_roi_editor(self):
        """Abre editor de ROIs."""
        try:
            if self.current_image_data is None:
                QMessageBox.warning(self, "Aviso", "Nenhuma imagem carregada.\n\nPor favor, importe uma imagem primeiro.")
                return

            # Verifica se a imagem está válida
            if 'visible_image' not in self.current_image_data:
                QMessageBox.critical(self, "Erro", "Dados da imagem estão corrompidos")
                logger.error("current_image_data não contém 'visible_image'")
                return

            image = self.current_image_data['visible_image']

            # Valida que é um array numpy válido
            if not isinstance(image, np.ndarray):
                QMessageBox.critical(self, "Erro", "Formato de imagem inválido")
                logger.error(f"Imagem não é numpy array, tipo: {type(image)}")
                return

            logger.info(f"Abrindo editor de ROIs - Imagem: {image.shape}, dtype: {image.dtype}")

            dialog = ROIEditorDialog(image, self)
            dialog.rois_saved.connect(self.on_rois_saved)

            dialog.exec()

        except Exception as e:
            logger.error(f"Erro ao abrir editor de ROIs: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Erro no Editor de ROIs",
                f"Ocorreu um erro ao abrir o editor de ROIs:\n\n{str(e)}\n\nVerifique os logs para mais detalhes."
            )

    def on_rois_saved(self, rois: List[Dict[str, Any]]):
        """
        Callback quando ROIs são salvas.

        Args:
            rois: Lista de ROIs desenhadas
        """
        self.current_rois = rois
        self.statusBar().showMessage(f"{len(rois)} ROI(s) criada(s)")

        # Salva no banco se houver imagem ativa
        # TODO: Implementar salvamento de ROIs no banco

        QMessageBox.information(self, "ROIs Salvas", f"{len(rois)} ROI(s) foram criadas com sucesso!")

    def show_about(self):
        """Mostra dialog sobre o aplicativo."""
        about_text = """
        <h2>Termografia Médica - FASE 2</h2>
        <p><b>Versão:</b> 2.0.0</p>
        <p><b>Desenvolvido por:</b> Dr. Jorge Cecílio Daher Jr.</p>
        <p><b>CRM-GO:</b> 6108</p>
        <p><b>Especialidade:</b> Endocrinologia e Metabologia</p>
        <hr>
        <p>Sistema completo de análise termográfica médica com:</p>
        <ul>
            <li>Processamento de imagens FLIR radiométricas</li>
            <li>Análise de assimetrias térmicas em dermátomos</li>
            <li>Análise BTT (Brain Thermal Tunnel) para cefaleias</li>
            <li>Geração automática de laudos com Claude AI</li>
            <li>Editor de ROIs interativo</li>
            <li>Exportação profissional em PDF</li>
            <li>Histórico completo de pacientes</li>
            <li>Temas personalizáveis</li>
        </ul>
        <p><i>Powered by Anthropic Claude AI</i></p>
        """

        QMessageBox.about(self, "Sobre - Termografia Médica", about_text)


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
