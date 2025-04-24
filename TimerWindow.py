import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                             QLabel, QPushButton, QHBoxLayout)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QBrush


class CircularTimer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Таймер")
        self.setFixedSize(400, 450)

        self.max_time = 30 # TODO загрузить в константы
        self.current_time = 0

        self.init_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.setInterval(1000)

    def init_ui(self):
        """Инициализация интерфейса"""
        self.setStyleSheet("""
            background-color: #0A1A3F;
            color: white;
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        self.time_label = QLabel("00:00:00")
        self.time_label.setFont(QFont("Arial", 28, QFont.Bold))
        self.time_label.setAlignment(Qt.AlignCenter)

        self.start_btn = QPushButton("▶ Старт")
        self.pause_btn = QPushButton("⏸ Пауза")
        self.reset_btn = QPushButton("↻ Сброс")

        btn_style = """
            QPushButton {
                background-color: #0078D7;
                color: white;
                border-radius: 5px;
                padding: 6px 12px;
                min-width: 80px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0095FF;
            }
            QPushButton:disabled {
                background-color: #505050;
            }
        """

        for btn in [self.start_btn, self.pause_btn, self.reset_btn]:
            btn.setStyleSheet(btn_style)
            btn.setFixedHeight(40)

        self.pause_btn.setEnabled(False)

        self.start_btn.clicked.connect(self.start_timer)
        self.pause_btn.clicked.connect(self.pause_timer)
        self.reset_btn.clicked.connect(self.reset_timer)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addStretch(1)

        main_layout.addStretch(1)
        main_layout.addWidget(self.time_label, 0, Qt.AlignCenter)
        main_layout.addStretch(1)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def start_timer(self):
        if self.current_time >= self.max_time:
            return

        self.timer.start()
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)

    def pause_timer(self):
        self.timer.stop()
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)

    def reset_timer(self):
        self.timer.stop()
        self.current_time = 0
        self.update_display()
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)

    def update_timer(self):
        self.current_time += 1
        self.update_display()

        if self.current_time >= self.max_time:
            self.timer.stop()
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(False)

    def update_display(self):
        hours = self.current_time // 3600
        minutes = (self.current_time % 3600) // 60
        seconds = self.current_time % 60
        self.time_label.setText(f"{hours:02}:{minutes:02}:{seconds:02}")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        circle_diameter = 250
        x = (self.width() - circle_diameter) // 2
        y = (self.height() - circle_diameter) // 2 - 30

        circle_rect = self.rect().adjusted(
            x, y,
            -(self.width() - circle_diameter - x),
            -(self.height() - circle_diameter - y)
        )

        pen_width = 12
        bg_pen = QPen(QColor("#404040"), pen_width)
        progress_pen = QPen(QColor("#0078D7"), pen_width)
        progress_pen.setCapStyle(Qt.RoundCap)

        painter.setPen(bg_pen)
        painter.drawEllipse(circle_rect)

        if self.current_time > 0:
            progress = min(self.current_time / self.max_time, 1.0)
            angle = int(360 * progress)

            painter.setPen(progress_pen)
            painter.drawArc(circle_rect, 90 * 16, -angle * 16)
            label_x = circle_rect.center().x() - self.time_label.width() // 2
            label_y = circle_rect.center().y() - self.time_label.height() // 2
            self.time_label.move(label_x, label_y)
