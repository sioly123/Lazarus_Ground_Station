from PyQt5.QtWidgets import QMainWindow, QTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import QTimer, Qt
from core.serial_reader import SerialReader
from gui.live_plot import LivePlot
from datetime import datetime

class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()

        self.now_str = ""
        self.console_update_counter = 0
        self.start_detection = False
        self.calib_detection = False
        self.apogee_detection = False
        self.descent_detection = False
        self.engine_detection = False
        self.recovery_detection = False

        self.signal_quality = "None"

        self.setWindowTitle("LoRa Telemetry")
        self.setStyleSheet("background-color: black; color: white;")

        self.serial = SerialReader(config['port'],
                                   config['baudrate'])

        if config['lora_config']:
            self.serial.LoraSet(config['lora_config'])

        self.alt_plot = LivePlot(title="Altitude", color='b')
        self.velocity_plot = LivePlot(title="Velocity", color='r')
        self.pitch_plot = LivePlot(title="Pitch", color='y')
        self.roll_plot = LivePlot(title="Roll", color='g')

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("background-color: black; color: white; font-family: monospace;")

        self.label_info = QLabel("velocity: -- m/s, altitude: -- m \npitch: -- deg, roll: -- deg")
        self.label_info.setStyleSheet("color: white; font-size: 18px;")

        self.label_pos = QLabel("Pos: --  --  ")
        self.label_pos.setStyleSheet("color: white; font-size: 18px;")


        self.start_button = QPushButton("Start")
        self.apogee_button = QPushButton("Apogee")
        self.landing_button = QPushButton("Descent")
        self.calib_button = QPushButton("Calibration: Off")
        self.engine_button = QPushButton("Engine: Off")
        self.recovery_button = QPushButton("Recovery: Off")
        self.signal_button = QPushButton("Signal: None")

        buttons = [self.start_button, self.apogee_button, self.landing_button,self.calib_button,
                   self.engine_button, self.recovery_button, self.signal_button]

        for btn in buttons:
            btn.setStyleSheet("QPushButton {border: 2px solid white; border-radius: 5px; color: red; padding: 5px;}")

        central = QWidget()
        main_layout = QVBoxLayout()


        top_row = QHBoxLayout()
        top_row.addWidget(self.alt_plot)
        top_row.addWidget(self.velocity_plot)

        status_panel = QVBoxLayout()
        status_panel.addWidget(self.label_info)
        status_panel.addWidget(self.start_button)
        status_panel.addWidget(self.apogee_button)
        status_panel.addWidget(self.landing_button)
        status_panel.addWidget(self.label_pos)
        # status_panel.addStretch()
        status_panel_widget = QWidget()
        status_panel_widget.setLayout(status_panel)
        status_panel_widget.setFixedWidth(210)
        top_row.addWidget(status_panel_widget)

        # Bottom Row: Pitch | Roll | Engine Panel
        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self.pitch_plot)
        bottom_row.addWidget(self.roll_plot)

        engine_panel = QVBoxLayout()
        engine_panel.addWidget(self.calib_button)
        engine_panel.addWidget(self.engine_button)
        engine_panel.addWidget(self.recovery_button)
        engine_panel.addWidget(self.signal_button)
        # engine_panel.addStretch()
        engine_panel_widget = QWidget()
        engine_panel_widget.setLayout(engine_panel)
        engine_panel_widget.setFixedWidth(210)
        bottom_row.addWidget(engine_panel_widget)

        # Combine plots + panels
        main_layout.addLayout(top_row)
        main_layout.addLayout(bottom_row)
        main_layout.addWidget(self.console)

        central.setLayout(main_layout)
        self.setCentralWidget(central)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(50)

    def update_data(self):
        self.serial.DecodeLine()
        self.alt_plot.update_plot(self.serial.altitude)
        self.velocity_plot.update_plot(self.serial.velocity)
        self.pitch_plot.update_plot(self.serial.pitch)
        self.roll_plot.update_plot(self.serial.roll)

        self.console_update_counter += 1
        if self.console_update_counter >= 10:
            self.console_update_counter = 0
            self.now_str = datetime.now().strftime("%H:%M:%S")
            self.console.append(f"{self.now_str} |  LEN: {self.serial.len} bytes | RSSI: {self.serial.rssi} dBm | "f"SNR: {self.serial.snr} dB | msg: {self.serial.velocity};{self.serial.altitude};"f"{self.serial.pitch};{self.serial.roll};{self.serial.status};{self.serial.latitude};{self.serial.longitude} " )

        if ((self.serial.status & (1 << 0)) != 0) and not self.calib_detection:
            self.calib_button.setStyleSheet("QPushButton {border: 2px solid white; border-radius: 5px; background-color: black; color: green; padding: 5px;}")
            self.calib_button.setText("Calibration: On")
            self.now_str = datetime.now().strftime("%H:%M:%S")
            self.console.append(f"{self.now_str} | CALIBRATION ON")
            self.calib_detection = True
        if ((self.serial.status & (1 << 1)) != 0) and not self.start_detection:
            self.start_button.setStyleSheet("QPushButton {border: 2px solid white; border-radius: 5px; background-color: black; color: green; padding: 5px;}")
            self.now_str = datetime.now().strftime("%H:%M:%S")
            self.console.append(f"{self.now_str} | START DETECTED")
            self.start_detection = True
        snr_threshold = 5.0
        rssi_threshold = -80.0
        if self.serial.snr >= snr_threshold and self.serial.rssi >= rssi_threshold:
            self.signal_quality = "Good"
            self.signal_button.setStyleSheet("QPushButton {border: 2px solid white; border-radius: 5px; background-color: black; color: green; padding: 5px;}")
        elif self.serial.snr < snr_threshold and self.serial.rssi < rssi_threshold:
            self.signal_quality = "Poor"
            self.signal_button.setStyleSheet("QPushButton {border: 2px solid white; border-radius: 5px; background-color: black; color: red; padding: 5px;}")
        else:
            self.signal_quality = "Moderate"
            self.signal_button.setStyleSheet("QPushButton {border: 2px solid white; border-radius: 5px; background-color: black; color: yellow; padding: 5px;}")
        self.signal_button.setText(f"Signal: {self.signal_quality}")

        self.label_info.setText(f"Pitch: {self.serial.pitch:.2f}°, Roll: {self.serial.roll:.2f}°\n"f"V: {self.serial.velocity:.2f} m/s, H: {self.serial.altitude:.2f} m" )
        self.label_pos.setText(f"Pos: {self.serial.latitude:.6f}  {self.serial.longitude:.6f}")
