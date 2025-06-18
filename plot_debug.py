import sys
import serial
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
from collections import deque

PORT = 'COM7'
BAUDRATE = 9600
TOTAL_VARS = 7
TARGET_INDEXES = [0, 1, 2, 3, 4]  # velocity, pitch, roll, yaw, altitude
VAR_NAMES = ['Velocity', 'Pitch', 'Roll', 'Yaw', 'Altitude']
HISTORY = 200

class SerialReader(QtCore.QThread):
    data_received = QtCore.pyqtSignal(list)

    def __init__(self, port, baudrate):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.running = True

    def run(self):
        try:
            with serial.Serial(self.port, self.baudrate, timeout=1) as ser:
                print("[INFO] Połączono z LoRa...")
                while self.running:
                    line = ser.readline().decode(errors='ignore').strip()
                    if '+TEST: RX "' in line:
                        try:
                            hex_data = line.split('"')[1]
                            ascii_str = bytearray.fromhex(hex_data).decode('ascii')
                            floats = [float(x) for x in ascii_str.strip().split(';') if x]
                            if len(floats) >= TOTAL_VARS:
                                selected = [floats[i] for i in TARGET_INDEXES]
                                self.data_received.emit(selected)
                        except Exception as e:
                            print(f"[ERROR] Dekodowanie: {e}")
        except Exception as e:
            print(f"[ERROR] Port COM: {e}")

    def stop(self):
        self.running = False
        self.wait()

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LoRa Live Plot – Velocity, Pitch, Roll, Yaw, Altitude")

        layout = QtWidgets.QVBoxLayout(self)
        self.plots = []
        self.curves = []
        self.buffers = [deque(maxlen=HISTORY) for _ in VAR_NAMES]

        for name in VAR_NAMES:
            plot = pg.PlotWidget(title=name)
            if name == 'Altitude':
                plot.setYRange(0, 1000)  # Dostosuj jeśli trzeba
            elif name == 'Velocity':
                plot.setYRange(-50, 50)
            else:
                plot.setYRange(-180, 180)
            curve = plot.plot(pen=pg.mkPen(color='cyan', width=2))
            layout.addWidget(plot)
            self.plots.append(plot)
            self.curves.append(curve)

        self.serial_thread = SerialReader(PORT, BAUDRATE)
        self.serial_thread.data_received.connect(self.update_plots)
        self.serial_thread.start()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.redraw)
        self.timer.start(100)

    def update_plots(self, data):
        for i, val in enumerate(data):
            self.buffers[i].append(val)

    def redraw(self):
        for i in range(len(VAR_NAMES)):
            self.curves[i].setData(list(self.buffers[i]))

    def closeEvent(self, event):
        self.serial_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 900)
    window.show()
    sys.exit(app.exec_())
