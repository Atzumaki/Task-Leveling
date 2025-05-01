import sqlite3
from pathlib import Path
import sys
from PyQt5.QtWidgets import QWidget, QHeaderView, QSizePolicy, QStyledItemDelegate, QStyleOptionViewItem, QStyle, \
    QAbstractItemDelegate, QApplication, QTextEdit, QPushButton, QCheckBox, QHBoxLayout, QVBoxLayout, QMessageBox, \
    QAbstractItemView
from PyQt5.QtCore import QTimer, Qt, QSize, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QTextDocument, QAbstractTextDocumentLayout, QTextOption, QCursor, \
    QPalette, QKeySequence
import math
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt5.uic.properties import QtGui, QtCore

from TimerWindow import CircularTimer

if getattr(sys, 'frozen', False):
    application_path = Path(sys.executable).parent
else:
    application_path = Path(__file__).parent

DB_FILE = application_path / "tasks.db"
bag = set()


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

        # Если ячейка выделена - заливаем фон
        if options.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        # Рисуем текст
        doc = QTextDocument()
        doc.setHtml(f"<span style='color:#0078D7;'>{options.text}</span>")
        doc.setTextWidth(option.rect.width())

        textRect = option.widget.style().subElementRect(QStyle.SE_ItemViewItemText, options)
        painter.translate(textRect.left(), textRect.top())
        clip = QRectF(0, 0, textRect.width(), textRect.height())
        painter.setClipRect(clip)

        ctx = QAbstractTextDocumentLayout.PaintContext()

        # Если ячейка выделена — меняем цвет текста на цвет текста выделения
        if options.state & QStyle.State_Selected:
            ctx.palette.setColor(QPalette.Text, option.palette.highlightedText().color())

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
    def __init__(self, size, date, parent=None):
        super().__init__(parent)
        self.size = size
        self.date = date
        self.is_loading_data = False

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
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)
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
                selection-background-color: #3399FF;  /* добавлено: яркий фон выделения */
                selection-color: white;                /* добавлено: текст внутри выделения */
            }
            QTableWidget QTableCornerButton::section {
                background-color: #0078D7;
                border: 1px solid #0A1A3F;
            }
        """)

        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.cellChanged.connect(self.check_last_row_input)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_table_right_click)
        self.fill_empty_cells()

        for col in range(self.columnCount()):
            if col != 4 and col != 5:
                delegate = WordWrapDelegate(self)
                self.setItemDelegateForColumn(col, delegate)

    def on_table_right_click(self, pos):
        index = self.indexAt(pos)
        if index.isValid():
            self.setFocus()
            QTimer.singleShot(50, lambda: self._show_row_menu(index.row()))

    def _show_row_menu(self, row):
        """Внутренний метод для отображения меню"""
        if hasattr(self, '_context_menu') and self._context_menu.isVisible():
            self._context_menu.close()

        # Создаем меню
        menu = QWidget(flags=Qt.Popup)
        layout = QVBoxLayout(menu)
        layout.setContentsMargins(5, 5, 5, 5)

        # Настройка стилей
        menu.setStyleSheet("""
            QWidget {
                background-color: #0A1A3F;
                border: 1px solid #0078D7;
                border-radius: 5px;
            }
            QPushButton {
                background-color: transparent;
                color: white;
                font-size: 14px;
                padding: 8px 16px;
                border: none;
                text-align: left;
                min-width: 180px;
            }
            QPushButton:hover {
                background-color: #0078D7;
            }
        """)

        # Добавляем кнопки с передачей menu как parent
        buttons = [
            ("🔁 Повторять задачу", lambda: self.toggle_repeating_task(row, menu)),
            ("🚫 Неповторять задачу", lambda: self.not_repeating_task(row, menu)),
            ("➕ Добавить строку вниз", lambda: self.add_row_below(row, menu)),
            ("❌ Удалить строку", lambda: self.delete_row(row, menu))
        ]

        for text, handler in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            layout.addWidget(btn)

        # Позиционирование
        global_pos = QCursor.pos()
        menu.adjustSize()
        menu.move(global_pos.x(), global_pos.y() - menu.height())

        # Сохраняем ссылку и показываем
        self._context_menu = menu
        menu.show()

    def create_done_checkbox(self, row, col):
        checkbox = QCheckBox()
        checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #ffffff;
                border: 2px solid #0078D7;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #0078D7;
                border: 2px solid #0078D7;
                border-radius: 3px;
            }
        """)
        checkbox.setMinimumSize(30, 30)
        checkbox.setMaximumSize(30, 30)
        self.update_checkbox_state(checkbox, row)
        checkbox.stateChanged.connect(
            lambda state, r=row, cb=checkbox: self.on_checkbox_changed(r, cb)
        )

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(checkbox)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        return container

    def update_checkbox_state(self, checkbox, row):
        date_str = self.date.toString("yyyy-MM-dd")

        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT content FROM tasks 
                WHERE date = ? AND row = ? AND column = 5
            """, (date_str, row))

            result = cursor.fetchone()
            is_checked = str(result[0]).strip() == "1" if result else False
            checkbox.setChecked(is_checked)

    def on_checkbox_changed(self, row, checkbox):
        date_str = self.date.toString("yyyy-MM-dd")
        new_state = "1" if checkbox.isChecked() else "0"

        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO tasks (date, row, column, content)
                VALUES (?, ?, ?, ?)
            """, (date_str, row, 5, new_state))
            conn.commit()

    def create_timer_button(self, row, col):
        button = QPushButton("Старт")
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # И контейнеру тоже

        return container

    def start_timer_for_row(self, row, column):
        self.timer_window = CircularTimer(row=row, table=self)
        self.timer_window.show()

    def toggle_repeating_task(self, row, w):
        # Добавляем эмоджи к названию задачи
        bag.add(row)
        item = self.item(row, 1)  # Колонка с названием задачи
        if item:
            text = item.text()
            if "🔁" not in text:
                item.setText(f"🔁 {text}")
            else:
                item.setText(text.replace("🔁", "").strip())

                # Сохраняем в базу данных
                date_str = self.date.toString("yyyy-MM-dd")
                with sqlite3.connect(DB_FILE) as conn:
                    cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO tasks (date, row, column, content)
                    VALUES (?, ?, ?, ?)
                """, (date_str, row, 1, item.text()))
                conn.commit()

                w.close()

    def not_repeating_task(self, row, w):
        if row in bag:
            bag.remove(row)
        # Удаляем эмоджи из названия задачи
        item = self.item(row, 1)  # Колонка с названием задачи
        if item:
            text = item.text()
            if "🔁" in text:
                item.setText(text.replace("🔁", "").strip())

                # Сохраняем в базу данных
                date_str = self.date.toString("yyyy-MM-dd")
                with sqlite3.connect(DB_FILE) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO tasks (date, row, column, content)
                        VALUES (?, ?, ?, ?)
                    """, (date_str, row, 1, item.text()))
                    conn.commit()

        w.close()

    def add_row_below(self, row, parent):
        date_str = self.date.toString("yyyy-MM-dd")
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE tasks
                SET row = row + 1
                WHERE date = ? AND row > ?
            """, (date_str, row))
            conn.commit()
        self.insertRow(row + 1)
        self.fill_row(row + 1)

        parent.close()

    def fill_row(self, row):
        """Заполняет строку виджетами и пустыми ячейками"""
        for col in range(self.columnCount()):
            if col == 4:  # Колонка с таймером
                # Создаем кнопку таймера только если ее еще нет
                if not self.cellWidget(row, col):
                    self.setCellWidget(row, col, self.create_timer_button(row, col))
            elif col == 5:  # Колонка с чекбоксом
                # Создаем чекбокс только если его еще нет
                if not self.cellWidget(row, col):
                    self.setCellWidget(row, col, self.create_done_checkbox(row, col))
            else:
                # Для текстовых ячеек - создаем только если ячейка пустая
                if not self.item(row, col):
                    item = QTableWidgetItem("")
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                    self.setItem(row, col, item)

    def delete_row(self, row, parent):
        if self.rowCount() <= 1:
            parent.close()
            return

        date_str = self.date.toString("yyyy-MM-dd")
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            cur.execute("""
                DELETE FROM tasks
                WHERE date = ? AND row = ?
            """, (date_str, row))
            cur.execute("""
                UPDATE tasks
                SET row = row - 1
                WHERE date = ? AND row > ?
            """, (date_str, row))
            conn.commit()
        self.removeRow(row)
        parent.close()

    def check_last_row_input(self, row, col):
        if row == self.rowCount() - 1:
            item = self.item(row, col)
            if item and item.text().strip() and not self.is_loading_data:
                self.insertRow(self.rowCount())
                self.fill_row(self.rowCount() - 1)

    def fill_empty_cells(self):
        for row in range(self.rowCount()):
            self.fill_row(row)
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT row FROM tasks WHERE date = ? AND column = 1 AND content LIKE '%🔁%'",
                           (self.date.toString("yyyy-MM-dd"),))
            repeating_rows = {row[0] for row in cursor.fetchall()}
            bag.update(repeating_rows)
