from datetime import timedelta, datetime
from pathlib import Path
import sqlite3
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCheckBox, QTableWidgetItem

if getattr(sys, 'frozen', False):
    application_path = Path(sys.executable).parent
else:
    application_path = Path(__file__).parent

DB_FILE = application_path / "tasks.db"


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
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM tasks WHERE date = ?", (date_str,))
        conn.commit()

        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                if col == 5:
                    widget = table.cellWidget(row, col)
                    if widget:
                        checkbox = widget.findChild(QCheckBox)
                        content = "1" if checkbox.isChecked() else "0"
                    else:
                        content = "0"
                else:
                    item = table.item(row, col)
                    content = item.text() if item else ""

                cursor.execute("""
                    INSERT OR REPLACE INTO tasks (date, row, column, content)
                    VALUES (?, ?, ?, ?)
                """, (date_str, row, col, content))

        conn.commit()
        print(f"Данные для {date_str} успешно сохранены.")
    except Exception as e:
        print(f"Ошибка при сохранении данных: {e}")
    finally:
        conn.close()


def load_table_data(table, date_str):
    table.is_loading_data = True
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT row, column, content 
            FROM tasks 
            WHERE date = ? 
            ORDER BY row, column
        """, (date_str,))
        tasks = cursor.fetchall()
        table.setRowCount(0)
        max_row = max(task[0] for task in tasks) if tasks else 0
        table.setRowCount(max_row + 1)
        for row, col, content in tasks:
            if 0 <= row < table.rowCount() and 0 <= col < table.columnCount():
                item = QTableWidgetItem(content)
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                table.setItem(row, col, item)
        table.fill_empty_cells()

    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")
    finally:
        conn.close()
        table.is_loading_data = False


def transfer_unfinished_tasks(date_str):
    """Копирует только невыполненные задачи (где checkbox ≠ 1) на следующий день"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Получаем даты
        current_date = datetime.strptime(date_str, "%Y-%m-%d")
        next_date = current_date + timedelta(days=1)
        next_date_str = next_date.strftime("%Y-%m-%d")

        # 1. Удаляем ВСЕ существующие задачи следующего дня
        cursor.execute("DELETE FROM tasks WHERE date = ?", (next_date_str,))

        # 2. Находим ВСЕ задачи текущего дня
        cursor.execute("SELECT row, column, content FROM tasks WHERE date = ?", (date_str,))
        all_tasks = cursor.fetchall()

        # 3. Находим строки с выполненными задачами (checkbox = 1)
        cursor.execute("""
            SELECT DISTINCT row FROM tasks 
            WHERE date = ? AND column = 5 AND content = '1'
        """, (date_str,))
        completed_rows = {row[0] for row in cursor.fetchall()}

        # 4. Копируем только задачи из НЕ выполненых строк
        for row, col, content in all_tasks:
            if row not in completed_rows:  # Если строка не содержит checkbox=1
                cursor.execute("""
                    INSERT INTO tasks (date, row, column, content)
                    VALUES (?, ?, ?, ?)
                """, (next_date_str, row, col, content))

        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        print(f"Ошибка при переносе задач: {e}")
        return False
    finally:
        conn.close()
