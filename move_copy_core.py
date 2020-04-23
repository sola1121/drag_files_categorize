import os, shutil

from PyQt5.QtCore import QThread


class WorkerThread(QThread):
    """工作线程"""
    def __init__(self, widget, src_path, dst_path, *argv, **kwargv):
        super().__init__(*argv, **kwargv)
        self.widget = widget
        self.src_path = src_path
        self.dst_path = dst_path

    def run(self):
        pass
