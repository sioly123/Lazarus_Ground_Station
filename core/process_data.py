import re
import logging
from PyQt5.QtCore import QObject, pyqtSignal


class ProcessData(QObject):
    processed_data_ready = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(
            'Lazarus_Ground_Station.data_processor')
        self.current_telemetry = None
        self.current_transmission = None
        self.past = None

    def handle_telemetry(self, telemetry):
        self.current_telemetry = telemetry
        self.process_and_emit()

    def handle_transmission_info(self, transmission):
        self.current_transmission = transmission
        self.process_and_emit()

    def process_and_emit(self):
        if self.current_telemetry and self.current_transmission:
            combined_data = {**self.current_telemetry,
                             **self.current_transmission}
            self.processed_data_ready.emit(combined_data)