import sys
from PyQt5.QtWidgets import (QApplication, QDialog)
from gui.main_window import MainWindow
from core.serial_config import SerialConfigDialog

def main():
    app = QApplication(sys.argv)

    config_dialog = SerialConfigDialog()
    if config_dialog.exec_() == QDialog.Accepted:
        config = config_dialog.get_settings()
    else:
        config = {'port': "", 'baudrate': 9600, 'lora_config': None}

    window = MainWindow(config)
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
    # test

if __name__ == "__main__":
    main()