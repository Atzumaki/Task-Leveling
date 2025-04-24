from PyQt5.QtWidgets import QWidget, QHeaderView, QSizePolicy, QStyledItemDelegate, QStyleOptionViewItem, QStyle, \
    QAbstractItemDelegate, QApplication, QTextEdit, QPushButton, QCheckBox, QHBoxLayout
from PyQt5.QtCore import QTimer, Qt, QSize, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QTextDocument, QAbstractTextDocumentLayout, QTextOption, QCursor
import math
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt5.uic.properties import QtGui, QtCore

from TimerWindow import CircularTimer


class Line(QWidget):
    def __init__(self, width, length, color, isshine, parent=None):
        super().__init__(parent)

        self.width = width
        self.length = length
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


from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout, QPushButton, QSizePolicy, QStyledItemDelegate, QTextEdit, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class WordWrapTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWordWrapMode(QTextOption.WordWrap)
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def sizeHint(self):
        doc = self.document()
        doc.setTextWidth(self.viewport().width())
        height = doc.size().height()
        return QSize(super().sizeHint().width(), int(height) + 5)


class WordWrapDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.editor = None

    def createEditor(self, parent, option, index):
        self.editor = WordWrapTextEdit(parent)
        self.editor.setStyleSheet("""
            QTextEdit {
                font-size: 20px;
                border: 2px solid #0078D7;
                padding: 2px;
                color: #0078D7;
            }
        """)
        self.editor.textChanged.connect(lambda: self.adjustEditorSize(self.editor))
        return self.editor

    def adjustEditorSize(self, editor):
        QTimer.singleShot(0, lambda: editor.updateGeometry())

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        editor.setPlainText(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.toPlainText(), Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        table = index.model().parent()
        if table:
            editor.setFixedWidth(table.viewport().width() // 4)
            editor.setFixedHeight(table.viewport().width() // 6)
        editor.setGeometry(option.rect)
        self.adjustEditorSize(editor)

    def paint(self, painter, option, index):
        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)

        painter.save()

        doc = QTextDocument()
        doc.setHtml(f"<span style='color:#0078D7;'>{options.text}</span>")
        doc.setTextWidth(option.rect.width())

        textRect = option.widget.style().subElementRect(QStyle.SE_ItemViewItemText, options)
        painter.translate(textRect.left(), textRect.top())
        clip = QRectF(0, 0, textRect.width(), textRect.height())
        painter.setClipRect(clip)

        ctx = QAbstractTextDocumentLayout.PaintContext()
        ctx.clip = clip
        doc.documentLayout().draw(painter, ctx)

        painter.restore()

    def sizeHint(self, option, index):
        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)

        doc = QTextDocument()
        doc.setHtml(options.text)
        doc.setTextWidth(option.rect.width())

        height = doc.size().height()
        min_height = 30
        return QSize(int(doc.idealWidth()), max(int(height), min_height))


class TaskTable(QTableWidget):
    def __init__(self, size, parent=None):
        super().__init__(parent)
        self.size = size

        headers = [
            "Сфера деятельности",
            "Название задачи",
            "Продукт",
            "Время пот",
            "Время факт",
            "Сделано",
            "Творческая",
            "Умственная",
            "Физическая",
            "Восполнение"
        ]

        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.setRowCount(1)

        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
            QHeaderView::section {
                background-color: #0078D7;
                color: white;
                padding: 5px;
                font-size: 16px;
                border: 1px solid #0A1A3F;
            }
            QTableWidget {
                gridline-color: #0078D7;
                font-size: 14px;
            }
            QTableWidget QTableCornerButton::section {
                background-color: #0078D7;
                border: 1px solid #0A1A3F;
            }
        """)

        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.cellChanged.connect(self.check_last_row_input)
        self.verticalHeader().sectionClicked.connect(self.show_row_menu)

        self.fill_empty_cells()

        # Устанавливаем делегаты для ячеек
        for col in range(self.columnCount()):
            if col != 4:
                delegate = WordWrapDelegate(self)
                self.setItemDelegateForColumn(col, delegate)

    def show_row_menu(self, row):
        global_pos = QCursor.pos()
        w = QWidget(flags=Qt.Popup)
        layout = QHBoxLayout(w)
        add_btn = QPushButton("Добавить строку вниз")
        del_btn = QPushButton("Удалить строку")
        layout.addWidget(add_btn)
        layout.addWidget(del_btn)
        w.setStyleSheet("""
              QWidget {
                  background-color: #0A1A3F;
              }
              QPushButton {
                  background-color: #0078D7;
                  color: white;
                  font-size: 14px;
                  padding: 5px 10px;
                  border: none;
                  border-radius: 4px;
              }
              QPushButton:hover {
                  background-color: #3399FF;
              }
          """)
        w.move(global_pos)
        w.show()
        add_btn.clicked.connect(lambda: self.add_row_below(row, w))
        del_btn.clicked.connect(lambda: self.delete_row(row, w))

    def create_timer_button(self, row, col):
        button = QPushButton("Старт")
        button.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                padding: 3px;
                font-size: 14px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #3399FF;
            }
        """)
        button.setMinimumHeight(30)
        button.clicked.connect(lambda: self.start_timer_for_row(row, col))

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(button)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        return container

    def start_timer_for_row(self, row, column):
        self.timer_window = CircularTimer(self, row, column)
        self.timer_window.show()

    def add_row_below(self, row, parent):
        self.insertRow(row + 1)
        for col in range(self.columnCount()):
            if col == 4:
                self.setCellWidget(row + 1, col, self.create_timer_button(row + 1, col))
            else:
                item = QTableWidgetItem("")
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                self.setItem(row + 1, col, item)
        parent.close()

    def fill_row(self, row):
        for col in range(self.columnCount()):
            if col == 4:
                self.setCellWidget(row, col, self.create_timer_button(row, col))
            else:
                item = QTableWidgetItem("")
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                self.setItem(row, col, item)

    def delete_row(self, row, parent):
        if self.rowCount() > 1:
            self.removeRow(row)
        parent.close()

    def check_last_row_input(self, row, col):
        if row == self.rowCount() - 1 and self.item(row, col).text().strip():
            self.insertRow(self.rowCount())
            self.fill_row(self.rowCount() - 1)

    def fill_empty_cells(self):
        for row in range(self.rowCount()):
            self.fill_row(row)
