from System import Central
import pyautogui
import sys
from database import init_db
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    init_db()
    app = QApplication(sys.argv)
    central = Central(pyautogui.size(), color="#081436")
    sys.exit(app.exec_())