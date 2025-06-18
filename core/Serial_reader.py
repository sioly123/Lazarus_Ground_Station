import serial
import time
import re

class SerialReader:
    def __init__(self, port = "COM7", baudrate = 9600):
        self.port = port
        self.baudrate = baudrate
        self.velocity = 0.0
        self.pitch = 0.0
        self.roll = 0.0
        self.yaw = 0.0
        self.altitude = 0.0
        self.latitude = 0.0
        self.longitude = 0.0
        self.len = 0
        self.rssi = 0
        self.snr = 0
        try:
            self.ser = serial.Serial(self.port, self.baudrate)
        except serial.SerialException as e:
            self.ser = None
            print(f"Serial port error {e}",e)

    def ReadLine(self):
        if self.ser is not None:
            line = self.ser.readline().decode(errors='ignore').strip()
            return line
        else:
            print("Could not read line")

    def LoraSet(self):
        if self.ser is not None:
            self.ser.write(b'AT + MODE = TEST\n')
            time.sleep(1)
            self.ser.write(b'AT + TEST = RXLRPKT\n')
            time.sleep(1)
        else:
            print("Serial port error")

    def DecodeLine(self):
            line = self.ReadLine()
            if not line:
                return
            if line.startswith("+TEST: RX"):
                match = re.search(r'"([0-9A-Fa-f]+)"', line)
                if match:
                    hex_data = match.group(1)
                    byte_data = bytes.fromhex(hex_data)
                    decoded_string = byte_data.decode('utf-8', errors='replace')
                    data = decoded_string.split(";")
                    self.velocity = float(data[0])
                    self.pitch = float(data[1])
                    self.roll = float(data[2])
                    self.yaw = float(data[3])
                    self.altitude = float(data[4])
                    self.latitude = float(data[5])
                    self.longitude = float(data[6])
            else:
                pattern = r"\+TEST: LEN:(\d+), RSSI:(-?\d+), SNR:(-?\d+)"
                match = re.search(pattern, line)
                if match:
                    self.len = int(match.group(1))
                    self.rssi= int(match.group(2))
                    self.snr= int(match.group(3))
