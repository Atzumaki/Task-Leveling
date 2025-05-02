import math
import sqlite3
import sys
from pathlib import Path

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QCalendarWidget, QMessageBox
from PyQt5.QtCore import Qt, QObject, QEvent
from PyQt5.QtWidgets import QDialog, QVBoxLayout
from PyQt5.QtChart import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen
from PyQt5.QtCore import Qt

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
        self.date = None
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

    def show_time_table(self, date=""):
        if date == "":
            date = self.date
        else:
            self.date = date
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

        grafic_button = QPushButton("График энергии⚡")
        grafic_button.setFixedSize(180, 40)
        grafic_button.setStyleSheet(""" 
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
        grafic_button.clicked.connect(self.get_energy)

        transfer_button = QPushButton("Закончить день💨")
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
        top_bar.addWidget(back_button, alignment=Qt.AlignLeft)
        top_bar.addWidget(transfer_button, alignment=Qt.AlignLeft)
        top_bar.addWidget(grafic_button, alignment=Qt.AlignLeft)
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
        try:
            selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
            table = self.table_wind.findChild(TaskTable)

            if table:
                total_hours = 0.0
                valid = True

                for row in range(table.rowCount()):
                    item = table.item(row, 3)
                    if item and item.text().strip():
                        try:
                            hours = float(item.text())
                            total_hours += hours
                        except ValueError:
                            valid = False
                            break

                if not valid:
                    QMessageBox.warning(self.table_wind, "Ошибка",
                                        "Некорректные значения времени!")
                    return
                elif not math.isclose(total_hours, 24.0, rel_tol=0.01):
                    QMessageBox.warning(self.table_wind, "Ошибка",
                                        f"Сумма времени должна быть 24 часа!\nОсталось добавить: {24.0 - total_hours:.2f}")
                    return

                save_table_data(table, selected_date)

            if hasattr(self, 'table_wind') and self.table_wind:
                self.table_wind.deleteLater()
                self.table_wind = None

        except Exception as e:
            print(f"Ошибка при закрытии: {str(e)}")

    def clear_table(self):
        reply = QMessageBox.question(self.table_wind, 'Подтверждение очистки',
                                     "Вы уверены, что хотите полностью очистить таблицу задач?\n"
                                     "Все строки будут удалены, останется только одна пустая строка.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            table = self.table_wind.findChild(TaskTable)
            if table:
                selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")

                self.clear_data_from_db(selected_date)

                table.setRowCount(0)

                table.setRowCount(1)
                table.fill_empty_cells()

                self.close_table()
                self.show_time_table(self.calendar.selectedDate())

                QMessageBox.information(self.table_wind, 'Таблица очищена',
                                        'Все строки удалены, оставлена одна пустая строка!')

    def clear_data_from_db(self, date_str):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Удаляем все записи для указанной даты
        cursor.execute("DELETE FROM tasks WHERE date = ?", (date_str,))
        conn.commit()
        conn.close()

    def transfer_tasks(self):
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
                table = self.table_wind.findChild(TaskTable)
                if table:
                    save_table_data(table, selected_date)

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

    def get_energy(self):
        from database import get_time_by_categories
        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        time_data = get_time_by_categories(selected_date)
        self.show_time_distribution_chart(time_data, selected_date)

    def show_time_distribution_chart(self, time_data, date):
        dialog = QDialog()
        dialog.setWindowTitle(f"Распределение времени за {date}")
        dialog.resize(600, 400)
        dialog.setStyleSheet("background-color: #081436;")

        layout = QVBoxLayout(dialog)

        labels = ['Творческое', 'Умственное', 'Физическое', 'Восполнение']
        values = [
            time_data.get('column_6', 0),
            time_data.get('column_7', 0),
            time_data.get('column_8', 0),
            time_data.get('column_9', 0)
        ]

        bar_set = QBarSet("Часы")
        bar_set.append(values)
        bar_set.setColor(QColor("#0078D7"))

        series = QBarSeries()
        series.append(bar_set)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(f"Распределение времени за {date}")
        chart.setAnimationOptions(QChart.SeriesAnimations)

        chart.setBackgroundBrush(QBrush(QColor("#081436")))
        chart.setPlotAreaBackgroundBrush(QBrush(QColor("#081436")))
        chart.setPlotAreaBackgroundVisible(True)
        chart.setTitleBrush(QBrush(Qt.white))

        axis_x = QBarCategoryAxis()
        axis_x.append(labels)
        axis_x.setLabelsBrush(QBrush(Qt.white))
        axis_x.setLinePen(QPen(QColor("#1A2A48")))
        axis_x.setGridLineVisible(False)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, max(values) + 2)
        axis_y.setLabelsBrush(QBrush(Qt.white))
        axis_y.setLinePen(QPen(QColor("#1A2A48")))
        axis_y.setGridLinePen(QPen(QColor("#1A2A48")))
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        chart.legend().setVisible(False)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)

        layout.addWidget(chart_view)
        dialog.setLayout(layout)
        dialog.exec_()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            if obj == self.window:
                self.window.close()
            elif obj == self.table_wind:
                if self.table_wind:
                    table = self.table_wind.findChild(TaskTable)
                    if table:
                        self.close_table()
            return True
        if event.type() == QEvent.Close and obj == self.table_wind:
            self.close_table()
            event.ignore()
            return True
        return super().eventFilter(obj, event)
