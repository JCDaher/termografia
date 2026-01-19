"""
Editor interativo de ROIs (Regions of Interest) para imagens termográficas.
Permite desenhar polígonos, retângulos e elipses sobre as imagens.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QMessageBox, QInputDialog, QGroupBox, QComboBox
)
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QPixmap, QImage, QColor, QBrush
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ROICanvas(QLabel):
    """Canvas para desenhar ROIs sobre a imagem."""

    roi_completed = pyqtSignal(list)  # Emite coordenadas quando ROI é completa

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumSize(600, 400)
        self.setStyleSheet("border: 2px solid #ccc; background-color: white;")

        # Estado do desenho
        self.drawing = False
        self.current_points = []
        self.completed_rois = []
        self.mode = 'polygon'  # polygon, rectangle, ellipse
        self.temp_rect_start = None

        # Imagem de fundo
        self.background_image = None
        self.scaled_pixmap = None

    def set_image(self, image: np.ndarray):
        """
        Define a imagem de fundo.

        Args:
            image: Imagem BGR do OpenCV
        """
        try:
            # Converte BGR para RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            height, width, channel = rgb_image.shape
            bytes_per_line = 3 * width

            q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)

            # Escala para caber no canvas
            self.scaled_pixmap = pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            self.background_image = image
            self.update()

        except Exception as e:
            logger.error(f"Erro ao definir imagem: {e}")

    def set_mode(self, mode: str):
        """
        Define o modo de desenho.

        Args:
            mode: 'polygon', 'rectangle', ou 'ellipse'
        """
        self.mode = mode
        self.clear_current()

    def mousePressEvent(self, event):
        """Evento de clique do mouse."""
        if event.button() == Qt.MouseButton.LeftButton:
            point = event.pos()

            if self.mode == 'polygon':
                self.current_points.append(point)
                self.update()

            elif self.mode in ['rectangle', 'ellipse']:
                self.temp_rect_start = point
                self.drawing = True

        elif event.button() == Qt.MouseButton.RightButton:
            # Botão direito finaliza o polígono
            if self.mode == 'polygon' and len(self.current_points) >= 3:
                self.finish_roi()

    def mouseMoveEvent(self, event):
        """Evento de movimento do mouse."""
        if self.drawing and self.temp_rect_start:
            self.update()

    def mouseReleaseEvent(self, event):
        """Evento de soltar o mouse."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.mode in ['rectangle', 'ellipse'] and self.temp_rect_start:
                point = event.pos()
                # Cria retângulo/elipse
                rect = QRect(self.temp_rect_start, point).normalized()

                # Converte para polígono de pontos
                if self.mode == 'rectangle':
                    self.current_points = [
                        rect.topLeft(),
                        rect.topRight(),
                        rect.bottomRight(),
                        rect.bottomLeft()
                    ]
                else:  # ellipse
                    # Aproxima elipse com polígono de 20 pontos
                    self.current_points = self._ellipse_to_polygon(rect, 20)

                self.finish_roi()
                self.temp_rect_start = None
                self.drawing = False

    def _ellipse_to_polygon(self, rect: QRect, num_points: int = 20) -> List[QPoint]:
        """
        Converte uma elipse em polígono.

        Args:
            rect: Retângulo delimitador da elipse
            num_points: Número de pontos do polígono

        Returns:
            Lista de pontos formando a elipse
        """
        points = []
        cx = rect.center().x()
        cy = rect.center().y()
        rx = rect.width() / 2
        ry = rect.height() / 2

        for i in range(num_points):
            angle = 2 * np.pi * i / num_points
            x = int(cx + rx * np.cos(angle))
            y = int(cy + ry * np.sin(angle))
            points.append(QPoint(x, y))

        return points

    def finish_roi(self):
        """Finaliza a ROI atual e emite sinal."""
        if len(self.current_points) >= 3:
            # Converte QPoint para tuplas (x, y)
            coords = [(p.x(), p.y()) for p in self.current_points]

            # Adiciona às ROIs completadas
            self.completed_rois.append({
                'points': self.current_points.copy(),
                'coords': coords
            })

            # Emite sinal
            self.roi_completed.emit(coords)

            # Limpa pontos atuais
            self.clear_current()

    def clear_current(self):
        """Limpa a ROI atual sendo desenhada."""
        self.current_points = []
        self.temp_rect_start = None
        self.drawing = False
        self.update()

    def clear_all(self):
        """Limpa todas as ROIs."""
        self.current_points = []
        self.completed_rois = []
        self.temp_rect_start = None
        self.drawing = False
        self.update()

    def paintEvent(self, event):
        """Desenha a imagem e as ROIs."""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Desenha imagem de fundo
        if self.scaled_pixmap:
            painter.drawPixmap(0, 0, self.scaled_pixmap)

        # Desenha ROIs completadas
        for roi in self.completed_rois:
            pen = QPen(QColor(0, 255, 0), 2)
            brush = QBrush(QColor(0, 255, 0, 50))
            painter.setPen(pen)
            painter.setBrush(brush)

            points = roi['points']
            if len(points) >= 2:
                for i in range(len(points)):
                    p1 = points[i]
                    p2 = points[(i + 1) % len(points)]
                    painter.drawLine(p1, p2)

        # Desenha ROI atual
        if len(self.current_points) > 0:
            pen = QPen(QColor(255, 0, 0), 2)
            brush = QBrush(QColor(255, 0, 0, 30))
            painter.setPen(pen)

            # Desenha linhas
            for i in range(len(self.current_points)):
                p1 = self.current_points[i]
                if i < len(self.current_points) - 1:
                    p2 = self.current_points[i + 1]
                    painter.drawLine(p1, p2)

                # Desenha pontos
                painter.drawEllipse(p1, 3, 3)

            # Linha de fechamento (se polígono)
            if self.mode == 'polygon' and len(self.current_points) >= 2:
                pen.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.drawLine(self.current_points[-1], self.current_points[0])

        # Desenha retângulo/elipse temporário
        if self.drawing and self.temp_rect_start:
            pen = QPen(QColor(255, 0, 0), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)

            current_pos = self.mapFromGlobal(self.cursor().pos())
            rect = QRect(self.temp_rect_start, current_pos).normalized()

            if self.mode == 'rectangle':
                painter.drawRect(rect)
            elif self.mode == 'ellipse':
                painter.drawEllipse(rect)


class ROIEditorDialog(QDialog):
    """Dialog para edição de ROIs."""

    rois_saved = pyqtSignal(list)  # Emite lista de ROIs quando salvos

    def __init__(self, image: np.ndarray, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editor de ROIs - Termografia")
        self.resize(900, 700)

        self.image = image
        self.rois = []

        self.init_ui()

    def init_ui(self):
        """Inicializa a interface."""
        layout = QVBoxLayout(self)

        # Instruções
        instructions = QLabel(
            "<b>Instruções:</b><br>"
            "• <b>Polígono:</b> Clique para adicionar pontos, clique direito para fechar<br>"
            "• <b>Retângulo/Elipse:</b> Clique e arraste para desenhar<br>"
            "• Use 'Limpar Atual' para recomeçar, 'Limpar Tudo' para apagar todas"
        )
        instructions.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(instructions)

        # Layout horizontal para controles e canvas
        h_layout = QHBoxLayout()

        # Painel de controles
        controls_group = QGroupBox("Controles")
        controls_layout = QVBoxLayout(controls_group)

        # Modo de desenho
        controls_layout.addWidget(QLabel("<b>Modo de Desenho:</b>"))
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(['Polígono', 'Retângulo', 'Elipse'])
        self.combo_mode.currentTextChanged.connect(self.change_mode)
        controls_layout.addWidget(self.combo_mode)

        # Botões de ação
        self.btn_clear_current = QPushButton("Limpar Atual")
        self.btn_clear_current.clicked.connect(self.canvas.clear_current)
        controls_layout.addWidget(self.btn_clear_current)

        self.btn_clear_all = QPushButton("Limpar Tudo")
        self.btn_clear_all.clicked.connect(self.clear_all_rois)
        controls_layout.addWidget(self.btn_clear_all)

        controls_layout.addWidget(QLabel("<b>ROIs Criadas:</b>"))

        # Lista de ROIs
        self.list_rois = QListWidget()
        controls_layout.addWidget(self.list_rois)

        self.btn_remove_roi = QPushButton("Remover Selecionada")
        self.btn_remove_roi.clicked.connect(self.remove_selected_roi)
        controls_layout.addWidget(self.btn_remove_roi)

        controls_layout.addStretch()

        controls_group.setMaximumWidth(250)
        h_layout.addWidget(controls_group)

        # Canvas de desenho
        self.canvas = ROICanvas()
        self.canvas.set_image(self.image)
        self.canvas.roi_completed.connect(self.on_roi_completed)
        h_layout.addWidget(self.canvas, stretch=1)

        layout.addLayout(h_layout)

        # Botões finais
        buttons_layout = QHBoxLayout()

        btn_save = QPushButton("Salvar ROIs")
        btn_save.clicked.connect(self.save_rois)
        btn_save.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;")
        buttons_layout.addWidget(btn_save)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        layout.addLayout(buttons_layout)

    def change_mode(self, mode_text: str):
        """Altera o modo de desenho."""
        mode_map = {
            'Polígono': 'polygon',
            'Retângulo': 'rectangle',
            'Elipse': 'ellipse'
        }
        self.canvas.set_mode(mode_map[mode_text])

    def on_roi_completed(self, coords: List[Tuple[int, int]]):
        """Callback quando ROI é completada."""
        # Pede nome para a ROI
        name, ok = QInputDialog.getText(
            self,
            "Nome da ROI",
            "Digite um nome para esta ROI:",
            text=f"ROI {len(self.rois) + 1}"
        )

        if ok and name:
            roi_data = {
                'name': name,
                'coordinates': coords,
                'type': self.combo_mode.currentText()
            }

            self.rois.append(roi_data)
            self.list_rois.addItem(f"{name} ({roi_data['type']})")

    def remove_selected_roi(self):
        """Remove ROI selecionada."""
        current_row = self.list_rois.currentRow()
        if current_row >= 0:
            self.list_rois.takeItem(current_row)
            self.rois.pop(current_row)

            # Atualiza canvas (remove da lista de completados)
            if current_row < len(self.canvas.completed_rois):
                self.canvas.completed_rois.pop(current_row)
                self.canvas.update()

    def clear_all_rois(self):
        """Limpa todas as ROIs."""
        reply = QMessageBox.question(
            self,
            "Confirmar",
            "Deseja realmente apagar todas as ROIs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.rois = []
            self.list_rois.clear()
            self.canvas.clear_all()

    def save_rois(self):
        """Salva as ROIs e fecha o dialog."""
        if not self.rois:
            QMessageBox.warning(self, "Aviso", "Nenhuma ROI foi criada")
            return

        self.rois_saved.emit(self.rois)
        self.accept()


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # Cria imagem de teste
    test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

    dialog = ROIEditorDialog(test_image)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        print(f"ROIs salvos: {len(dialog.rois)}")
        for roi in dialog.rois:
            print(f"- {roi['name']}: {len(roi['coordinates'])} pontos")
    else:
        print("Cancelado")
