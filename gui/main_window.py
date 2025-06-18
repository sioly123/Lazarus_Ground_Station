from PyQt5.QtWidgets import QMainWindow, QTextEdit, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import QTimer
from core.Serial_reader import SerialReader
from gui.live_plot import LivePlot
from datetime import datetime
from PyQt5 import QtGui

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LoRa Telemetry")

        self.serial = SerialReader("COM7", 9600)
        self.serial.LoraSet()

        # Tworzymy wykresy przed dodaniem do layoutu
        self.alt_plot = LivePlot(title="Altitude", color='c')
        self.velocity_plot = LivePlot(title="Velocity", color='m')

        self.console = QTextEdit()
        self.console.setReadOnly(True)

        central = QWidget()
        main_layout = QVBoxLayout()
        plots_layout = QHBoxLayout()

        plots_layout.addWidget(self.alt_plot)
        plots_layout.addWidget(self.velocity_plot)

        main_layout.addLayout(plots_layout)
        main_layout.addWidget(self.console)
        central.setLayout(main_layout)
        self.setCentralWidget(central)

        self.setStyleSheet("background-color: black; color: white;")
        self.console.setStyleSheet("background-color: black; color: white; font-family: monospace;")

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(50)

    def update_data(self):
        self.serial.DecodeLine()
        self.alt_plot.update_plot(self.serial.altitude)
        self.velocity_plot.update_plot(self.serial.velocity)
        now_str = datetime.now().strftime("%H:%M:%S")
        self.console.append(f"{now_str} | Vel: {self.serial.velocity:.2f}, Pitch: {self.serial.pitch:.2f}, Roll: {self.serial.roll:.2f}, "f"Yaw: {self.serial.yaw:.2f}, Alt: {self.serial.altitude:.2f}, Lat: {self.serial.latitude:.6f}, "f"Lon: {self.serial.longitude:.6f}, Len: {self.serial.len}, RSSI: {self.serial.rssi}, SNR: {self.serial.snr}")
