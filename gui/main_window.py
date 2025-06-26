import logging
import folium
from PyQt5.QtWidgets import (QMainWindow, QTextEdit,
                             QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel,
                             QPushButton, QGridLayout,
                             QSizePolicy)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView
from core.serial_reader import SerialReader
from gui.live_plot import LivePlot
from datetime import datetime
from core.process_data import ProcessData
from core.csv_handler import CsvHandler


class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.logger = logging.getLogger(
            'Lazarus_Ground_Station.main_window')
        self.logger.info("Inicjalizacja głównego okna")

        self.now_str = ""
        self.console_update_counter = 0
        self.start_detection = False
        self.calib_detection = False
        self.apogee_detection = False
        self.descent_detection = False
        self.engine_detection = False
        self.recovery_detection = False

        self.current_data = {
            'velocity': 0.0,
            'altitude': 0.0,
            'pitch': 0.0,
            'roll': 0.0,
            'status': 0,
            'latitude': 52.2549,
            'longitude': 20.9004,
            'len': 0,
            'rssi': 0,
            'snr': 0
        }

        # Inicjalizacja mapy
        self.current_lat = self.current_data['latitude']
        self.current_lng = self.current_data['longitude']
        self.map = None
        self.map_view = None

        self.csv_handler = CsvHandler()
        self.logger.info(
            f"CSV handler zainicjalizowany w sesji: {self.csv_handler.session_dir}")

        self.signal_quality = "None"

        self.setWindowTitle("LoRa Telemetry")
        self.setStyleSheet("""
            background-color: black; 
            color: white;
        """)
        self.setMinimumSize(1200, 800)

        self.serial = SerialReader(config['port'],
                                   config['baudrate'])
        self.logger.info(
            f"SerialReader zainicjalizowany na porcie {config['port']} z baudrate {config['baudrate']}")
        self.processor = ProcessData()
        self.logger.info(
            f"Singleton ProcessData zainicjalizowany")

        if config['lora_config']:
            self.serial.LoraSet(config['lora_config'],
                                config[
                                    'is_config_selected'])
            self.logger.info(
                f"Konfiguracja LoRa ustawiona: {config['lora_config']}")

        self.serial.telemetry_received.connect(
            self.processor.handle_telemetry)
        self.serial.transmission_info_received.connect(
            self.processor.handle_transmission_info)
        self.processor.processed_data_ready.connect(
            self.handle_processed_data)

        self.init_ui()
        self.serial.start_reading()

    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika"""
        # Wykresy główne (altitude i velocity)
        self.alt_plot = LivePlot(title="Altitude",
                                 color='b')
        self.velocity_plot = LivePlot(title="Velocity",
                                      color='r')

        # Wykresy dolne (pitch i roll) - takie same rozmiary jak górne
        self.pitch_plot = LivePlot(title="Pitch", color='y')
        self.roll_plot = LivePlot(title="Roll", color='g')

        # Ustawienie takich samych rozmiarów dla wszystkich wykresów
        plot_height = 300
        for plot in [self.alt_plot, self.velocity_plot,
                     self.pitch_plot, self.roll_plot]:
            plot.setMinimumHeight(plot_height)
            plot.setSizePolicy(QSizePolicy.Expanding,
                               QSizePolicy.Expanding)

        # Konsola tekstowa
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMinimumHeight(100)
        self.console.setStyleSheet("""
            QTextEdit {
                background-color: #111;
                color: #eee;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid #333;
                border-radius: 3px;
                padding: 5px;
            }
        """)

        # Etykiety
        self.label_info = QLabel(
            "velocity: -- m/s, altitude: -- m \npitch: -- deg, roll: -- deg")
        self.label_info.setStyleSheet(
            "color: white; font-size: 16px;")
        self.label_pos = QLabel("Pos: --  --  ")
        self.label_pos.setStyleSheet(
            "color: white; font-size: 16px;")

        # Przyciski
        buttons = [
            ("Start", "start_button"),
            ("Apogee", "apogee_button"),
            ("Descent", "landing_button"),
            ("Calibration: Off", "calib_button"),
            ("Engine: Off", "engine_button"),
            ("Recovery: Off", "recovery_button"),
            ("Signal: None", "signal_button")
        ]

        for text, name in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid white;
                    border-radius: 3px;
                    color: red;
                    padding: 3px;
                    min-width: 120px;
                    margin: 1px;
                    font-size: 12px;
                }
            """)
            setattr(self, name, btn)

        # Mapa 250x250px
        self.initialize_map()
        self.map_view = QWebEngineView()
        self.map_view.setFixedSize(250, 250)
        self.map_view.setStyleSheet("""
            QWebEngineView {
                background-color: black;
                border: 1px solid #444;
                border-radius: 3px;
            }
        """)
        self.update_map_view()

        central = QWidget()
        main_layout = QGridLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Główny układ (QGridLayout)
        central = QWidget()
        main_layout = QGridLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Górny wiersz - altitude i velocity
        top_plots_row = QHBoxLayout()
        top_plots_row.setContentsMargins(0, 0, 0, 0)
        top_plots_row.setSpacing(5)
        top_plots_row.addWidget(self.alt_plot, 1)
        top_plots_row.addWidget(self.velocity_plot, 1)

        # Dolny wiersz - pitch i roll
        bottom_plots_row = QHBoxLayout()
        bottom_plots_row.setContentsMargins(0, 0, 0, 0)
        bottom_plots_row.setSpacing(5)
        bottom_plots_row.addWidget(self.pitch_plot, 1)
        bottom_plots_row.addWidget(self.roll_plot, 1)

        # Panel boczny
        side_panel = self.create_side_panel()

        # Ustawienie elementów w siatce
        main_layout.addLayout(top_plots_row, 0, 0)
        main_layout.addLayout(bottom_plots_row, 1, 0)
        main_layout.addWidget(self.console, 2, 0, 1,
                              2)  # Konsola na całą szerokość
        main_layout.addWidget(side_panel, 0, 1, 2,
                              1)  # Panel boczny obok wykresów

        ### NOWE PROPORCJE ###
        main_layout.setRowStretch(0,
                                  4)  # Górne wykresy - 45% wysokości
        main_layout.setRowStretch(1,
                                  4)  # Dolne wykresy - 45% wysokości
        main_layout.setRowStretch(2,
                                  1)  # Konsola - 10% wysokości (zmniejszona)

        # Proporcje kolumn (80% wykresy, 20% panel boczny)
        main_layout.setColumnStretch(0, 4)
        main_layout.setColumnStretch(1, 1)

        central.setLayout(main_layout)
        self.setCentralWidget(central)

    def create_side_panel(self):
        """Tworzy panel boczny z mapą i przyciskami"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(5)

        # Etykieta z danymi (nad mapą)
        layout.addWidget(self.label_info,
                         alignment=Qt.AlignCenter)

        # Mapa
        layout.addWidget(self.map_view,
                         alignment=Qt.AlignCenter)

        # Etykieta z pozycją (pod mapą)
        layout.addWidget(self.label_pos,
                         alignment=Qt.AlignCenter)

        # Przyciski w siatce
        button_grid = QGridLayout()
        button_grid.setContentsMargins(0, 0, 0, 0)
        button_grid.setSpacing(3)
        buttons = [
            (self.start_button, 0, 0),
            (self.apogee_button, 0, 1),
            (self.landing_button, 1, 0),
            (self.calib_button, 1, 1),
            (self.engine_button, 2, 0),
            (self.recovery_button, 2, 1),
            (self.signal_button, 3, 0, 1, 2)
        ]

        for btn, row, col, *span in buttons:
            if span:
                button_grid.addWidget(btn, row, col, *span)
            else:
                button_grid.addWidget(btn, row, col)

        layout.addLayout(button_grid)
        panel.setLayout(layout)
        panel.setMinimumWidth(270)
        panel.setMaximumWidth(300)
        return panel

    def initialize_map(self):
        """Inicjalizuje mapę 250x250px"""
        self.map = folium.Map(
            location=[self.current_lat, self.current_lng],
            zoom_start=18,
            width='250px',
            height='250px',
            control_scale=True,
            tiles='OpenStreetMap'
        )

        folium.Marker(
            [self.current_lat, self.current_lng],
            popup=f"WAT: {self.current_lat:.6f}, {self.current_lng:.6f}",
            icon=folium.Icon(color="green", icon="flag",
                             prefix='fa')
        ).add_to(self.map)

        self.map.save('map.html')

    def update_map_view(self):
        """Aktualizuje widok mapy"""
        self.map_view.setHtml(open('map.html').read())

    def handle_processed_data(self, data):
        self.logger.debug(
            f"Odebrano dane przetworzone: {data}")
        self.current_data = data
        try:
            self.update_data()
            self.csv_handler.write_row(data)

            if data['latitude'] != 0.0 and data[
                'longitude'] != 0.0:
                self.current_lat = data['latitude']
                self.current_lng = data['longitude']
                self.initialize_map()
                self.update_map_view()

        except Exception as e:
            self.logger.exception(
                f"Błąd w update_data(): {e}")

    def update_data(self):
        """Aktualizacja danych na interfejsie"""
        # Aktualizacja wykresów
        self.alt_plot.update_plot(
            self.current_data['altitude'])
        self.velocity_plot.update_plot(
            self.current_data['velocity'])
        self.pitch_plot.update_plot(
            self.current_data['pitch'])
        self.roll_plot.update_plot(
            self.current_data['roll'])

        # Aktualizacja konsoli
        self.console_update_counter += 1
        if self.console_update_counter >= 10:
            self.console_update_counter = 0
            self.now_str = datetime.now().strftime(
                "%H:%M:%S")
            msg = (
                f"{self.current_data['velocity']};{self.current_data['altitude']};"
                f"{self.current_data['pitch']};{self.current_data['roll']};"
                f"{self.current_data['status']};{self.current_data['latitude']};"
                f"{self.current_data['longitude']}")
            self.console.append(
                f"{self.now_str} | LEN: {self.current_data['len']} bajtów | "
                f"RSSI: {self.current_data['rssi']} dBm | "
                f"SNR: {self.current_data['snr']} dB | msg: {msg}"
            )
            self.console.ensureCursorVisible()

        # Aktualizacja przycisków statusu
        self.update_status_buttons()

        # Aktualizacja etykiet
        self.label_info.setText(
            f"Pitch: {self.current_data['pitch']:.2f}°, Roll: {self.current_data['roll']:.2f}°\n"
            f"V: {self.current_data['velocity']:.2f} m/s, H: {self.current_data['altitude']:.2f} m"
        )
        self.label_pos.setText(
            f"Pos: {self.current_data['latitude']:.6f}  {self.current_data['longitude']:.6f}")

    def update_status_buttons(self):
        """Aktualizacja stanu przycisków"""
        # Kalibracja
        if (self.current_data['status'] & (
                1 << 0)) and not self.calib_detection:
            self.update_button_style(self.calib_button,
                                     "Calibration: On",
                                     "green")
            self.calib_detection = True

        # Start
        if (self.current_data['status'] & (
                1 << 1)) and not self.start_detection:
            self.update_button_style(self.start_button,
                                     "Start", "green")
            self.start_detection = True

        # Jakość sygnału
        snr, rssi = self.current_data['snr'], \
        self.current_data['rssi']
        if snr >= 5.0 and rssi >= -80.0:
            self.update_signal_quality("Good", "green")
        elif snr < 5.0 and rssi < -80.0:
            self.update_signal_quality("Weak", "red")
        else:
            self.update_signal_quality("Average", "yellow")

    def update_button_style(self, button, text, color):
        """Aktualizuje styl przycisku"""
        button.setStyleSheet(f"""
            QPushButton {{
                border: 1px solid white;
                border-radius: 3px;
                background-color: black;
                color: {color};
                padding: 3px;
            }}
        """)
        button.setText(text)
        self.console.append(
            f"{datetime.now().strftime('%H:%M:%S')} | {text.upper()}")

    def update_signal_quality(self, quality, color):
        """Aktualizuje przycisk sygnału"""
        self.signal_quality = quality
        self.update_button_style(self.signal_button,
                                 f"Signal: {quality}",
                                 color)

    def closeEvent(self, event):
        """Zamykanie aplikacji"""
        self.serial.stop_reading()
        self.csv_handler.close_file()
        super().closeEvent(event)