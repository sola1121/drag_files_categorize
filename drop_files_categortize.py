import sys
import json
import random

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QFileDialog

from ui_window import MainWindow


AREA_HEIGHT = 45


class LabelAcceptDrop(QLabel):
    """接受拖入事件的标签"""
    def __init__(self, str, parent=None, flags=Qt.WindowFlags()):
        super().__init__(str, parent=parent, flags=flags)
        self.setAcceptDrops(True)
        self.origin_style = self.styleSheet()

    # FIXME: 拖拽功能有点问题

    def dragEnterEvent(self, QDragEnterEvent):
        self.setStyleSheet("background: red;")
        super().dragEnterEvent(QDragEnterEvent)

    def dragLeaveEvent(self, QDragLeaveEvent):
        # self.setStyleSheet(self.origin_style)
        self.setStyleSheet("background: blue;")
        super().dragLeaveEvent(QDragLeaveEvent)

    def dropEvent(self, QDropEvent):
        print("+++ {} +++".format(QDropEvent.mimeData()))


class RunMainWin(MainWindow):
    """调用主窗口"""
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.the_id = 0
        self.drop_groups = dict()

        self.area_add_action.triggered.connect(self.add_drop_area)
        self.config_input_aciton.triggered.connect(self.load_json_config)
        self.config_output_aciton.triggered.connect(self.down_json_config)
    
    def add_drop_area(self):
        """添加可拖拽区域"""
        new_drop_label = LabelAcceptDrop("测试内容{}".format(random.randint(0, 10)))
        new_drop_label.setAcceptDrops(True)
        new_drop_label.setFixedSize(330, AREA_HEIGHT)
        new_drop_label.setStyleSheet("color: blue; background-color: yellow")

        dir_drop_button = QPushButton(QIcon("icons/directory.png"), "定位目录")
        dir_drop_button.clicked.connect(lambda : self.find_drop_directory(new_drop_label))
        dir_drop_button.setFixedSize(80, AREA_HEIGHT)

        remove_area_button = QPushButton(QIcon("icons/reduce.png"), "移除区域")
        remove_area_button.clicked.connect(lambda : self.remove_drop_area(new_drop_label))
        remove_area_button.setFixedSize(80, AREA_HEIGHT)

        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(dir_drop_button)
        hbox_layout.addWidget(remove_area_button)
        
        dir_drop_button.clicked.connect(self.find_drop_directory)

        self.form_layout.addRow(new_drop_label, hbox_layout)
        self.resize(-1, self.height()+AREA_HEIGHT)

        new_drop_label.the_id = self.the_id
        dir_drop_button.the_id = self.the_id
        remove_area_button.the_id = self.the_id
        self.drop_groups[self.the_id] = [new_drop_label, dir_drop_button, remove_area_button]
        self.the_id += 1

    def find_drop_directory(self, item):
        """定义拖拽区域的定位目录"""
        pass

    def remove_drop_area(self, item):
        """移除可拖拽区域"""
        self.form_layout.removeRow(item)
        self.resize(-1, self.height()-AREA_HEIGHT)
        del self.drop_groups[item.the_id]

    def label_drop(self, drop_event):
        """当发生了拖入事件"""
        print(drop_event)

    def load_json_config(self):
        """载入json配置文件"""
        pass

    def down_json_config(self):
        """导出json配置文件"""
        pass


if __name__ == "__main__":

    app = QApplication(sys.argv)
    win = RunMainWin()
    win.show()
    sys.exit(app.exec())