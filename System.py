from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt
from Widgets import Line

class Central:
    def __init__(self, size, color):
        self.size = size
        self.color = color
        self.x = size[0]
        self.y = size[1]
        self.start()

    def start(self):
        self.window = QWidget()

        self.window.setWindowFlags(Qt.FramelessWindowHint)
        self.window.resize(self.size[0], self.size[1])
        self.window.setStyleSheet(f"background-color: {self.color};")
        line = Line(5, self.x - 5, (5, 5), color='#2F70AF', isshine=True, parent=self.window)
        line.setGeometry(0, 0, self.x, self.y)
        self.window.show()