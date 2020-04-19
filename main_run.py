#!/usr/bin/env python3

import sys

from PyQt5.QtWidgets import QApplication

from drop_files_categortize import RunMainWin


if __name__ == "__main__":

    app = QApplication(sys.argv)
    win = RunMainWin()
    win.show()
    sys.exit(app.exec())