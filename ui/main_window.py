"""
Interface principal do aplicativo de termografia médica.
Janela principal PyQt6 com funcionalidades de importação, análise e geração de laudos.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QTextEdit, QTabWidget, QGroupBox,
    QLineEdit, QComboBox, QSpinBox, QMessageBox, QProgressBar,
    QTableWidget, QTableWidgetItem, QSplitter, QFormLayout, QListWidget,
    QMenu, QMenuBar, QProgressDialog
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
from core.hotspot_detector import HotspotDetector
from database.db_manager import get_db_manager
from api.claude_client import get_claude_client, has_api_key, configure_api_key
from reports.pdf_generator import PDFGenerator
from ui.roi_editor import ROIEditorDialog
from ui.patient_history import PatientHistoryDialog
from ui.report_editor import ReportEditorDialog
from ui.themes import get_theme_manager, ThemeManager

logger = logging.getLogger(__name__)

# Import FLIR modules (with error handling)
try:
    from core.flir_html_parser import parse_flir_html
    from core.flir_validator import FLIRValidator
    FLIR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"FLIR modules not available: {e}")
    FLIR_AVAILABLE = False


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
        self.batch_results = []  # Resultados do processamento em lote

        # Estado FLIR HTML import
        self.flir_html_path = None  # Caminho para HTML FLIR importado
        self.flir_data = None  # Dados parseados do FLIR
        self.flir_validation_report = None  # Último relatório de validação

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

        # Botão importar FLIR HTML
        self.btn_import_flir_html = QPushButton("📥 Importar FLIR HTML")
        self.btn_import_flir_html.clicked.connect(self.import_flir_html)
        self.btn_import_flir_html.setToolTip("Importa medições de referência do FLIR Thermal Studio")
        toolbar.addWidget(self.btn_import_flir_html)

        # Botão processar
        self.btn_process = QPushButton("⚙️ Processar Atual")
        self.btn_process.clicked.connect(self.process_image)
        self.btn_process.setEnabled(False)
        toolbar.addWidget(self.btn_process)

        # Botão processar todas
        self.btn_process_all = QPushButton("⚙️ Processar Todas")
        self.btn_process_all.clicked.connect(self.process_all_images)
        self.btn_process_all.setEnabled(False)
        toolbar.addWidget(self.btn_process_all)

        # Botão processar todas com detecção automática
        self.btn_process_all_auto = QPushButton("🔥 Processar Todas (Auto)")
        self.btn_process_all_auto.clicked.connect(self.process_all_images_auto)
        self.btn_process_all_auto.setEnabled(False)
        self.btn_process_all_auto.setToolTip("Detecta automaticamente pontos quentes sem precisar desenhar ROIs")
        toolbar.addWidget(self.btn_process_all_auto)

        # Botão gerar laudo
        self.btn_generate_report = QPushButton("📄 Gerar Laudo")
        self.btn_generate_report.clicked.connect(self.generate_report)
        self.btn_generate_report.setEnabled(False)
        toolbar.addWidget(self.btn_generate_report)

        toolbar.addStretch()

        # Indicador de validação FLIR
        self.lbl_flir_status = QLabel("FLIR: ✗")
        self.lbl_flir_status.setToolTip("Status de validação FLIR")
        toolbar.addWidget(self.lbl_flir_status)

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
                # Habilita processamento em lote se houver múltiplas imagens
                self.btn_process_all.setEnabled(len(self.loaded_images) > 1)
                self.btn_process_all_auto.setEnabled(len(self.loaded_images) > 1)
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
                # Habilita processamento em lote se houver múltiplas imagens
                self.btn_process_all.setEnabled(len(self.loaded_images) > 1)
                self.btn_process_all_auto.setEnabled(len(self.loaded_images) > 1)
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
        """Processa imagem térmica e ROIs automaticamente."""
        if not self.current_image_data:
            QMessageBox.warning(self, "Erro", "Nenhuma imagem carregada.\n\nImporte uma imagem FLIR primeiro.")
            return

        try:
            self.statusBar().showMessage("Processando imagem e ROIs...")
            logger.info("=== Iniciando processamento de imagem ===")

            # Se houver ROIs salvas, processar
            if self.current_rois and len(self.current_rois) > 0:
                logger.info(f"Processando {len(self.current_rois)} ROIs")

                thermal_data = self.current_image_data.get('thermal_data')

                if thermal_data is None:
                    logger.warning("thermal_data é None - não é possível processar ROIs")
                    QMessageBox.warning(self, "Aviso",
                        "Dados térmicos não disponíveis para processar ROIs.\n\n"
                        "A imagem pode não conter informações de temperatura incorporadas.\n"
                        "Tente importar uma imagem FLIR com dados térmicos.")
                    self.btn_generate_report.setEnabled(False)
                    self.statusBar().showMessage("Erro: Sem dados térmicos")
                    return

                logger.info(f"Dados térmicos: shape={thermal_data.shape}, dtype={thermal_data.dtype}")

                # Pega o tamanho da imagem visível usada para desenhar ROIs
                visible_image = self.current_image_data.get('visible_image')
                if visible_image is not None:
                    visible_h, visible_w = visible_image.shape[:2]
                    thermal_h, thermal_w = thermal_data.shape[:2]
                    logger.info(f"Imagem visível: {visible_w}x{visible_h}, Dados térmicos: {thermal_w}x{thermal_h}")

                    # Calcula fatores de escala
                    scale_x = thermal_w / visible_w
                    scale_y = thermal_h / visible_h
                    logger.info(f"Fatores de escala: x={scale_x:.4f}, y={scale_y:.4f}")
                else:
                    scale_x = scale_y = 1.0
                    logger.warning("Imagem visível não disponível, usando escala 1:1")

                # Calcular temperaturas de cada ROI
                roi_temps = {}
                import cv2

                for roi in self.current_rois:
                    name = roi['name']
                    # ROIs vêm com 'coordinates' do ROI Editor
                    points = roi.get('coordinates', roi.get('points', []))

                    if not points:
                        logger.warning(f"ROI '{name}' não tem coordenadas válidas")
                        continue

                    logger.info(f"Processando ROI '{name}' com {len(points)} pontos")

                    # Escala as coordenadas para o tamanho dos dados térmicos
                    scaled_points = [(int(x * scale_x), int(y * scale_y)) for x, y in points]
                    logger.info(f"  Coords originais: {points[0]}, Escaladas: {scaled_points[0]}")

                    # Verificar se os pontos estão dentro dos limites
                    thermal_h, thermal_w = thermal_data.shape[:2]
                    out_of_bounds = []
                    for i, (x, y) in enumerate(scaled_points):
                        if x < 0 or x >= thermal_w or y < 0 or y >= thermal_h:
                            out_of_bounds.append(f"ponto[{i}]=({x},{y})")

                    if out_of_bounds:
                        logger.warning(f"  ⚠️ ROI '{name}': Pontos fora dos limites [{thermal_w}x{thermal_h}]: {', '.join(out_of_bounds)}")
                        # Cortar pontos para ficarem dentro dos limites
                        scaled_points = [(max(0, min(x, thermal_w-1)), max(0, min(y, thermal_h-1))) for x, y in scaled_points]
                        logger.info(f"  Pontos corrigidos: {scaled_points}")

                    # Criar máscara para o ROI
                    mask = np.zeros(thermal_data.shape[:2], dtype=np.uint8)
                    pts = np.array(scaled_points, dtype=np.int32)
                    cv2.fillPoly(mask, [pts], 255)

                    # Calcular temperatura média na ROI
                    roi_region = thermal_data[mask == 255]
                    if len(roi_region) > 0:
                        avg_temp = np.mean(roi_region)
                        roi_temps[name] = avg_temp
                        logger.info(f"  ✅ ROI '{name}': {avg_temp:.2f}°C ({len(roi_region)} pixels)")
                    else:
                        logger.warning(f"  ❌ ROI '{name}' não capturou nenhum pixel (pontos: {scaled_points[:3]}...)")

                # Tentar identificar ROIs esquerda/direita automaticamente
                left_temp = None
                right_temp = None

                for name, temp in roi_temps.items():
                    name_lower = name.lower()
                    if 'esq' in name_lower or 'left' in name_lower or 'e' == name_lower[-1]:
                        left_temp = temp
                    elif 'dir' in name_lower or 'right' in name_lower or 'd' == name_lower[-1]:
                        right_temp = temp

                # Auto-preencher campos se encontrou ambos os lados
                if left_temp is not None and right_temp is not None:
                    self.input_left_temp.setText(f"{left_temp:.2f}")
                    self.input_right_temp.setText(f"{right_temp:.2f}")

                    # Calcular assimetria automaticamente
                    self.analyze_asymmetry()

                    QMessageBox.information(self, "Processamento Completo",
                        f"ROIs processadas com sucesso!\n\n"
                        f"📊 Temperaturas detectadas:\n"
                        f"• Esquerda: {left_temp:.2f}°C\n"
                        f"• Direita: {right_temp:.2f}°C\n\n"
                        f"ΔT calculado automaticamente.\n"
                        f"Verifique o resultado abaixo.")
                else:
                    # Mostrar temperaturas encontradas
                    roi_summary = "\n".join([f"• {name}: {temp:.2f}°C" for name, temp in roi_temps.items()])
                    QMessageBox.information(self, "ROIs Processadas",
                        f"Temperaturas calculadas:\n\n{roi_summary}\n\n"
                        f"💡 Dica: Nomeie as ROIs com 'Esquerdo/Direito' ou 'Esq/Dir' "
                        f"para preenchimento automático dos campos.")

            else:
                # Sem ROIs, apenas mostrar que está pronto
                QMessageBox.information(self, "Processamento",
                    "Imagem processada!\n\n"
                    "💡 Para análise de assimetria:\n"
                    "1. Use Editor de ROIs (Ferramentas > Editor de ROIs)\n"
                    "2. Desenhe ROIs nas regiões de interesse\n"
                    "3. Nomeie como 'Esquerdo' e 'Direito'\n"
                    "4. Clique em Processar novamente\n\n"
                    "Ou digite as temperaturas manualmente abaixo.")

            # Habilita geração de laudo
            self.btn_generate_report.setEnabled(True)
            self.statusBar().showMessage("Processamento concluído")

        except Exception as e:
            logger.error(f"Erro ao processar imagem: {e}", exc_info=True)
            QMessageBox.critical(self, "Erro", f"Erro ao processar: {e}")

    def process_all_images(self):
        """Processa todas as imagens carregadas em lote."""
        if not self.loaded_images or len(self.loaded_images) < 2:
            QMessageBox.warning(self, "Aviso", "Carregue múltiplas imagens para processamento em lote")
            return

        try:
            # Pergunta se quer usar as mesmas ROIs para todas as imagens
            reply = QMessageBox.question(self, "Processamento em Lote",
                f"Você tem {len(self.loaded_images)} imagens carregadas.\n\n"
                f"Deseja usar as mesmas ROIs em todas as imagens?\n\n"
                f"• SIM: As ROIs atuais serão aplicadas a todas\n"
                f"• NÃO: Cada imagem processará suas próprias ROIs (se houver)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)

            if reply == QMessageBox.StandardButton.Cancel:
                return

            use_same_rois = (reply == QMessageBox.StandardButton.Yes)

            # Se não há ROIs e usuário escolheu usar mesmas ROIs
            if use_same_rois and not self.current_rois:
                QMessageBox.warning(self, "Aviso",
                    "Nenhuma ROI definida!\n\n"
                    "Por favor:\n"
                    "1. Abra o Editor de ROIs (Ferramentas > Editor de ROIs)\n"
                    "2. Desenhe as ROIs\n"
                    "3. Salve\n"
                    "4. Execute 'Processar Todas' novamente")
                return

            # Cria dialog de progresso
            progress = QProgressDialog("Processando imagens...", "Cancelar", 0, len(self.loaded_images), self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)

            # Salva ROIs de template se necessário
            template_rois = self.current_rois.copy() if use_same_rois else None

            # Resultados consolidados
            all_results = []
            successful = 0
            failed = 0

            # Processa cada imagem
            for idx, image_data in enumerate(self.loaded_images):
                if progress.wasCanceled():
                    break

                progress.setValue(idx)
                progress.setLabelText(f"Processando imagem {idx + 1} de {len(self.loaded_images)}...")

                try:
                    # Se usar mesmas ROIs, aplicar template
                    if use_same_rois:
                        rois = template_rois
                    else:
                        # Usar ROIs específicas da imagem (se houver)
                        rois = image_data.get('rois', [])

                    # Processar ROIs se houver
                    if rois:
                        thermal_data = image_data.get('thermal_data')
                        if thermal_data is not None:
                            # Calcula fatores de escala para esta imagem
                            visible_image = image_data.get('visible_image')
                            if visible_image is not None:
                                visible_h, visible_w = visible_image.shape[:2]
                                thermal_h, thermal_w = thermal_data.shape[:2]
                                scale_x = thermal_w / visible_w
                                scale_y = thermal_h / visible_h
                            else:
                                scale_x = scale_y = 1.0

                            roi_temps = {}
                            for roi in rois:
                                name = roi['name']
                                # ROIs vêm com 'coordinates' do ROI Editor
                                points = roi.get('coordinates', roi.get('points', []))

                                if not points:
                                    continue

                                # Escala as coordenadas para o tamanho dos dados térmicos
                                scaled_points = [(int(x * scale_x), int(y * scale_y)) for x, y in points]

                                # Verificar se os pontos estão dentro dos limites
                                thermal_h, thermal_w = thermal_data.shape[:2]
                                out_of_bounds = []
                                for i, (x, y) in enumerate(scaled_points):
                                    if x < 0 or x >= thermal_w or y < 0 or y >= thermal_h:
                                        out_of_bounds.append(f"ponto[{i}]=({x},{y})")

                                if out_of_bounds:
                                    logger.warning(f"  Imagem {idx+1}, ROI '{name}': Pontos fora dos limites [{thermal_w}x{thermal_h}]: {', '.join(out_of_bounds)}")
                                    # Cortar pontos para ficarem dentro dos limites
                                    scaled_points = [(max(0, min(x, thermal_w-1)), max(0, min(y, thermal_h-1))) for x, y in scaled_points]

                                # Criar máscara
                                import cv2
                                mask = np.zeros(thermal_data.shape[:2], dtype=np.uint8)
                                pts = np.array(scaled_points, dtype=np.int32)
                                cv2.fillPoly(mask, [pts], 255)

                                # Calcular temperatura média
                                roi_region = thermal_data[mask == 255]
                                if len(roi_region) > 0:
                                    roi_temps[name] = np.mean(roi_region)
                                else:
                                    logger.warning(f"  Imagem {idx+1}, ROI '{name}': Máscara não capturou pixels (pontos escalados: {scaled_points[:3]}...)")

                            # Tentar identificar esquerda/direita
                            left_temp = None
                            right_temp = None
                            for name, temp in roi_temps.items():
                                name_lower = name.lower()
                                if 'esq' in name_lower or 'left' in name_lower or 'e' == name_lower[-1]:
                                    left_temp = temp
                                elif 'dir' in name_lower or 'right' in name_lower or 'd' == name_lower[-1]:
                                    right_temp = temp

                            # Se encontrou ambos, calcular assimetria
                            if left_temp is not None and right_temp is not None:
                                result = self.thermal_analyzer.analyze_asymmetry(
                                    left_temp, right_temp,
                                    self.combo_dermatome.currentText()
                                )

                                all_results.append({
                                    'image_index': idx + 1,
                                    'image_name': Path(image_data.get('image_path', f'Imagem {idx+1}')).name,
                                    'left_temp': left_temp,
                                    'right_temp': right_temp,
                                    'delta_t': result.delta_t,
                                    'classification': result.classification,
                                    'clinical_significance': result.clinical_significance
                                })
                                successful += 1
                            else:
                                logger.warning(f"Imagem {idx+1}: Não foi possível identificar ROIs esquerda/direita")
                                failed += 1
                        else:
                            logger.warning(f"Imagem {idx+1}: Sem dados térmicos")
                            failed += 1
                    else:
                        logger.warning(f"Imagem {idx+1}: Sem ROIs")
                        failed += 1

                except Exception as e:
                    logger.error(f"Erro ao processar imagem {idx+1}: {e}")
                    failed += 1

            progress.setValue(len(self.loaded_images))

            # Mostra resultados consolidados
            if all_results:
                result_summary = f"✅ Processamento em Lote Concluído!\n\n"
                result_summary += f"Total de imagens: {len(self.loaded_images)}\n"
                result_summary += f"Processadas com sucesso: {successful}\n"
                result_summary += f"Falhas: {failed}\n\n"
                result_summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

                # Estatísticas gerais
                avg_delta_t = np.mean([r['delta_t'] for r in all_results])
                max_delta_t = np.max([r['delta_t'] for r in all_results])
                min_delta_t = np.min([r['delta_t'] for r in all_results])

                result_summary += f"📊 Estatísticas Gerais:\n"
                result_summary += f"ΔT Médio: {avg_delta_t:.2f}°C\n"
                result_summary += f"ΔT Máximo: {max_delta_t:.2f}°C\n"
                result_summary += f"ΔT Mínimo: {min_delta_t:.2f}°C\n\n"

                # Distribuição de classificações
                classifications = {}
                for r in all_results:
                    cls = r['classification']
                    classifications[cls] = classifications.get(cls, 0) + 1

                result_summary += f"📈 Distribuição de Classificações:\n"
                for cls, count in classifications.items():
                    percentage = (count / len(all_results)) * 100
                    result_summary += f"• {cls}: {count} ({percentage:.1f}%)\n"

                result_summary += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                result_summary += f"\n💡 Próximo passo: Clique em 'Gerar Laudo' para\n"
                result_summary += f"criar um relatório consolidado de todas as imagens!"

                # Salva resultados para usar no laudo
                self.batch_results = all_results

                # Mostra resumo
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Processamento em Lote")
                msg_box.setText(result_summary)
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.exec()

                # Habilita geração de laudo
                self.btn_generate_report.setEnabled(True)
                self.statusBar().showMessage(f"Processamento em lote concluído: {successful}/{len(self.loaded_images)}")

            else:
                QMessageBox.warning(self, "Processamento em Lote",
                    f"Nenhuma imagem foi processada com sucesso.\n\n"
                    f"Certifique-se de que:\n"
                    f"• As ROIs estão nomeadas como 'Esquerdo'/'Direito' ou 'Esq'/'Dir'\n"
                    f"• As imagens têm dados térmicos válidos")

        except Exception as e:
            logger.error(f"Erro no processamento em lote: {e}", exc_info=True)
            QMessageBox.critical(self, "Erro", f"Erro no processamento em lote: {e}")

    def process_all_images_auto(self):
        """
        Processa todas as imagens em lote com detecção automática de pontos quentes.
        Não requer desenho manual de ROIs.
        """
        if not self.loaded_images or len(self.loaded_images) < 2:
            QMessageBox.warning(self, "Aviso", "Carregue múltiplas imagens para processamento em lote")
            return

        try:
            # Pergunta configurações de detecção
            reply = QMessageBox.question(
                self,
                "Processamento Automático",
                f"🔥 DETECÇÃO AUTOMÁTICA DE PONTOS QUENTES\n\n"
                f"Você tem {len(self.loaded_images)} imagens carregadas.\n\n"
                f"Este modo detecta automaticamente as regiões mais quentes\n"
                f"em cada imagem SEM precisar desenhar ROIs manualmente.\n\n"
                f"O algoritmo vai:\n"
                f"• Identificar as 2 regiões mais quentes automaticamente\n"
                f"• Classificar como esquerda/direita pela posição\n"
                f"• Calcular temperaturas e assimetria\n\n"
                f"Continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                return

            # Criar detector de hotspots
            hotspot_detector = HotspotDetector(
                percentile_threshold=80.0,  # Top 20% mais quente
                min_region_size=100,        # Mínimo 100 pixels
                max_regions=2               # Detectar 2 regiões (esq/dir)
            )

            # Cria dialog de progresso
            progress = QProgressDialog(
                "Detectando pontos quentes automaticamente...",
                "Cancelar",
                0,
                len(self.loaded_images),
                self
            )
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)

            # Resultados consolidados
            all_results = []
            successful = 0
            failed = 0

            # Processa cada imagem
            for idx, image_data in enumerate(self.loaded_images):
                if progress.wasCanceled():
                    break

                progress.setValue(idx)
                image_name = Path(image_data.get('image_path', f'Imagem {idx+1}')).name
                progress.setLabelText(f"Processando {image_name}...\n({idx + 1}/{len(self.loaded_images)})")

                try:
                    thermal_data = image_data.get('thermal_data')

                    if thermal_data is None:
                        logger.warning(f"Imagem {idx+1}: Sem dados térmicos")
                        failed += 1
                        continue

                    # Detectar hotspots automaticamente
                    logger.info(f"\n{'='*60}")
                    logger.info(f"Imagem {idx+1}: {image_name}")

                    temp_left, temp_right = hotspot_detector.detect_left_right_hotspots(
                        thermal_data,
                        method='percentile'
                    )

                    # Se detectou ambas as regiões
                    if temp_left is not None and temp_right is not None:
                        # Calcular assimetria
                        result = self.thermal_analyzer.analyze_asymmetry(
                            temp_left,
                            temp_right,
                            self.combo_dermatome.currentText()
                        )

                        all_results.append({
                            'image_index': idx + 1,
                            'image_name': image_name,
                            'left_temp': temp_left,
                            'right_temp': temp_right,
                            'delta_t': result.delta_t,
                            'classification': result.classification,
                            'clinical_significance': result.clinical_significance,
                            'method': 'auto_hotspot'
                        })
                        successful += 1
                        logger.info(f"  ✅ Sucesso: Esq={temp_left:.2f}°C, Dir={temp_right:.2f}°C, ΔT={result.delta_t:.2f}°C")
                    else:
                        # Não conseguiu detectar ambas as regiões
                        logger.warning(f"  ❌ Não foi possível detectar 2 regiões quentes (esquerda={temp_left}, direita={temp_right})")
                        failed += 1

                except Exception as e:
                    logger.error(f"Erro ao processar imagem {idx+1}: {e}", exc_info=True)
                    failed += 1

            progress.setValue(len(self.loaded_images))

            # Mostra resultados consolidados
            if all_results:
                result_summary = f"✅ Processamento Automático Concluído!\n\n"
                result_summary += f"🔥 Detecção automática de pontos quentes\n\n"
                result_summary += f"Total de imagens: {len(self.loaded_images)}\n"
                result_summary += f"Processadas com sucesso: {successful}\n"
                result_summary += f"Falhas: {failed}\n\n"
                result_summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

                # Estatísticas gerais
                avg_delta_t = np.mean([r['delta_t'] for r in all_results])
                max_delta_t = np.max([r['delta_t'] for r in all_results])
                min_delta_t = np.min([r['delta_t'] for r in all_results])
                avg_left = np.mean([r['left_temp'] for r in all_results])
                avg_right = np.mean([r['right_temp'] for r in all_results])

                result_summary += f"📊 Estatísticas Gerais:\n"
                result_summary += f"Temp. Média Esquerda: {avg_left:.2f}°C\n"
                result_summary += f"Temp. Média Direita: {avg_right:.2f}°C\n"
                result_summary += f"ΔT Médio: {avg_delta_t:.2f}°C\n"
                result_summary += f"ΔT Máximo: {max_delta_t:.2f}°C\n"
                result_summary += f"ΔT Mínimo: {min_delta_t:.2f}°C\n\n"

                # Distribuição de classificações
                classifications = {}
                for r in all_results:
                    cls = r['classification']
                    classifications[cls] = classifications.get(cls, 0) + 1

                result_summary += f"📈 Distribuição de Classificações:\n"
                for cls, count in sorted(classifications.items(), key=lambda x: -x[1]):
                    percentage = (count / len(all_results)) * 100
                    result_summary += f"• {cls}: {count} ({percentage:.1f}%)\n"

                # Detalhes de algumas imagens
                result_summary += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                result_summary += f"\n📋 Primeiras 5 imagens:\n"
                for i, r in enumerate(all_results[:5]):
                    result_summary += f"\n{i+1}. {r['image_name']}\n"
                    result_summary += f"   Esq: {r['left_temp']:.2f}°C | Dir: {r['right_temp']:.2f}°C\n"
                    result_summary += f"   ΔT: {r['delta_t']:.2f}°C - {r['classification']}\n"

                if len(all_results) > 5:
                    result_summary += f"\n... e mais {len(all_results) - 5} imagem(ns)\n"

                result_summary += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                result_summary += f"\n💡 Próximo passo: Clique em 'Gerar Laudo' para\n"
                result_summary += f"criar um relatório consolidado!"

                # Salva resultados para usar no laudo
                self.batch_results = all_results

                # Mostra resumo
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Processamento Automático")
                msg_box.setText(result_summary)
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.exec()

                # Habilita geração de laudo
                self.btn_generate_report.setEnabled(True)
                self.statusBar().showMessage(
                    f"Processamento automático concluído: {successful}/{len(self.loaded_images)}"
                )

            else:
                QMessageBox.warning(
                    self,
                    "Processamento Automático",
                    f"❌ Nenhuma imagem foi processada com sucesso.\n\n"
                    f"Possíveis causas:\n"
                    f"• Imagens sem dados térmicos válidos\n"
                    f"• Regiões quentes muito pequenas (< 100 pixels)\n"
                    f"• Distribuição de temperatura muito uniforme\n\n"
                    f"Tente:\n"
                    f"• Usar o modo manual (Processar Todas)\n"
                    f"• Verificar se as imagens são FLIR com dados térmicos"
                )

        except Exception as e:
            logger.error(f"Erro no processamento automático: {e}", exc_info=True)
            QMessageBox.critical(self, "Erro", f"Erro no processamento automático:\n\n{e}")

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
            'exam_date': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'clinical_indication': self.input_clinical_indication.toPlainText(),
            'equipment': 'Câmera termográfica FLIR',
            'dermatome_analyses': []
        }

        # Adiciona dados FLIR se disponível
        if self.flir_data is not None:
            exam_data['flir_reference_data'] = {
                'source_file': str(self.flir_html_path.name) if self.flir_html_path else 'unknown',
                'total_measurements': len(self.flir_data.get_all_measurements()),
                'images': []
            }

            for image in self.flir_data.images:
                image_data = {
                    'filename': image.filename,
                    'measurements': []
                }
                for m in image.measurements:
                    image_data['measurements'].append({
                        'roi_name': m.roi_name,
                        'mean_temp': m.mean_temp,
                        'max_temp': m.max_temp,
                        'min_temp': m.min_temp
                    })
                exam_data['flir_reference_data']['images'].append(image_data)

            # Adiciona relatório de validação se disponível
            if self.flir_validation_report is not None:
                exam_data['flir_validation'] = {
                    'accuracy': self.flir_validation_report.get_accuracy_percentage(),
                    'matched_rois': self.flir_validation_report.matched_rois,
                    'total_rois': self.flir_validation_report.total_rois,
                    'status_counts': self.flir_validation_report.get_status_counts(),
                    'statistics': self.flir_validation_report.statistics
                }

                logger.info(
                    f"Adicionando dados FLIR ao laudo: "
                    f"{self.flir_validation_report.matched_rois} ROIs validadas, "
                    f"precisão {self.flir_validation_report.get_accuracy_percentage():.1f}%"
                )

        # Verifica se há resultados de processamento em lote
        if self.batch_results and len(self.batch_results) > 0:
            # Processamento em lote - passa todos os resultados
            exam_data['batch_results'] = self.batch_results
            logger.info(f"Gerando laudo profissional com {len(self.batch_results)} imagens processadas em lote")

            # Se tem FLIR importado, valida batch results
            if self.flir_data is not None:
                # Coleta todas as temperaturas do batch
                all_temps = {}
                for result in self.batch_results:
                    if 'left_roi_name' in result and 'left_temp' in result:
                        all_temps[result.get('left_roi_name', 'Left')] = result['left_temp']
                    if 'right_roi_name' in result and 'right_temp' in result:
                        all_temps[result.get('right_roi_name', 'Right')] = result['right_temp']

                # Valida contra FLIR
                if all_temps:
                    self.validate_with_flir(all_temps)
        else:
            # Processamento individual - adiciona análise se disponível
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

                # Se tem FLIR, valida
                if self.flir_data is not None:
                    temps = {
                        'Left': float(self.input_left_temp.text()),
                        'Right': float(self.input_right_temp.text())
                    }
                    self.validate_with_flir(temps)

        # Mostra progresso
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Modo indeterminado

        # Inicia thread de geração
        self.report_thread = ReportGenerationThread('dermatome', exam_data)
        self.report_thread.finished.connect(self.on_report_generated)
        self.report_thread.error.connect(self.on_report_error)
        self.report_thread.start()

        status_msg = "Gerando laudo profissional com Claude AI..."
        if self.batch_results:
            status_msg += f" ({len(self.batch_results)} imagens)"
        self.statusBar().showMessage(status_msg)

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

        # Detecta erro de descriptografia
        if "descriptografar" in error_msg.lower() or "decrypt" in error_msg.lower():
            reply = QMessageBox.critical(
                self,
                "Erro ao carregar API Key",
                f"{error_msg}\n\n"
                f"A API key não pode ser descriptografada. Isso geralmente acontece quando:\n"
                f"• A API key foi configurada em outra máquina ou usuário\n"
                f"• O sistema foi reinstalado ou atualizado\n\n"
                f"Deseja reconfigurar a API key agora?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Remove credenciais antigas
                try:
                    from config.security import get_security_manager
                    security_manager = get_security_manager()
                    security_manager.delete_api_key()
                    logger.info("Credenciais antigas removidas")
                except Exception as e:
                    logger.error(f"Erro ao remover credenciais: {e}")

                # Muda para aba de configurações
                self.tabs.setCurrentIndex(3)  # Aba Configurações

                QMessageBox.information(
                    self,
                    "Reconfigurar API Key",
                    "Por favor, insira sua API key da Anthropic na aba Configurações\n"
                    "e clique em 'Salvar API Key'.\n\n"
                    "Você pode obter uma API key em:\n"
                    "https://console.anthropic.com/settings/keys"
                )
        else:
            # Outros erros
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

        # Menu FLIR
        flir_menu = menubar.addMenu("FLIR")

        action_import_flir_html = QAction("Importar FLIR HTML...", self)
        action_import_flir_html.setShortcut("Ctrl+F")
        action_import_flir_html.triggered.connect(self.import_flir_html)
        flir_menu.addAction(action_import_flir_html)

        action_show_validation = QAction("Ver Relatório de Validação", self)
        action_show_validation.setShortcut("Ctrl+Shift+V")
        action_show_validation.triggered.connect(self.show_flir_validation_details)
        flir_menu.addAction(action_show_validation)

        flir_menu.addSeparator()

        action_clear_flir = QAction("Limpar Dados FLIR", self)
        action_clear_flir.triggered.connect(self.clear_flir_data)
        flir_menu.addAction(action_clear_flir)

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
        try:
            self.current_rois = rois
            self.statusBar().showMessage(f"{len(rois)} ROI(s) criada(s)")

            logger.info(f"ROIs salvas: {len(rois)}")
            for roi in rois:
                logger.info(f"  - {roi['name']}: {len(roi.get('coordinates', roi.get('points', [])))} pontos")

            # Calcula temperaturas automaticamente se houver dados térmicos
            if not self.current_image_data:
                logger.warning("Nenhuma imagem carregada (current_image_data é None)")
                roi_names = "\n".join([f"• {roi['name']}" for roi in rois])
                QMessageBox.warning(self, "ROIs Salvas",
                    f"⚠️ {len(rois)} ROI(s) criadas!\n\n"
                    f"ROIs criadas:\n{roi_names}\n\n"
                    f"ATENÇÃO: Nenhuma imagem está carregada.\n"
                    f"Importe uma imagem FLIR primeiro.")
                return

            if 'thermal_data' not in self.current_image_data:
                logger.warning("Imagem não contém dados térmicos (thermal_data)")
                roi_names = "\n".join([f"• {roi['name']}" for roi in rois])
                QMessageBox.warning(self, "ROIs Salvas",
                    f"⚠️ {len(rois)} ROI(s) criadas!\n\n"
                    f"ROIs criadas:\n{roi_names}\n\n"
                    f"ATENÇÃO: Esta imagem não possui dados térmicos.\n"
                    f"Importe uma imagem FLIR com dados de temperatura.")
                return

            thermal_data = self.current_image_data['thermal_data']

            if thermal_data is None:
                logger.warning("thermal_data é None")
                roi_names = "\n".join([f"• {roi['name']}" for roi in rois])
                QMessageBox.warning(self, "ROIs Salvas",
                    f"⚠️ {len(rois)} ROI(s) criadas!\n\n"
                    f"ROIs criadas:\n{roi_names}\n\n"
                    f"ATENÇÃO: Dados térmicos não disponíveis.\n"
                    f"Clique em 'Processar' para tentar calcular.")
                return

            logger.info(f"Dados térmicos disponíveis: shape={thermal_data.shape}, dtype={thermal_data.dtype}")

            # Pega o tamanho da imagem visível usada para desenhar ROIs
            visible_image = self.current_image_data.get('visible_image')
            if visible_image is not None:
                visible_h, visible_w = visible_image.shape[:2]
                thermal_h, thermal_w = thermal_data.shape[:2]
                logger.info(f"Imagem visível: {visible_w}x{visible_h}, Dados térmicos: {thermal_w}x{thermal_h}")

                # Calcula fatores de escala
                scale_x = thermal_w / visible_w
                scale_y = thermal_h / visible_h
                logger.info(f"Fatores de escala: x={scale_x:.4f}, y={scale_y:.4f}")
            else:
                scale_x = scale_y = 1.0
                logger.warning("Imagem visível não disponível, usando escala 1:1")

            roi_temps_info = []
            import cv2

            for roi in rois:
                name = roi['name']
                points = roi.get('coordinates', roi.get('points', []))

                if not points:
                    logger.warning(f"ROI '{name}' não tem coordenadas")
                    continue

                logger.info(f"Processando ROI '{name}' com {len(points)} pontos")

                # Escala as coordenadas para o tamanho dos dados térmicos
                scaled_points = [(int(x * scale_x), int(y * scale_y)) for x, y in points]
                logger.info(f"  Original: {points[0]}, Escalado: {scaled_points[0]}")
                logger.info(f"  Todos os pontos escalados: {scaled_points}")

                # Verificar se os pontos estão dentro dos limites
                thermal_h, thermal_w = thermal_data.shape[:2]
                out_of_bounds = []
                for i, (x, y) in enumerate(scaled_points):
                    if x < 0 or x >= thermal_w or y < 0 or y >= thermal_h:
                        out_of_bounds.append(f"ponto[{i}]=({x},{y})")

                if out_of_bounds:
                    logger.warning(f"  ⚠️ Pontos fora dos limites [{thermal_w}x{thermal_h}]: {', '.join(out_of_bounds)}")
                    # Cortar pontos para ficarem dentro dos limites
                    scaled_points = [(max(0, min(x, thermal_w-1)), max(0, min(y, thermal_h-1))) for x, y in scaled_points]
                    logger.info(f"  Pontos corrigidos: {scaled_points}")

                # Calcular temperatura da ROI
                mask = np.zeros(thermal_data.shape[:2], dtype=np.uint8)
                pts = np.array(scaled_points, dtype=np.int32)
                cv2.fillPoly(mask, [pts], 255)

                # Log da máscara
                pixels_in_mask = np.sum(mask == 255)
                logger.info(f"  Pixels na máscara: {pixels_in_mask}")

                roi_region = thermal_data[mask == 255]
                if len(roi_region) > 0:
                    avg_temp = np.mean(roi_region)
                    roi_temps_info.append(f"• {name}: {avg_temp:.2f}°C")
                    logger.info(f"  ✅ Temperatura calculada: {avg_temp:.2f}°C (pixels: {len(roi_region)})")
                else:
                    logger.warning(f"  ❌ ROI '{name}' não capturou nenhum pixel após escalonamento")

            # Mostra temperaturas calculadas
            if roi_temps_info:
                temps_text = "\n".join(roi_temps_info)
                QMessageBox.information(self, "ROIs Salvas",
                    f"✅ {len(rois)} ROI(s) criadas e processadas!\n\n"
                    f"📊 Temperaturas calculadas:\n{temps_text}\n\n"
                    f"⚙️ Próximo passo: Clique em 'Processar' para preencher\n"
                    f"automaticamente os campos e analisar assimetria.")
            else:
                roi_names = "\n".join([f"• {roi['name']}" for roi in rois])
                QMessageBox.warning(self, "ROIs Salvas",
                    f"⚠️ {len(rois)} ROI(s) criadas mas nenhuma temperatura foi calculada!\n\n"
                    f"ROIs criadas:\n{roi_names}\n\n"
                    f"Possíveis causas:\n"
                    f"• ROIs fora da área da imagem\n"
                    f"• ROIs muito pequenas\n"
                    f"• Coordenadas inválidas\n\n"
                    f"Tente redesenhar as ROIs ou clique em 'Processar'.")

        except Exception as e:
            logger.error(f"Erro em on_rois_saved: {e}", exc_info=True)
            QMessageBox.critical(self, "Erro",
                f"Erro ao processar ROIs salvas:\n\n{str(e)}\n\n"
                f"Verifique os logs para mais detalhes.")

    def import_flir_html(self):
        """Importa arquivo HTML do FLIR Thermal Studio com medições de referência."""
        # Verifica se módulos FLIR estão disponíveis
        if not FLIR_AVAILABLE:
            QMessageBox.critical(
                self,
                "FLIR não disponível",
                "Os módulos FLIR não estão disponíveis.\n\n"
                "Certifique-se de que beautifulsoup4 está instalado:\n"
                "  pip install beautifulsoup4\n\n"
                "Depois reinicie a aplicação."
            )
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Export HTML do FLIR Thermal Studio",
            "",
            "HTML Files (*.html *.htm)"
        )

        if not file_path:
            return

        try:
            # Parse HTML
            self.flir_html_path = Path(file_path)
            self.flir_data = parse_flir_html(self.flir_html_path)

            total_measurements = len(self.flir_data.get_all_measurements())
            total_images = len(self.flir_data.images)

            # Atualiza status
            self.update_flir_status()

            # Mostra informações
            info_text = (
                f"✅ FLIR HTML importado com sucesso!\n\n"
                f"📊 Total de imagens: {total_images}\n"
                f"🌡️  Total de medições: {total_measurements}\n\n"
                f"Detalhes:\n"
            )

            for image in self.flir_data.images:
                info_text += f"\n📷 {image.filename}:\n"
                for m in image.measurements[:5]:  # Mostra primeiras 5
                    info_text += f"   • {m.roi_name}: {m.mean_temp:.2f}°C\n"
                if len(image.measurements) > 5:
                    info_text += f"   ... e mais {len(image.measurements) - 5} ROIs\n"

            info_text += (
                f"\n💡 Esses dados serão usados para:\n"
                f"   • Validar precisão das medições do sistema\n"
                f"   • Enriquecer os laudos gerados pelo Claude AI\n"
                f"   • Fornecer referência profissional FLIR"
            )

            QMessageBox.information(
                self,
                "FLIR HTML Importado",
                info_text
            )

            logger.info(f"FLIR HTML importado: {file_path}")
            logger.info(f"  {total_images} imagens, {total_measurements} medições")

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Erro ao importar FLIR HTML: {e}", exc_info=True)

            # Mostra erro detalhado
            error_msg = QMessageBox(self)
            error_msg.setIcon(QMessageBox.Icon.Critical)
            error_msg.setWindowTitle("Erro ao Importar FLIR HTML")
            error_msg.setText(f"Erro ao processar arquivo HTML do FLIR:\n\n{str(e)}")
            error_msg.setDetailedText(error_details)
            error_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            error_msg.exec()

            self.flir_html_path = None
            self.flir_data = None
            self.update_flir_status()

    def validate_with_flir(self, system_temperatures: Dict[str, float]) -> Optional[Any]:
        """
        Valida temperaturas do sistema contra dados FLIR.

        Args:
            system_temperatures: Dicionário {roi_name: temperatura}

        Returns:
            ValidationReport ou None se FLIR não disponível
        """
        if self.flir_data is None or not FLIR_AVAILABLE:
            return None

        try:
            validator = FLIRValidator(
                tolerance_ok=0.5,
                tolerance_warning=1.0
            )

            validation_report = validator.validate(
                self.flir_data,
                system_temperatures,
                fuzzy_match=True
            )

            self.flir_validation_report = validation_report
            self.update_flir_status()

            logger.info(f"Validação FLIR: {validation_report}")

            return validation_report

        except Exception as e:
            logger.error(f"Erro na validação FLIR: {e}", exc_info=True)
            return None

    def update_flir_status(self):
        """Atualiza label de status FLIR."""
        if self.flir_data is None:
            self.lbl_flir_status.setText("FLIR: ✗")
            self.lbl_flir_status.setStyleSheet("color: gray;")
            self.lbl_flir_status.setToolTip("Nenhum arquivo FLIR HTML importado")
        elif self.flir_validation_report is None:
            # FLIR importado mas ainda não validado
            total_measurements = len(self.flir_data.get_all_measurements())
            self.lbl_flir_status.setText(f"FLIR: ✓ ({total_measurements})")
            self.lbl_flir_status.setStyleSheet("color: blue;")
            self.lbl_flir_status.setToolTip(
                f"FLIR importado: {total_measurements} medições\n"
                f"Aguardando processamento para validação"
            )
        else:
            # FLIR importado e validado
            accuracy = self.flir_validation_report.get_accuracy_percentage()
            matched = self.flir_validation_report.matched_rois
            total = self.flir_validation_report.total_rois

            if accuracy >= 90:
                color = "green"
                symbol = "✓✓"
            elif accuracy >= 70:
                color = "orange"
                symbol = "✓"
            else:
                color = "red"
                symbol = "⚠"

            self.lbl_flir_status.setText(f"FLIR: {symbol} {accuracy:.0f}%")
            self.lbl_flir_status.setStyleSheet(f"color: {color}; font-weight: bold;")

            status_counts = self.flir_validation_report.get_status_counts()
            tooltip = (
                f"Validação FLIR:\n"
                f"Precisão: {accuracy:.1f}%\n"
                f"ROIs: {matched}/{total}\n"
                f"✅ OK: {status_counts['ok']}\n"
                f"⚠️ Warning: {status_counts['warning']}\n"
                f"❌ Error: {status_counts['error']}\n"
            )

            if self.flir_validation_report.statistics:
                stats = self.flir_validation_report.statistics
                tooltip += (
                    f"\nEstatísticas:\n"
                    f"Diff média: {stats['mean_abs_difference']:.2f}°C\n"
                    f"Diff máxima: {stats['max_abs_difference']:.2f}°C"
                )

            self.lbl_flir_status.setToolTip(tooltip)

    def show_flir_validation_details(self):
        """Mostra detalhes completos da validação FLIR."""
        if not FLIR_AVAILABLE:
            QMessageBox.warning(
                self,
                "FLIR não disponível",
                "Módulos FLIR não estão disponíveis."
            )
            return

        if self.flir_validation_report is None:
            QMessageBox.information(
                self,
                "Validação FLIR",
                "Nenhuma validação disponível.\n\n"
                "Importe um arquivo FLIR HTML e processe uma imagem para ver a validação."
            )
            return

        try:
            validator = FLIRValidator()
            report_text = validator.generate_text_report(self.flir_validation_report)

            # Cria dialog para exibir relatório
            dialog = QMessageBox(self)
            dialog.setWindowTitle("Relatório de Validação FLIR")
            dialog.setIcon(QMessageBox.Icon.Information)
            dialog.setText("Relatório completo de validação FLIR vs Sistema:")
            dialog.setDetailedText(report_text)
            dialog.setStandardButtons(QMessageBox.StandardButton.Ok)

            # Expande o texto detalhado automaticamente
            for button in dialog.buttons():
                if dialog.buttonRole(button) == QMessageBox.ButtonRole.ActionRole:
                    button.click()
                    break

            dialog.exec()

        except Exception as e:
            logger.error(f"Erro ao exibir validação FLIR: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao exibir relatório de validação:\n\n{str(e)}"
            )

    def clear_flir_data(self):
        """Limpa dados FLIR importados."""
        if self.flir_data is None:
            QMessageBox.information(
                self,
                "Limpar FLIR",
                "Nenhum dado FLIR importado para limpar."
            )
            return

        reply = QMessageBox.question(
            self,
            "Limpar Dados FLIR",
            "Deseja realmente limpar os dados FLIR importados?\n\n"
            "Isso removerá:\n"
            "• Medições de referência FLIR\n"
            "• Relatório de validação\n\n"
            "Esta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.flir_html_path = None
            self.flir_data = None
            self.flir_validation_report = None
            self.update_flir_status()

            QMessageBox.information(
                self,
                "FLIR Limpo",
                "✅ Dados FLIR removidos com sucesso."
            )

            logger.info("Dados FLIR limpos pelo usuário")

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
            <li>Importação e validação FLIR HTML</li>
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
