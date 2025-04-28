from datetime import timedelta, datetime
from pathlib import Path
import sqlite3
import sys
from PyQt5.QtCore import Qt

if getattr(sys, 'frozen', False):
    application_path = Path(sys.executable).parent
else:
    application_path = Path(__file__).parent

DB_FILE = application_path / "tasks.db"

#TODO Пофиксить SQL иньекции
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            date TEXT NOT NULL,
            row INTEGER NOT NULL,
            column INTEGER NOT NULL,
            content TEXT,
            PRIMARY KEY (date, row, column)
        )
    """)
    conn.commit()
    conn.close()


def save_table_data(table, date_str):
    """Сохраняет все данные из таблицы в БД по указанной дате"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    for row in range(table.rowCount()):
        for col in range(table.columnCount()):
            item = table.item(row, col)
            content = item.text() if item else ""
            cursor.execute("""
                INSERT OR REPLACE INTO tasks (date, row, column, content)
                VALUES (?, ?, ?, ?)
            """, (date_str, row, col, content))

    conn.commit()
    conn.close()


def load_table_data(table, date_str):
    """Загружает данные в таблицу из БД по указанной дате"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT row, column, content FROM tasks WHERE date = ?
    """, (date_str,))
    for row, col, content in cursor.fetchall():
        from PyQt5.QtWidgets import QTableWidgetItem
        item = QTableWidgetItem(content)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
        table.setItem(row, col, item)

    conn.close()

def transfer_unfinished_tasks(date_str):
    """Переносит невыполненные задачи на следующий день"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Получаем все задачи за дату
    cursor.execute("""
        SELECT row, column, content FROM tasks WHERE date = ?
    """, (date_str,))
    tasks = cursor.fetchall()

    # Определяем следующую дату
    current_date = datetime.strptime(date_str, "%Y-%m-%d")
    next_date = current_date + timedelta(days=1)
    next_date_str = next_date.strftime("%Y-%m-%d")

    # Находим невыполненные задачи
    tasks_by_row = {}
    for row, col, content in tasks:
        if row not in tasks_by_row:
            tasks_by_row[row] = {}
        tasks_by_row[row][col] = content

    for row, columns in tasks_by_row.items():
        done = columns.get(5, "")  # 5-я колонка — "Сделано"
        if done.strip().lower() not in ["1", "true", "yes", "да", "✔", "✓"]:
            for col, content in columns.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO tasks (date, row, column, content)
                    VALUES (?, ?, ?, ?)
                """, (next_date_str, row, col, content))

    conn.commit()
    conn.close()
