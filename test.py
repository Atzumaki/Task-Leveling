from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtWidgets
import sys


data = [("1", "Baharak", 10), ("2", "Darwaz", 60),
        ("3", "Fays abad", 20), ("4", "Ishkashim", 80),
        ("5", "Jurm", 100)]


class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.tw = QtWidgets.QTableWidget(0, 3)
        self.tw.setHorizontalHeaderLabels(["ID", "Name", "Progress"])
        for r, (_id, _name, _progress) in enumerate(data):
            it_id = QtWidgets.QTableWidgetItem(_id)
            it_name = QtWidgets.QTableWidgetItem(_name)
            self.tw.insertRow(self.tw.rowCount())
            for c, item in enumerate((it_id, it_name)):
                self.tw.setItem(r, c, item)
            cellProgress = QProgressBar() # Создаете свой виджет для отображения в ячейке
            cellProgress.setValue(int(_id)*10)
            self.tw.setCellWidget(r,2,cellProgress) # и говорите табличке что в ее ячейче будет виджет а не текст

        layout = QVBoxLayout()
        layout.addWidget(self.tw)
        button = QPushButton('Запуск')
        button.clicked.connect(self.button_click)
        layout.addWidget(button)
        self.setLayout(layout)

    def button_click(self):
        for i in range(self.tw.rowCount()):
            pb = self.tw.cellWidget(i,2) # получаете виджет ячейки
            pb.setValue(pb.value()+10) # делаете все что нужно



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())