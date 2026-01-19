"""
Sistema de temas para a interface PyQt6.
Suporta Light Mode e Dark Mode com estilos personalizados.
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ThemeManager:
    """Gerenciador de temas da aplicação."""

    # Temas disponíveis
    LIGHT = "light"
    DARK = "dark"
    BLUE = "blue"

    def __init__(self, app: Optional[QApplication] = None):
        """
        Inicializa o gerenciador de temas.

        Args:
            app: Instância do QApplication
        """
        self.app = app or QApplication.instance()
        self.current_theme = self.LIGHT

    def apply_theme(self, theme: str = LIGHT):
        """
        Aplica um tema à aplicação.

        Args:
            theme: Nome do tema ('light', 'dark', ou 'blue')
        """
        if theme == self.DARK:
            self._apply_dark_theme()
        elif theme == self.BLUE:
            self._apply_blue_theme()
        else:
            self._apply_light_theme()

        self.current_theme = theme
        logger.info(f"Tema aplicado: {theme}")

    def _apply_light_theme(self):
        """Aplica tema claro (padrão)."""
        self.app.setStyle("Fusion")

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(0, 0, 255))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

        self.app.setPalette(palette)
        self.app.setStyleSheet(self._get_light_stylesheet())

    def _apply_dark_theme(self):
        """Aplica tema escuro."""
        self.app.setStyle("Fusion")

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(35, 35, 35))

        # Cores para disabled
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(127, 127, 127))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(127, 127, 127))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(127, 127, 127))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, QColor(80, 80, 80))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, QColor(127, 127, 127))

        self.app.setPalette(palette)
        self.app.setStyleSheet(self._get_dark_stylesheet())

    def _apply_blue_theme(self):
        """Aplica tema azul médico."""
        self.app.setStyle("Fusion")

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(230, 240, 250))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(240, 245, 250))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(220, 230, 240))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Button, QColor(200, 220, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(0, 90, 180))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(26, 90, 154))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

        self.app.setPalette(palette)
        self.app.setStyleSheet(self._get_blue_stylesheet())

    def _get_light_stylesheet(self) -> str:
        """Retorna stylesheet para tema claro."""
        return """
            QMainWindow {
                background-color: #f0f0f0;
            }

            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
            }

            QPushButton {
                background-color: #e0e0e0;
                border: 1px solid #b0b0b0;
                border-radius: 3px;
                padding: 5px 15px;
                min-height: 25px;
            }

            QPushButton:hover {
                background-color: #d0d0d0;
                border: 1px solid #a0a0a0;
            }

            QPushButton:pressed {
                background-color: #c0c0c0;
            }

            QPushButton:disabled {
                background-color: #f0f0f0;
                color: #a0a0a0;
            }

            QLineEdit, QTextEdit, QListWidget, QTableWidget {
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 3px;
                background-color: white;
            }

            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #2a82da;
            }

            QTabWidget::pane {
                border: 1px solid #ccc;
                border-radius: 3px;
            }

            QTabBar::tab {
                background-color: #e0e0e0;
                border: 1px solid #b0b0b0;
                border-bottom: none;
                border-top-left-radius: 3px;
                border-top-right-radius: 3px;
                padding: 5px 15px;
                margin-right: 2px;
            }

            QTabBar::tab:selected {
                background-color: white;
                font-weight: bold;
            }

            QTabBar::tab:hover:!selected {
                background-color: #d0d0d0;
            }

            QStatusBar {
                background-color: #e0e0e0;
                border-top: 1px solid #b0b0b0;
            }
        """

    def _get_dark_stylesheet(self) -> str:
        """Retorna stylesheet para tema escuro."""
        return """
            QMainWindow {
                background-color: #353535;
            }

            QGroupBox {
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #ffffff;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
            }

            QPushButton {
                background-color: #454545;
                border: 1px solid #656565;
                border-radius: 3px;
                padding: 5px 15px;
                min-height: 25px;
                color: #ffffff;
            }

            QPushButton:hover {
                background-color: #505050;
                border: 1px solid #757575;
            }

            QPushButton:pressed {
                background-color: #404040;
            }

            QPushButton:disabled {
                background-color: #353535;
                color: #7f7f7f;
            }

            QLineEdit, QTextEdit, QListWidget, QTableWidget {
                border: 1px solid #555;
                border-radius: 3px;
                padding: 3px;
                background-color: #232323;
                color: #ffffff;
            }

            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #2a82da;
            }

            QTabWidget::pane {
                border: 1px solid #555;
                border-radius: 3px;
            }

            QTabBar::tab {
                background-color: #454545;
                border: 1px solid #656565;
                border-bottom: none;
                border-top-left-radius: 3px;
                border-top-right-radius: 3px;
                padding: 5px 15px;
                margin-right: 2px;
                color: #ffffff;
            }

            QTabBar::tab:selected {
                background-color: #232323;
                font-weight: bold;
            }

            QTabBar::tab:hover:!selected {
                background-color: #505050;
            }

            QStatusBar {
                background-color: #454545;
                border-top: 1px solid #656565;
                color: #ffffff;
            }

            QLabel {
                color: #ffffff;
            }

            QTableWidget {
                gridline-color: #555;
            }

            QHeaderView::section {
                background-color: #454545;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #555;
            }
        """

    def _get_blue_stylesheet(self) -> str:
        """Retorna stylesheet para tema azul médico."""
        return """
            QMainWindow {
                background-color: #e6f0fa;
            }

            QGroupBox {
                font-weight: bold;
                border: 1px solid #1a5a9a;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #1a5a9a;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
            }

            QPushButton {
                background-color: #c8dcf0;
                border: 1px solid #1a5a9a;
                border-radius: 3px;
                padding: 5px 15px;
                min-height: 25px;
                color: #000;
            }

            QPushButton:hover {
                background-color: #b8ccf0;
                border: 1px solid #0a4a8a;
            }

            QPushButton:pressed {
                background-color: #a8bcf0;
            }

            QPushButton:disabled {
                background-color: #e6f0fa;
                color: #888;
            }

            QLineEdit, QTextEdit, QListWidget, QTableWidget {
                border: 1px solid #1a5a9a;
                border-radius: 3px;
                padding: 3px;
                background-color: white;
            }

            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #0a4a8a;
            }

            QTabWidget::pane {
                border: 1px solid #1a5a9a;
                border-radius: 3px;
            }

            QTabBar::tab {
                background-color: #c8dcf0;
                border: 1px solid #1a5a9a;
                border-bottom: none;
                border-top-left-radius: 3px;
                border-top-right-radius: 3px;
                padding: 5px 15px;
                margin-right: 2px;
            }

            QTabBar::tab:selected {
                background-color: white;
                font-weight: bold;
            }

            QTabBar::tab:hover:!selected {
                background-color: #b8ccf0;
            }

            QStatusBar {
                background-color: #c8dcf0;
                border-top: 1px solid #1a5a9a;
            }
        """

    def toggle_theme(self):
        """Alterna entre tema claro e escuro."""
        if self.current_theme == self.DARK:
            self.apply_theme(self.LIGHT)
        else:
            self.apply_theme(self.DARK)

    def get_current_theme(self) -> str:
        """Retorna o tema atual."""
        return self.current_theme


# Instância global
_theme_manager = None


def get_theme_manager(app: Optional[QApplication] = None) -> ThemeManager:
    """
    Retorna a instância global do ThemeManager (padrão Singleton).

    Args:
        app: Instância do QApplication (apenas na primeira chamada)

    Returns:
        Instância de ThemeManager
    """
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager(app)
    return _theme_manager


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget

    app = QApplication(sys.argv)

    # Cria janela de teste
    window = QMainWindow()
    window.setWindowTitle("Teste de Temas")
    window.resize(400, 300)

    central = QWidget()
    layout = QVBoxLayout(central)

    theme_manager = get_theme_manager(app)

    # Botões para testar temas
    btn_light = QPushButton("Tema Claro")
    btn_light.clicked.connect(lambda: theme_manager.apply_theme(ThemeManager.LIGHT))
    layout.addWidget(btn_light)

    btn_dark = QPushButton("Tema Escuro")
    btn_dark.clicked.connect(lambda: theme_manager.apply_theme(ThemeManager.DARK))
    layout.addWidget(btn_dark)

    btn_blue = QPushButton("Tema Azul")
    btn_blue.clicked.connect(lambda: theme_manager.apply_theme(ThemeManager.BLUE))
    layout.addWidget(btn_blue)

    btn_toggle = QPushButton("Alternar Claro/Escuro")
    btn_toggle.clicked.connect(theme_manager.toggle_theme)
    layout.addWidget(btn_toggle)

    window.setCentralWidget(central)
    window.show()

    # Aplica tema inicial
    theme_manager.apply_theme(ThemeManager.LIGHT)

    sys.exit(app.exec())
