import sqlite3
import sys
from pathlib import Path

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QCalendarWidget, QMessageBox
from PyQt5.QtCore import Qt, QObject, QEvent
from Widgets import TaskTable
from database import save_table_data, load_table_data


if getattr(sys, 'frozen', False):
    application_path = Path(sys.executable).parent
else:
    application_path = Path(__file__).parent

DB_FILE = application_path / "tasks.db"


class Central(QObject):
    def __init__(self, size, color):
        super().__init__()
        self.size = size
        self.color = color
        self.window = QWidget()
        self.window.installEventFilter(self)
        self.x = size[0]
        self.y = size[1]
        self.calendar = None
        self.table_wind = None
        self.initialize_ui()

    def initialize_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.window.setWindowFlags(Qt.FramelessWindowHint)
        self.window.resize(self.size[0], self.size[1])
        self.window.setStyleSheet("background-color: #081436")

        layout = QVBoxLayout()

        self.calendar = QCalendarWidget()
        self.calendar.setStyleSheet(""" 
            QCalendarWidget {
                background-color: #081436;
                color: white;
                border: 2px solid #0A1A3F;
                border-radius: 15px;
                padding: 5px;
            }
            QCalendarWidget QWidget {
                background-color: #0078D7;
            }
            QCalendarWidget QMenu {
                background-color: #0A1A3F;
                color: white;
            }
            QCalendarWidget QAbstractItemView {
                selection-background-color: #081436;
                selection-color: white;
                background-color: #0078D7;
                gridline-color: #14284A;
                font-size:25px;
            }
            QCalendarWidget QAbstractItemView::disabled {
                color: #444B6E;
            }
        """)
        self.calendar.setFixedSize(self.x - 80, self.y - 80)
        self.calendar.activated.connect(self.show_time_table)
        layout.addWidget(self.calendar, alignment=Qt.AlignCenter)
        self.window.setLayout(layout)
        self.window.show()

    def show_time_table(self, date):
        """Показать таблицу задач для выбранной даты"""
        self.table_wind = QWidget()
        self.table_wind.installEventFilter(self)
        self.table_wind.setWindowTitle(f"{date.toString('dd.MM.yyyy')} — Таблица задач")
        self.table_wind.setStyleSheet("background-color: #081436; color: white; font-size: 20px;")
        self.table_wind.resize(self.size[0], self.size[1])

        layout = QVBoxLayout()
        date_str = date.toString("yyyy-MM-dd")

        back_button = QPushButton("Назад (Esc)")
        back_button.setFixedSize(120, 40)
        back_button.setStyleSheet(""" 
            QPushButton {
                border-radius: 5px;
                background-color: #0078D7;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #005bb5;
            }
        """)
        back_button.clicked.connect(self.table_wind.close)

        transfer_button = QPushButton("Перенести задачи ➡️")
        transfer_button.setFixedSize(180, 40)
        transfer_button.setStyleSheet(""" 
                    QPushButton {
                        border-radius: 5px;
                        background-color: #0078D7;
                        color: white;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        background-color: #005bb5;
                    }
                """)
        transfer_button.clicked.connect(self.transfer_tasks)

        clear_button = QPushButton("Очистить таблицу")
        clear_button.setFixedSize(180, 40)
        clear_button.setStyleSheet("""
                    QPushButton {
                        border-radius: 5px;
                        background-color: #D72A2A;
                        color: white;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        background-color: #D21F1F;
                    }
                """)
        clear_button.clicked.connect(self.clear_table)

        top_bar = QHBoxLayout()
        top_bar.addWidget(transfer_button, alignment=Qt.AlignLeft)
        top_bar.addWidget(back_button, alignment=Qt.AlignLeft)
        top_bar.addWidget(clear_button, alignment=Qt.AlignLeft)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        label = QLabel(f"Выбранная дата: {date.toString('dd.MM.yyyy')}")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        table = TaskTable(self.size)
        load_table_data(table, date_str)
        layout.addWidget(table)

        self.table_wind.setLayout(layout)
        self.table_wind.show()

    def clear_table(self):
        """Очистить данные в таблице и базе данных (оставляя названия колонок)"""
        reply = QMessageBox.question(self.table_wind, 'Подтверждение очистки',
                                     "Вы уверены, что хотите очистить таблицу задач?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Очистить данные в таблице
            table = self.table_wind.findChild(TaskTable)
            if table:
                # Сохраняем количество строк и колонок
                row_count = table.rowCount()
                column_count = table.columnCount()

                # Очищаем все данные
                table.clearContents()

                # Восстанавливаем структуру таблицы
                table.setRowCount(row_count)
                table.setColumnCount(column_count)

                # Заполняем пустые ячейки
                table.fill_empty_cells()

                # Очищаем данные в базе данных
                selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
                self.clear_data_from_db(selected_date)

                QMessageBox.information(self.table_wind, 'Таблица очищена',
                                        'Таблица задач была очищена!')

    def clear_data_from_db(self, date_str):
        """Очистить данные таблицы в базе данных по указанной дате"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Удаляем все записи для указанной даты
        cursor.execute("DELETE FROM tasks WHERE date = ?", (date_str,))
        conn.commit()
        conn.close()

    def transfer_tasks(self):
        """Show confirmation dialog before transferring tasks inside the table window."""
        # Get the selected date
        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")

        # Create the confirmation dialog
        reply = QMessageBox.question(self.table_wind, 'Подтверждение переноса',
                                     f"Вы уверены, что хотите перенести задачи для {selected_date}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Proceed with the task transfer
            from database import transfer_unfinished_tasks
            transfer_unfinished_tasks(selected_date)
            # Show success message after transfer
            QMessageBox.information(self.table_wind, 'Задачи перенесены', 'Задачи успешно перенесены!')

    def eventFilter(self, obj, event):
        """Обработка событий клавиатуры"""
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            if obj == self.window:
                self.window.close()
            elif obj == self.table_wind:
                if self.table_wind:  # Если открыта таблица
                    table = self.table_wind.findChild(TaskTable)
                    if table:
                        from database import save_table_data
                        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
                        save_table_data(table, selected_date)
                self.table_wind.close()
            return True
        return super().eventFilter(obj, event)
