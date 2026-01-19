"""
Entry point do aplicativo de termografia médica.
Inicializa a interface PyQt6 e configura logging.
"""

import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from ui.main_window import MainWindow


def setup_logging():
    """Configura sistema de logging."""
    # Cria diretório de logs se não existir
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # Configura logging
    log_file = log_dir / 'termografia.log'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("Aplicativo de Termografia Médica - FASE 1 MVP")
    logger.info("=" * 80)

    return logger


def main():
    """Função principal."""
    # Configura logging
    logger = setup_logging()

    try:
        # Cria aplicação Qt
        app = QApplication(sys.argv)

        # Configura nome e organização (para QSettings)
        app.setOrganizationName("TermografiaApp")
        app.setApplicationName("Termografia Médica")

        # Configura estilo (opcional)
        app.setStyle('Fusion')

        # Habilita high DPI scaling
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

        logger.info("Inicializando interface gráfica...")

        # Cria e exibe janela principal
        window = MainWindow()
        window.show()

        logger.info("Interface iniciada com sucesso")
        logger.info("Aplicativo pronto para uso")

        # Executa loop da aplicação
        exit_code = app.exec()

        logger.info(f"Aplicativo encerrado com código: {exit_code}")
        return exit_code

    except Exception as e:
        logger.error(f"Erro fatal na inicialização: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
