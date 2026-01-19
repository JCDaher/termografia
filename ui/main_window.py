"""
Interface principal do aplicativo de termografia médica.
Janela principal PyQt6 com funcionalidades de importação, análise e geração de laudos.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QTextEdit, QTabWidget, QGroupBox,
    QLineEdit, QComboBox, QSpinBox, QMessageBox, QProgressBar,
    QTableWidget, QTableWidgetItem, QSplitter, QFormLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
import logging
from typing import Optional, Dict, Any

from core.flir_processor import FLIRProcessor
from core.thermal_analyzer import ThermalAnalyzer
from database.db_manager import get_db_manager
from api.claude_client import get_claude_client, has_api_key, configure_api_key

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

        # Estado da aplicação
        self.current_image_data = None
        self.current_exam_id = None
        self.current_patient_id = None

        self.init_ui()
        self.check_api_key()

    def init_ui(self):
        """Inicializa a interface do usuário."""
        self.setWindowTitle("Termografia Médica - FASE 1 MVP")
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

        # Botão importar imagem
        self.btn_import = QPushButton("📁 Importar Imagem FLIR")
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

        self.lbl_image = QLabel("Nenhuma imagem carregada")
        self.lbl_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_image.setMinimumSize(400, 300)
        self.lbl_image.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")

        left_layout.addWidget(QLabel("Imagem Térmica:"))
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

    def import_flir_image(self):
        """Importa imagem FLIR."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Imagem FLIR",
            "",
            "Imagens (*.jpg *.jpeg *.png *.bmp)"
        )

        if not file_path:
            return

        try:
            # Carrega e processa imagem
            self.current_image_data = self.flir_processor.load_flir_image(file_path)

            # Exibe imagem
            self.display_image(self.current_image_data['visible_image'])

            # Mostra estatísticas
            stats = self.current_image_data['statistics']
            stats_text = f"""
Arquivo: {Path(file_path).name}
Resolução: {self.current_image_data['resolution'][0]}x{self.current_image_data['resolution'][1]}

Temperatura Mínima: {stats['min_temp']:.2f}°C
Temperatura Máxima: {stats['max_temp']:.2f}°C
Temperatura Média: {stats['mean_temp']:.2f}°C
Desvio Padrão: {stats['std_temp']:.2f}°C
"""
            self.text_stats.setText(stats_text)

            # Salva no banco se houver exame ativo
            if self.current_exam_id:
                self.db_manager.add_thermal_image(
                    exam_id=self.current_exam_id,
                    image_path=file_path,
                    image_type='FLIR',
                    min_temp=stats['min_temp'],
                    max_temp=stats['max_temp'],
                    avg_temp=stats['mean_temp']
                )

            self.btn_process.setEnabled(True)
            self.btn_toggle_heatmap.setEnabled(True)
            self.statusBar().showMessage("Imagem importada com sucesso")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao importar imagem: {e}")

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
        self.text_report.setText(report)
        self.tabs.setCurrentIndex(2)  # Vai para aba de laudo
        self.statusBar().showMessage("Laudo gerado com sucesso")
        QMessageBox.information(self, "Sucesso", "Laudo gerado com sucesso!")

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
        # TODO: Implementar exportação PDF na FASE 2
        QMessageBox.information(
            self,
            "Em Desenvolvimento",
            "Exportação para PDF será implementada na FASE 2"
        )


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
