#!/usr/bin/env python3

import sys

from PyQt5.QtWidgets import QApplication

from categortize_core import RunMainWin

class Main():
    def __init__(self, argv):
        self.app = QApplication(argv)
        self.win = RunMainWin()
    
    def run(self):
        self.win.show()
        sys.exit(self.app.exec())


if __name__ == "__main__":
    
    main = Main(sys.argv)
    main.run()
    