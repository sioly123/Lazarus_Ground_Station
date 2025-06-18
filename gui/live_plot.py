import pyqtgraph as pg
pg.setConfigOptions(useOpenGL=True)
from PyQt5.QtWidgets import QWidget, QVBoxLayout

class LivePlot(QWidget):
    def __init__(self, title="Wykres", max_points=100, color='y'):
        super().__init__()
        self.max_points = max_points
        self.data = []

        self.plot_widget = pg.PlotWidget(title=title)
        self.plot_widget.showGrid(x=True, y=True)
        pen = pg.mkPen(color=color, width=2)
        self.curve = self.plot_widget.plot(pen=pen)

        layout = QVBoxLayout()
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)

    def update_plot(self, new_value: float):
        self.data.append(new_value)
        if len(self.data) > self.max_points:
            self.data.pop(0)
        self.curve.setData(self.data)