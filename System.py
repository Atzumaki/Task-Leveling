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
        self.date = None

    def show_time_table(self, date=""):
        if date == "":
            date = self.date
        else:
            self.date = date
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
        back_button.clicked.connect(self.close_table)

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

        table = TaskTable(self.size, self.date)
        load_table_data(table, date_str)
        layout.addWidget(table)

        self.table_wind.setLayout(layout)
        self.table_wind.show()

    def close_table(self):
        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        table = self.table_wind.findChild(TaskTable)
        if table:
            save_table_data(table, selected_date)
        self.table_wind.close()

    def clear_table(self):
        """Очистить таблицу, оставляя только одну пустую строку"""
        reply = QMessageBox.question(self.table_wind, 'Подтверждение очистки',
                                     "Вы уверены, что хотите полностью очистить таблицу задач?\n"
                                     "Все строки будут удалены, останется только одна пустая строка.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            table = self.table_wind.findChild(TaskTable)
            if table:
                # Сохраняем дату для обновления
                selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")

                # Очищаем данные в базе данных
                self.clear_data_from_db(selected_date)

                # Полностью очищаем таблицу
                table.setRowCount(0)  # Удаляем все строки

                # Добавляем одну пустую строку
                table.setRowCount(1)
                table.fill_empty_cells()

                # Закрываем и заново открываем таблицу для обновления
                self.close_table()
                self.show_time_table(self.calendar.selectedDate())

                QMessageBox.information(self.table_wind, 'Таблица очищена',
                                        'Все строки удалены, оставлена одна пустая строка!')

    def clear_data_from_db(self, date_str):
        """Очистить данные таблицы в базе данных по указанной дате"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Удаляем все записи для указанной даты
        cursor.execute("DELETE FROM tasks WHERE date = ?", (date_str,))
        conn.commit()
        conn.close()

    def transfer_tasks(self):
        """Перенос задач на следующий день (без удаления из исходной таблицы)"""
        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")

        reply = QMessageBox.question(
            self.table_wind,
            'Подтверждение переноса',
            f"Перенести невыполненные задачи с {selected_date} на следующий день?\n"
            "Задачи останутся в исходной таблице.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # Сохраняем текущие данные перед переносом
                table = self.table_wind.findChild(TaskTable)
                if table:
                    save_table_data(table, selected_date)

                # Выполняем перенос (без удаления)
                from database import transfer_unfinished_tasks
                if transfer_unfinished_tasks(selected_date):

                    QMessageBox.information(
                        self.table_wind,
                        'Успех',
                        'Задачи успешно скопированы на следующий день!'
                    )
                else:
                    QMessageBox.warning(
                        self.table_wind,
                        'Ошибка',
                        'Ошибка при переносе задач!'
                    )

            except Exception as e:
                QMessageBox.critical(
                    self.table_wind,
                    'Ошибка',
                    f'Произошла ошибка: {str(e)}'
                )

    def eventFilter(self, obj, event):
        """Обработка событий клавиатуры"""
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            if obj == self.window:
                self.window.close()
            elif obj == self.table_wind:
                if self.table_wind:
                    table = self.table_wind.findChild(TaskTable)
                    if table:
                        self.close_table()
            return True
        return super().eventFilter(obj, event)

