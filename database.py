import sqlite3
from pathlib import Path

from PyQt5.QtCore import Qt

db_path = Path.home() / ".task_table_app"
db_path.mkdir(exist_ok=True)
DB_FILE = db_path / "tasks.db"

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
