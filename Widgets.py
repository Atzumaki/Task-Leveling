from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPainter, QPen, QColor
import math


class Line(QWidget):
    def __init__(self, width, length, coord, color, isshine, parent=None):
        super().__init__(parent)

        self.width = width
        self.length = length
        self.coord = coord
        self.color = color
        self.current_color = QColor(0, 0, 0)
        self.isshine = isshine
        self.time = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_line)
        self.timer.start(16)

    def update_line(self):
        if self.isshine:
            self.time += 0.02
            variation = int((math.sin(self.time) * 50) + 105)
            r = 0
            g = max(0, min(255, variation))
            b = max(0, min(255, variation + 100))
            self.current_color = QColor(r, g, b)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(self.current_color)
        pen.setWidth(self.width)
        painter.setPen(pen)
        start_x, start_y = self.coord
        end_x = start_x + self.length
        end_y = start_y
        painter.drawLine(start_x, start_y, end_x, end_y)
