import logging
from PyQt5.QtWidgets import QMainWindow, QTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import QTimer, Qt
from core.serial_reader import SerialReader
from gui.live_plot import LivePlot
from datetime import datetime
from core.process_data import ProcessData
from core.csv_handler import CsvHandler

class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.logger = logging.getLogger('Lazarus_Ground_Station.main_window')
        self.logger.info("Inicjalizacja głównego okna")

        self.now_str = ""
        self.console_update_counter = 0
        self.start_detection = False
        self.calib_detection = False
        self.apogee_detection = False
        self.recovery_detection = False
        self.landing_detection = False

        self.engine_detection = False

        self.current_data = {
            'velocity': 0.0,
            'altitude': 0.0,
            'pitch': 0.0,
            'roll': 0.0,
            'status': 0,
            'latitude': 0.0,
            'longitude': 0.0,
            'len': 0,
            'rssi': 0,
            'snr': 0
        }

        self.csv_handler = CsvHandler()
        self.logger.info(
            f"CSV handler zainicjalizowany w sesji: {self.csv_handler.session_dir}")

        self.signal_quality = "None"

        self.setWindowTitle("LoRa Telemetry")
        self.setStyleSheet("background-color: black; color: white;")

        self.serial = SerialReader(config['port'], config['baudrate'])
        self.logger.info(f"SerialReader zainicjalizowany na porcie {config['port']} z baudrate {config['baudrate']}")
        self.processor = ProcessData()
        self.logger.info(
            f"Singleton ProcessData zainicjalizowany")

        if config['lora_config']:
            self.serial.LoraSet(config['lora_config'], config['is_config_selected'])
            self.logger.info(f"Konfiguracja LoRa ustawiona: {config['lora_config']}")

        self.serial.telemetry_received.connect(self.processor.handle_telemetry)
        self.serial.transmission_info_received.connect(self.processor.handle_transmission_info)
        self.processor.processed_data_ready.connect(self.handle_processed_data)

        # Wykresy
        self.alt_plot = LivePlot(title="Altitude", color='b')
        self.velocity_plot = LivePlot(title="Velocity", color='r')
        self.pitch_plot = LivePlot(title="Pitch", color='y')
        self.roll_plot = LivePlot(title="Roll", color='g')

        # Konsola
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("background-color: black; color: white; font-family: monospace;")

        # Etykiety
        self.label_info = QLabel(f"Pitch: {self.current_data['pitch']:.2f}°, Roll: {self.current_data['roll']:.2f}°\n"f"V: {self.current_data['velocity']:.2f} m/s, H: {self.current_data['altitude']:.2f} m")
        self.label_info.setStyleSheet("color: white; font-size: 18px;")

        self.label_pos = QLabel("Pos: --  --  ")
        self.label_pos.setStyleSheet("color: white; font-size: 18px;")

        # Przyciski
        self.start_button = QPushButton("Start")
        self.apogee_button = QPushButton("Apogee")
        self.landing_button = QPushButton("Descent")
        self.calib_button = QPushButton("Calibration: Off")
        self.engine_button = QPushButton("Engine: Off")
        self.recovery_button = QPushButton("Recovery: Off")
        self.signal_button = QPushButton("Signal: None")

        buttons = [
            self.start_button, self.apogee_button, self.landing_button,
            self.calib_button, self.engine_button, self.recovery_button,
            self.signal_button
        ]

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
        status_panel_widget = QWidget()
        status_panel_widget.setLayout(status_panel)
        status_panel_widget.setFixedWidth(210)
        top_row.addWidget(status_panel_widget)

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self.pitch_plot)
        bottom_row.addWidget(self.roll_plot)

        engine_panel = QVBoxLayout()
        engine_panel.addWidget(self.calib_button)
        engine_panel.addWidget(self.engine_button)
        engine_panel.addWidget(self.recovery_button)
        engine_panel.addWidget(self.signal_button)
        engine_panel_widget = QWidget()
        engine_panel_widget.setLayout(engine_panel)
        engine_panel_widget.setFixedWidth(210)
        bottom_row.addWidget(engine_panel_widget)

        main_layout.addLayout(top_row)
        main_layout.addLayout(bottom_row)
        main_layout.addWidget(self.console)

        central.setLayout(main_layout)
        self.setCentralWidget(central)

        self.serial.start_reading()

        # self.timer = QTimer()
        # self.timer.timeout.connect(self.update_data)
        # self.timer.start(500)
        # self.logger.info("Timer rozpoczęty, częstotliwość: 500 ms")

    def handle_processed_data(self, data):
        self.logger.debug(
            f"Odebrano dane przetworzone: {data}")
        self.current_data = data
        try:
            self.update_data()
            self.csv_handler.write_row(data)
        except Exception as e:
            self.logger.exception(
                f"Błąd w update_data(): {e}")

    def update_data(self):
        self.alt_plot.update_plot(self.current_data['altitude'])
        self.velocity_plot.update_plot(self.current_data['velocity'])
        self.pitch_plot.update_plot(self.current_data['pitch'])
        self.roll_plot.update_plot(self.current_data['roll'])
        self.label_info.setText(
            f"Pit: {self.current_data['pitch']:.2f}°, Rol: {self.current_data['roll']:.2f}°\n"
            f"V: {self.current_data['velocity']:.2f} m/s, H: {self.current_data['altitude']:.2f} m"
        )
        self.label_pos.setText(
            f"LON:\t{self.current_data['longitude']:.6f}° N \nLAT:\t{self.current_data['latitude']:.6f}° E"
        )

        # print(self.current_data['status'])
        # print("Calib {}".format(self.current_data['status'] & (1 << 0)))
        # print("Start {}".format(self.current_data['status'] & (1 << 1)))
        # print("Engine {}".format(self.current_data['status'] & (1 << 2)))
        # print("Apogee {}".format(self.current_data['status'] & (1 << 3)))
        # print("Recovery {}".format(self.current_data['status'] & (1 << 4)))
        # print("Descent {}".format(self.current_data['status'] & (1 << 5)))

        self.now_str = datetime.now().strftime("%H:%M:%S")
        msg = (
            f"{self.current_data['velocity']};{self.current_data['altitude']};"
            f"{self.current_data['pitch']};{self.current_data['roll']};"
            f"{self.current_data['status']};{self.current_data['latitude']};"
            f"{self.current_data['longitude']}"
        )
        self.console.append(
            f"{self.now_str} | LEN: {self.current_data['len']} bajtów | "
            f"RSSI: {self.current_data['rssi']} dBm | "
            f"SNR: {self.current_data['snr']} dB | msg: {msg}"
        )
        self.logger.debug(f"Odebrano dane: {msg}")

        status = self.current_data['status']

        # Calibration
        if status & (1 << 0):
            if not self.calib_detection:
                self.calib_button.setStyleSheet(
                    "QPushButton {border: 2px solid white; border-radius: 5px; background-color: black; color: green; padding: 5px;}"
                )
                self.calib_button.setText("Calibration: On")
                self.console.append(f"{self.now_str} | CALIB ON")
                self.logger.info("Detekcja kalibracji")
                self.calib_detection = True
        else:
            if self.calib_detection:
                self.calib_button.setStyleSheet(
                    "QPushButton {border: 2px solid white; border-radius: 5px; background-color: black; color: red; padding: 5px;}"
                )
                self.calib_button.setText("Calibration: Off")
                self.calib_detection = False

        # Start
        if status & (1 << 1):
            if not self.start_detection:
                self.start_button.setStyleSheet(
                    "QPushButton {border: 2px solid white; border-radius: 5px; background-color: black; color: green; padding: 5px;}"
                )
                self.logger.info("Detekcja startu")
                self.console.append(f"{self.now_str} | START DETECTION")
                print("Detekcja startu")
                self.start_detection = True
        else:
            if self.start_detection:
                self.start_button.setStyleSheet(
                    "QPushButton {border: 2px solid white; border-radius: 5px; background-color: black; color: red; padding: 5px;}"
                )
                self.start_detection = False

        # Engine
        if status & (1 << 2):
            if not self.engine_detection:
                self.engine_button.setStyleSheet(
                    "QPushButton {border: 2px solid white; border-radius: 5px; background-color: black; color: green; padding: 5px;}"
                )
                self.engine_buttonn.setText("Engine: On")
                self.console.append(f"{self.now_str} | ENGINE ON")
                self.logger.info("Detekcja uruchomienia silników")
                self.engine_detection = True
        else:
            if self.engine_detection:
                self.engine_button.setStyleSheet(
                    "QPushButton {border: 2px solid white; border-radius: 5px; background-color: black; color: red; padding: 5px;}"
                )
                self.engine_buttonn.setText("Engine: Off")
                self.console.append(f"{self.now_str} | ENGINE OF")
                self.engine_detection = False

        # Apogee
        if status & (1 << 3):
            if not self.apogee_detection:
                self.apogee_button.setStyleSheet(
                    "QPushButton {border: 2px solid white; border-radius: 5px; background-color: black; color: green; padding: 5px;}"
                )
                self.console.append(f"{self.now_str} | APOGEE DETECTION")
                self.logger.info("Detekcja apogeum")
                self.apogee_detection = True
        else:
            if self.apogee_detection:
                self.apogee_button.setStyleSheet(
                    "QPushButton {border: 2px solid white; border-radius: 5px; background-color: black; color: red; padding: 5px;}"
                )
                self.apogee_detection = False

        # Recovery
        if status & (1 << 4):
            if not self.recovery_detection:
                self.recovery_button.setStyleSheet(
                    "QPushButton {border: 2px solid white; border-radius: 5px; background-color: black; color: green; padding: 5px;}"
                )
                self.recovery_button.setText("Recovery: On")
                self.console.append(f"{self.now_str} | RECOVERY DETECTION")
                self.logger.info("Detekcja odzysku")
                print("Detekcja odzysku")
                self.recovery_detection = True
        else:
            if self.recovery_detection:
                self.recovery_button.setStyleSheet(
                    "QPushButton {border: 2px solid white; border-radius: 5px; background-color: black; color: red; padding: 5px;}"
                )
                self.recovery_button.setText("Recovery: Off")
                self.recovery_detection = False

        # Landing
        if status & (1 << 5):
            if not self.landing_detection:
                self.landing_button.setStyleSheet(
                    "QPushButton {border: 2px solid white; border-radius: 5px; background-color: black; color: green; padding: 5px;}"
                )
                self.console.append(f"{self.now_str} | DESCENT DETECTION")
                self.logger.info("Detekcja lądowania")
                print("Detekcja lądowania")
                self.landing_detection = True
        else:
            if self.landing_detection:
                self.landing_button.setStyleSheet(
                    "QPushButton {border: 2px solid white; border-radius: 5px; background-color: black; color: red; padding: 5px;}"
                )
                self.landing_detection = False

        snr_threshold = 5.0
        rssi_threshold = -80.0
        snr = self.current_data['snr']
        rssi = self.current_data['rssi']

        if snr >= snr_threshold and rssi >= rssi_threshold:
            self.signal_quality = "Good"
            self.signal_button.setStyleSheet(
                "QPushButton {border: 2px solid white; border-radius: 5px; background-color: black; color: green; padding: 5px;}")
        elif snr < snr_threshold and rssi < rssi_threshold:
            self.signal_quality = "Weak"
            self.signal_button.setStyleSheet(
                "QPushButton {border: 2px solid white; border-radius: 5px; background-color: black; color: red; padding: 5px;}")
        else:
            self.signal_quality = "Average"
            self.signal_button.setStyleSheet(
                "QPushButton {border: 2px solid white; border-radius: 5px; background-color: black; color: yellow; padding: 5px;}")

        self.signal_button.setText(
            f"Signal: {self.signal_quality}")
        self.logger.debug(
            f"Jakość sygnału: {self.signal_quality} (SNR: {snr}, RSSI: {rssi})")

    def closeEvent(self, event):
        self.serial.stop_reading()
        self.csv_handler.close_file()
        super().closeEvent(event)