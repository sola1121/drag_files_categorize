#!/usr/bin/env python3

import sys

from importlib import util as imputil

THIRD_MODULE = 0
SELF_MODULE = 1

depend_modules = {
    "PyQt5": THIRD_MODULE, 
    "core.categortize": SELF_MODULE, 
    "core.move_copy": SELF_MODULE, 
    "window.ui_window": SELF_MODULE, 
    "window.ui_config": SELF_MODULE, 
    "common.exceptions": SELF_MODULE,
    "common.auxiliary_functions": SELF_MODULE,
}

for module in (depend_modules.keys()):
    if module not in sys.modules:
        if imputil.find_spec(module) is None:
            if depend_modules[module] == THIRD_MODULE:
                print("Third part module can't found. lack module '%s', can use pip to install." % module)
            else:
                print("Software damaged, missing '%s'." % module)
            sys.exit(1)

from PyQt5.QtWidgets import QApplication

from core.categortize import RunMainWin


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
    