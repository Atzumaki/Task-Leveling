from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from Widgets import TaskTable
from PyQt5.QtWidgets import QCalendarWidget
from database import save_table_data, load_table_data


class Central:
    def __init__(self, size, color):
        self.size = size
        self.color = color
        self.window = QWidget()
        self.x = size[0]
        self.y = size[1]
        self.calendar = None
        self.table_wind = None
        self.start_screen()

    def start_screen(self):
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
        self.calendar.activated.connect(self.time_table)
        layout.addWidget(self.calendar, alignment=Qt.AlignCenter)
        self.window.setLayout(layout)
        self.window.show()

    def time_table(self, date):
        table_wind = QWidget()
        table_wind.setWindowTitle(f"{date.toString('dd.MM.yyyy')} — Таблица задач")
        table_wind.setStyleSheet("background-color: #081436; color: white; font-size: 20px;")
        table_wind.resize(self.size[0], self.size[1])

        layout = QVBoxLayout()
        date_str = date.toString("yyyy-MM-dd")

        # Кнопка "назад"
        back_button = QPushButton("Esc")
        back_button.setFixedSize(50, 50)
        back_button.setStyleSheet("""
            QPushButton {
                border-radius: 25px;
                background-color: #0078D7;
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005bb5;
            }
        """)

        def go_back():
            save_table_data(table, date_str)
            table_wind.close()

        back_button.clicked.connect(go_back)

        top_bar = QHBoxLayout()
        top_bar.addWidget(back_button, alignment=Qt.AlignLeft)
        top_bar.addStretch()

        layout.addLayout(top_bar)

        label = QLabel(f"Выбранная дата: {date.toString('dd.MM.yyyy')}")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        table = TaskTable(self.size)
        load_table_data(table, date_str)
        layout.addWidget(table)

        table_wind.setLayout(layout)
        table_wind.show()
        self.table_wind = table_wind