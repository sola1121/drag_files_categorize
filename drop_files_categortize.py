import os, json
import random
from collections import OrderedDict
from urllib.parse import unquote

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox, QSizePolicy

from exceptions import *
from ui_config import *
from ui_window import MainWindow


class LabelAcceptDrop(QLabel):
    """接受拖入事件的标签"""
    def __init__(self, str, parent=None, flags=Qt.WindowFlags()):
        super().__init__(str, parent=parent, flags=flags)
        self.setAcceptDrops(True)
        self.setWordWrap(True)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setAlignment(Qt.AlignTop)
        label_font = QFont()
        label_font.setPointSize(LABEL_FONT_SIZE)
        self.setFont(label_font)
        self.setStyleSheet(LABEL_INIT_STYLE_SHEET)

        self.the_id = None
    
    def dragEnterEvent(self, event):
        """重载进入事件"""
        print("+++++++++++ 进入事件")
        if event.mimeData().hasUrls():
            # event.acceptProposedAction()
            event.accept()
            self.setStyleSheet(LABEL_ENTER_STYLE_SHEET)
        else:
            event.ignore()
            # super(self).dragEnterEvent(event)

    def dragLeaveEvent(self, event):
        """重载离开事件"""
        print('----------- 出去事件')
        self.setStyleSheet(LABEL_LEAVE_STYLE_SHEET)

    def dropEvent(self, event):
        """重载拖入释放事件"""
        if event.mimeData().hasUrls():
            # 遍历输出拖动进来的所有文件路径
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                print(path)
                print(unquote(path))
            text = event.mimeData().text()
            print(text)
            event.acceptProposedAction()
            self.setStyleSheet("")
        else:
            event.ignore()


class RunMainWin(MainWindow):
    """调用主窗口"""
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.the_id = 0                    # 自增键
        self.drop_groups = OrderedDict()   # 用于拖拽的对象储存
        self.button_font = QFont()         # 用于button的QFont
        self.button_font.setPointSize(BUTTON_FONT_SIZE)

        self.area_add_action.triggered.connect(lambda : self.add_drop_area(add_height=True))
        self.config_input_aciton.triggered.connect(self.reload_json_config)
        self.config_output_aciton.triggered.connect(self.down_json_config)

        self.load_json_config(DIRECTORIES_CONFIG, disable_auto_load=False)
    
    def add_drop_area(self, label_dir=None, add_height=False):
        """添加可拖拽区域"""
        # 拖拽区域, 使用label
        new_drop_label = LabelAcceptDrop("测试内容{}".format(random.randint(0, 10)))
        new_drop_label.setFixedSize(DROP_AREA_LABEL_WIDTH, DROP_AREA_HEIGHT)
        if label_dir:
            new_drop_label.setText(label_dir)
            new_drop_label.setToolTip(label_dir)
        # 拖拽区域, 定位目录
        dir_drop_button = QPushButton(QIcon(DIRECTORY_ICON), "定位\n目录")
        dir_drop_button.setFont(self.button_font)
        dir_drop_button.clicked.connect(lambda : self.find_drop_directory(new_drop_label))
        dir_drop_button.setFixedSize(DROP_AREA_DIRECTORY_BUTTON_WIDTH, DROP_AREA_HEIGHT)
        # 拖拽区域, 移除区域
        remove_area_button = QPushButton(QIcon(REDUCE_ICON), "移除\n区域")
        remove_area_button.setFont(self.button_font)
        remove_area_button.clicked.connect(lambda : self.remove_drop_area(new_drop_label))
        remove_area_button.setFixedSize(DROP_AREA_REMOVE_BUTTON_WIDTH, DROP_AREA_HEIGHT)
        # 进行排版
        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(dir_drop_button)
        hbox_layout.addWidget(remove_area_button)   
        self.form_layout.addRow(new_drop_label, hbox_layout)
        if add_height:
            self.resize(-1, self.height()+DROP_AREA_HEIGHT)
        # 配置到drop_group中, 创建更方便的访问
        new_drop_label.the_id = self.the_id
        dir_drop_button.the_id = self.the_id
        remove_area_button.the_id = self.the_id
        self.drop_groups[self.the_id] = [new_drop_label, dir_drop_button, remove_area_button]
        self.the_id += 1

    def find_drop_directory(self, item_label):
        """定义拖拽区域的定位目录"""
        directory = QFileDialog.getExistingDirectory(parent=self, caption="指定目录")
        if directory:
            item_label.setText(directory)
            item_label.setToolTip(directory)

    def remove_drop_area(self, item_label):
        """移除可拖拽区域"""
        self.form_layout.removeRow(item_label)
        self.resize(-1, self.height()-DROP_AREA_HEIGHT)
        del self.drop_groups[item_label.the_id]

    def reload_json_config(self):
        """通过文件寻找载入json配置文件"""
        directory, file_type = QFileDialog.getOpenFileName(parent=self, 
            caption="载入配置好的目录", 
            filter="json config file(*.json)"
        )
        if directory and file_type:
            # 获得配置文件后, 先清除当前的, 然后在重新生成
            for label in [group_list[0] for group_list in self.drop_groups.values()]:
                self.remove_drop_area(label)
            self.load_json_config(directory, disable_auto_load=True)

    def load_json_config(self, directory, disable_auto_load=False):
        """启动时自动进行载入json配置文件, disable_auto_load选项用于禁用判断json配置中auto_load"""
        self.linedit_config_path.setText(str(directory))
        self.linedit_config_path.setToolTip(f"当前使用的配置目录: {directory}")
        not_exit_paths = list()   # 记录目录是否为空列表
        with open(directory, 'r') as file:
            try:
                content_dit = json.load(file)
                if content_dit["auto_load"] or disable_auto_load:  # 判断是否进行预读取, 对于一些情况需要禁用auto_load
                    for path in content_dit["paths_list"]:
                        if not os.path.exists(path):
                            not_exit_paths.append(path)
                        self.add_drop_area(path, add_height=False)   # 生成拖拽区域
                    if not_exit_paths:   # 如果记录不存在目录列表不为空, 进行提示, 说明有不存在的目录
                        not_exit_path_hint = "以下目录不存在, 如果接收拖拽, 将会尝试创建." 
                        for info in not_exit_paths:
                            not_exit_path_hint += "\n" + str(info)
                        QMessageBox.information(self, "目录不存在提醒", not_exit_path_hint)
            except Exception as ex:
                QMessageBox.warning(self, "json 载入错误", f"不能解析所给定的json文件: {directory}\n{ex}")

    def down_json_config(self):
        """导出json配置文件"""
        output_json = dict()
        paths_list = list()
        output_json["auto_load"] = False
        for label in [group_list[0] for group_list in self.drop_groups.values()]:
            paths_list.append(label.text())
        output_json["paths_list"] = paths_list
        new_file_dir, file_type = QFileDialog.getSaveFileName(self, caption="导出新的配置", filter="json config file(*.json)")
        if new_file_dir and file_type:
            with open(new_file_dir, 'w', encoding="utf-8") as file:
                json.dump(output_json, file, ensure_ascii=False)
