import sys
from PyQt5.QtWidgets import (QApplication, QDialog,
                             QVBoxLayout, QHBoxLayout,
                             QLabel,
                             QComboBox, QPushButton,
                             QGroupBox)
from PyQt5.QtCore import Qt
import serial.tools.list_ports


class SerialConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(
            "Konfiguracja portu szeregowego i LoRa")
        self.setFixedSize(450, 400)
        self.setStyleSheet("""
            QDialog { background-color: #2c3e50; }
            QLabel { color: #ecf0f1; font-size: 12px; }
            QComboBox, QPushButton, QGroupBox {
                background-color: #34495e; 
                color: #ecf0f1; 
                border: 1px solid #7f8c8d;
                padding: 5px;
                border-radius: 4px;
            }
            QGroupBox { 
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title { color: #1abc9c; }
            QPushButton:hover { background-color: #3d566e; }
            QPushButton:disabled { background-color: #2c3e50; color: #7f8c8d; }
        """)

        self.port_name = ""
        self.baud_rate = 9600
        self.lora_config = {
            'frequency': '433',
            'bandwidth': '125',
            'spreading_factor': '10',
            'coding_rate': '4/5',
            'power': '20'
        }

        layout = QVBoxLayout()

        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port COM:"))
        self.port_combo = QComboBox()
        self.refresh_ports()
        port_layout.addWidget(self.port_combo)

        refresh_btn = QPushButton("Odśwież")
        refresh_btn.setFixedWidth(80)
        refresh_btn.clicked.connect(self.refresh_ports)
        port_layout.addWidget(refresh_btn)
        layout.addLayout(port_layout)

        baud_layout = QHBoxLayout()
        baud_layout.addWidget(
            QLabel("Prędkość transmisji:"))
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(
            ["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("9600")
        baud_layout.addWidget(self.baud_combo)
        layout.addLayout(baud_layout)

        lora_group = QGroupBox("Konfiguracja LoRa")
        lora_layout = QVBoxLayout()

        freq_layout = QHBoxLayout()
        freq_layout.addWidget(
            QLabel("Częstotliwość (MHz):"))
        self.freq_combo = QComboBox()
        self.freq_combo.addItems(["433", "868", "915"])
        self.freq_combo.setCurrentIndex(1)
        freq_layout.addWidget(self.freq_combo)
        lora_layout.addLayout(freq_layout)

        bw_layout = QHBoxLayout()
        bw_layout.addWidget(
            QLabel("Szerokość pasma (kHz):"))
        self.bw_combo = QComboBox()
        self.bw_combo.addItems(["125", "250", "500"])
        self.bw_combo.setCurrentIndex(0)
        bw_layout.addWidget(self.bw_combo)
        lora_layout.addLayout(bw_layout)

        sf_layout = QHBoxLayout()
        sf_layout.addWidget(QLabel("Spreading Factor:"))
        self.sf_combo = QComboBox()
        self.sf_combo.addItems(
            ["7", "8", "9", "10", "11", "12"])
        self.sf_combo.setCurrentIndex(3)  # SF10
        sf_layout.addWidget(self.sf_combo)
        lora_layout.addLayout(sf_layout)

        cr_layout = QHBoxLayout()
        cr_layout.addWidget(QLabel("Coding Rate:"))
        self.cr_combo = QComboBox()
        self.cr_combo.addItems(["4/5", "4/6", "4/7", "4/8"])
        self.cr_combo.setCurrentIndex(0)
        cr_layout.addWidget(self.cr_combo)
        lora_layout.addLayout(cr_layout)

        tx_layout = QHBoxLayout()
        tx_layout.addWidget(QLabel("Moc nadawania (dBm):"))
        self.tx_combo = QComboBox()
        self.tx_combo.addItems(
            ["2", "5", "8", "11", "14", "17", "20"])
        self.tx_combo.setCurrentIndex(6)  # 20 dBm
        tx_layout.addWidget(self.tx_combo)
        lora_layout.addLayout(tx_layout)

        lora_group.setLayout(lora_layout)
        layout.addWidget(lora_group)

        btn_layout = QHBoxLayout()
        connect_btn = QPushButton("Połącz i konfiguruj")
        connect_btn.clicked.connect(self.accept)
        connect_btn.setStyleSheet(
            "background-color: #27ae60;")

        connect_no_lora_btn = QPushButton(
            "Połącz bez konfiguracji")
        connect_no_lora_btn.clicked.connect(
            self.accept_no_lora)
        connect_no_lora_btn.setStyleSheet(
            "background-color: #2980b9;")

        cancel_btn = QPushButton("Kontynuuj bez portu")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(
            "background-color: #e74c3c;")

        btn_layout.addWidget(connect_btn)
        btn_layout.addWidget(connect_no_lora_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        if ports:
            for port in ports:
                self.port_combo.addItem(port.device)
        else:
            self.port_combo.addItem(
                "Brak dostępnych portów")

    def accept(self):
        self._get_settings()
        super().accept()

    def accept_no_lora(self):
        self.lora_config = None
        self._get_settings()
        super().accept()

    def _get_settings(self):
        if self.port_combo.currentText() == "Brak dostępnych portów":
            self.port_name = ""
        else:
            self.port_name = self.port_combo.currentText()

        self.baud_rate = int(self.baud_combo.currentText())

        if self.lora_config is not None:
            self.lora_config = {
                'frequency': self.freq_combo.currentText(),
                'bandwidth': self.bw_combo.currentText(),
                'spreading_factor': self.sf_combo.currentText(),
                'coding_rate': self.cr_combo.currentText(),
                'power': self.tx_combo.currentText()
            }

    def get_settings(self):
        return {
            'port': self.port_name,
            'baudrate': self.baud_rate,
            'lora_config': self.lora_config
        }