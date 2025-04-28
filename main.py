from System import Central
import pyautogui
import sys
from database import init_db
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    init_db()
    app = QApplication(sys.argv)

    try:
        screen_size = pyautogui.size()
        central = Central(size=screen_size, color="#081436")
        app.setQuitOnLastWindowClosed(True)
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Ошибка при запуске приложения: {e}")
        sys.exit(1)