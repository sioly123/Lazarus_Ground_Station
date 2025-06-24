import sys
import logging
from PyQt5.QtWidgets import (QApplication, QDialog)
from gui.main_window import MainWindow
from core.serial_config import SerialConfigDialog

def main():

    logging.basicConfig(
        filename=r'logs\app_events.log', filemode='a',
        level=logging.INFO,
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger('Lazarus_Ground_Station')

    app = QApplication(sys.argv)
    logger.info("Uruchamianie aplikacji")

    config_dialog = SerialConfigDialog()
    if config_dialog.exec_() == QDialog.Accepted:
        config = config_dialog.get_settings()
        logger.info(f"Konfiguracja portu załadowana: {config}")
    else:
        config = {'port': "", 'baudrate': 9600, 'lora_config': None}
        logger.info("Użytkownik zrezygnował z portu – używam domyślnych ustawień")

    window = MainWindow(config)
    window.resize(800, 600)
    window.show()
    exit_code = app.exec_()
    logger.info(f"Aplikacja zakończona z kodem {exit_code}")
    sys.exit(exit_code)
    # test

if __name__ == "__main__":
    main()