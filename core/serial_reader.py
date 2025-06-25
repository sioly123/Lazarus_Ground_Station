import serial
import time
import re
import logging

class SerialReader:
    def __init__(self, port="COM7", baudrate=9600):
        self.logger = logging.getLogger('Lazarus_Ground_Station.serial_reader')

        self.port = port
        self.baudrate = baudrate
        self.velocity = 0.0
        self.pitch = 0.0
        self.roll = 0.0
        self.status = 0
        self.altitude = 0.0
        self.latitude = 0.0
        self.longitude = 0.0
        self.len = 0
        self.rssi = 0
        self.snr = 0

        try:
            self.ser = serial.Serial(self.port, self.baudrate)
            self.logger.info(f"Otworzono port {self.port} z baudrate {self.baudrate}")
        except serial.SerialException as e:
            self.ser = None
            self.logger.error(f"Błąd otwierania portu {self.port}: {e}")

    def ReadLine(self):
        if self.ser is not None:
            try:
                line = self.ser.readline().decode(errors='ignore').strip()
                # self.logger.debug(f"Odebrano linię: {line}") Podmienić na csv
                return line
            except Exception as e:
                self.logger.warning(f"Błąd podczas odczytu linii: {e}")
        else:
            self.logger.warning("Brak połączenia z portem szeregowym")
        return None

    def DecodeLine(self):
        line = self.ReadLine()
        if not line:
            return

        if line.startswith("+TEST: RX"):
            match = re.search(r'"([0-9A-Fa-f]+)"', line)
            if match:
                try:
                    hex_data = match.group(1)
                    byte_data = bytes.fromhex(hex_data)
                    decoded_string = byte_data.decode('utf-8', errors='replace')
                    data = decoded_string.split(";")

                    self.velocity = float(data[0])
                    self.pitch = float(data[1])
                    self.roll = float(data[2])
                    self.status = int(data[3])
                    self.altitude = float(data[4])
                    self.latitude = float(data[5])
                    self.longitude = float(data[6])

                    self.logger.info(f"Dane telemetryczne: V={self.velocity}, P={self.pitch}, R={self.roll}, ST={self.status}, ALT={self.altitude}, LAT={self.latitude}, LON={self.longitude}")
                except Exception as e:
                    self.logger.error(f"Błąd dekodowania danych: {e}")
        else:
            pattern = r"\+TEST: LEN:(\d+), RSSI:(-?\d+), SNR:(-?\d+)"
            match = re.search(pattern, line)
            if match:
                try:
                    self.len = int(match.group(1))
                    self.rssi = int(match.group(2))
                    self.snr = int(match.group(3))

                    self.logger.debug(f"Parametry transmisji: LEN={self.len}, RSSI={self.rssi}, SNR={self.snr}")
                except Exception as e:
                    self.logger.warning(f"Błąd odczytu parametrów transmisji: {e}")

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
