import serial
import time
import re
import logging
import threading
from PyQt5.QtCore import QObject, pyqtSignal


class SerialReader(QObject):
    telemetry_received = pyqtSignal(dict)
    transmission_info_received = pyqtSignal(dict)

    def __init__(self, port="COM7", baudrate=9600):
        super().__init__()
        self.logger = logging.getLogger(
            'Lazarus_Ground_Station.serial_reader')
        self.port = port
        self.baudrate = baudrate
        self.running = False
        self.thread = None

        try:
            self.ser = serial.Serial(self.port,
                                     self.baudrate,
                                     timeout=0.1)
            self.logger.info(
                f"Otworzono port {self.port} z baudrate {self.baudrate}")
        except serial.SerialException as e:
            self.ser = None
            self.logger.error(
                f"Błąd otwierania portu {self.port}: {e}")

    def start_reading(self):
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(
            target=self._read_serial)
        self.thread.daemon = True
        self.thread.start()
        self.logger.info(
            "Wątek odczytu szeregowego uruchomiony")

    def stop_reading(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.logger.info(
            "Wątek odczytu szeregowego zatrzymany")

    def _read_serial(self):
        while self.running and self.ser and self.ser.is_open:
            try:
                line = self.ser.readline().decode(
                    errors='ignore').strip()
                if line:
                    self.DecodeLine(line)
            except Exception as e:
                self.logger.error(f"Błąd odczytu: {e}")
                time.sleep(0.1)

    def DecodeLine(self, line):
        if line.startswith("+TEST: RX"):
            match = re.search(r'"([0-9A-Fa-f]+)"', line)
            if match:
                try:
                    hex_data = match.group(1)
                    byte_data = bytes.fromhex(hex_data)
                    decoded_string = byte_data.decode(
                        'utf-8', errors='replace')
                    data = decoded_string.split(";")

                    telemetry = {
                        'velocity': float(data[0]),
                        'pitch': float(data[1]),
                        'roll': float(data[2]),
                        'status': int(data[3]),
                        'altitude': float(data[4]),
                        'latitude': float(data[5]),
                        'longitude': float(data[6])
                    }

                    self.logger.info(
                        f"Dane telemetryczne: "
                        f"V={telemetry['velocity']}, "
                        f"P={telemetry['pitch']}, "
                        f"R={telemetry['roll']}, "
                        f"ST={telemetry['status']}, "
                        f"ALT={telemetry['altitude']}, "
                        f"LAT={telemetry['latitude']}, "
                        f"LON={telemetry['longitude']}")

                    self.telemetry_received.emit(telemetry)
                except Exception as e:
                    self.logger.error(
                        f"Błąd dekodowania danych: {e}")
        else:
            pattern = r"\+TEST: LEN:(\d+), RSSI:(-?\d+), SNR:(-?\d+)"
            match = re.search(pattern, line)
            if match:
                try:
                    transmission = {
                        'len': int(match.group(1)),
                        'rssi': int(match.group(2)),
                        'snr': int(match.group(3))
                    }

                    self.logger.debug(
                        f"Parametry transmisji: "
                        f"LEN={transmission['len']}, "
                        f"RSSI={transmission['rssi']}, "
                        f"SNR={transmission['snr']}")

                    self.transmission_info_received.emit(
                        transmission)
                except Exception as e:
                    self.logger.warning(
                        f"Błąd odczytu parametrów transmisji: {e}")

    def LoraSet(self, config, is_config_selected):
        if self.ser is None:
            self.logger.warning("Port szeregowy nie jest dostępny, pomijam konfigurację LoRa")
            return

        try:
            self.logger.info("Rozpoczynanie konfiguracji LoRa...")
            self.ser.write(b'at\r\n')
            time.sleep(0.5)
            self.ser.write(b'at+mode=test\r\n')
            time.sleep(0.5)

            if is_config_selected:
                rf_cmd = (f'at+test=rfcfg,'
                       f'{config["frequency"]}.000,'
                       f'{config["spread_factor"]},'
                       f'{config["bandwidth"]},'
                       f'{config["txpr"]},'
                       f'{config["rxpr"]},'
                       f'{config["power"]},'
                       f'{config["crc"]},'
                       f'{config["iq"]},'
                       f'{config["net"]}\r\n')

                self.ser.write(rf_cmd.encode('utf-8'))
                self.logger.debug(
                    f"Wysłano komendę: {rf_cmd.strip()}")
                time.sleep(0.5)
            else:
                self.logger.debug("Nie wysłano komendy konfiguracyjnej do LoRa")

            self.ser.write(b'at+test=rxlrpkt\r\n')
            time.sleep(0.5)

            self.ser.reset_input_buffer()
            self.logger.info("Konfiguracja LoRa zakończona pomyślnie")
        except Exception as e:
            self.logger.error(f"Błąd podczas konfiguracji LoRa: {e}")
