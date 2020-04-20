import os, shutil, filecmp, json, itertools
from collections import OrderedDict

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox, QDesktopWidget

from exceptions import *
from ui_config import *
from ui_window import MainWindow


### 控件类, 窗口类 ###
### REVIEW 功能性控件类, 功能性窗口类, 图形化界面的逻辑层

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
        self.setStyleSheet(LABEL_INIT_STYLESHEET)

        self.the_id = None

    def mousePressEvent(self, event):
        """重载点击事件, 显示磁盘容量"""
        try:
            statusbar = self.nativeParentWidget().statusBar()
            statusbar.clearMessage()
            if str(self.text()) == LABEL_PLACEHOLDER:
                return None
            if not os.path.exists(self.text()):
                return None
            disk_info = shutil.disk_usage(path=self.text())   # 单位KB
            disk_info_format = "根 {root} , 总容量: {total}GB 使用: {used}GB 空闲: {free}GB 使用率: {used_rate}%".format(
                   root = (os.path.splitdrive(self.text())[0]) if (os.path.splitdrive(self.text())[0]) else "/",
                   total = round(disk_info.total/1024**3, 2), 
                   used = round(disk_info.used/1024**3, 2), 
                   free = round(disk_info.free/1024**3, 2), 
                   used_rate = round(disk_info.used/disk_info.total*100, 2))
            statusbar.showMessage(disk_info_format)
        except Exception as ex:
            QMessageBox.warning(self.nativeParentWidget(), "获取磁盘使用失败", f"{ex}")

    def mouseDoubleClickEvent(self, event):
        """重载双击事件, 显示磁盘容量"""
        self.mousePressEvent(event)
    
    def dragEnterEvent(self, event):
        """重载进入事件"""
        print("+++++++++++ 进入事件")
        if event.mimeData().hasUrls():
            # event.acceptProposedAction()
            event.accept()
            self.setStyleSheet(LABEL_ENTER_STYLESHEET)
        else:
            event.ignore()
            # super(self).dragEnterEvent(event)

    def dragLeaveEvent(self, event):
        """重载离开事件"""
        print('----------- 出去事件')
        self.setStyleSheet(LABEL_LEAVE_STYLESHEET)

    # TODO: 主要功能开发, 使用shutil, filecmp, os开始对文件进行操作
    def dropEvent(self, event):
        """重载拖入释放事件"""
        if event.mimeData().hasUrls():
            print(self.the_id)
            # 遍历输出拖动进来的所有文件路径
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                print(path)
            text = event.mimeData().text()
            print(text)
            event.acceptProposedAction()
        else:
            event.ignore()
        self.setStyleSheet(LABEL_INIT_STYLESHEET)


class RunMainWin(MainWindow):
    """调用主窗口"""
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.the_id = 0                    # 自增键
        self.drop_groups = OrderedDict()   # 用于拖拽的对象储存
        self.button_font = QFont()         # 用于button的QFont
        self.button_font.setPointSize(BUTTON_FONT_SIZE)   # 设置按钮的字体大小
        self.move_or_cut_mode = self.move_copy_switch_action.data()   # 文件的处理模式, 剪切或复制

        self.area_add_action.triggered.connect(lambda : self.add_drop_area(adjust_size=True))
        self.move_copy_switch_action.triggered.connect(lambda : self.switch_mode(self.move_copy_switch_action.data()))
        self.config_input_aciton.triggered.connect(self.reload_json_config)
        self.config_output_aciton.triggered.connect(self.down_json_config)

        self.load_json_config(DIRECTORIES_CONFIG, disable_auto_load=False, adjust_size=False)

    def add_drop_area(self, label_dir=None, adjust_size=False):
        """添加可拖拽区域
            label_dir: 设置接受拖拽label控件的指向目录
            adjust_size: 是否在添加可拖拽区域时, 同时调整MainWindow的高度
        """
        # 判断窗口大小
        is_out_desktop = within_range_desktop(self.height()+DROP_AREA_HEIGHT, DROP_AREA_HEIGHT)
        if is_out_desktop >= 0:
            back_info = QMessageBox.information(self, "窗口过大提醒", "继续增加拖拽区域将超出桌面范围, 是否继续.", 
                                                buttons=QMessageBox.Yes | QMessageBox.No)
            if back_info == QMessageBox.No:
                return None
        # 拖拽区域, 使用label
        new_drop_label = LabelAcceptDrop(LABEL_PLACEHOLDER, parent=self)
        new_drop_label.setFixedSize(DROP_AREA_LABEL_WIDTH, DROP_AREA_HEIGHT)
        if label_dir:
            new_drop_label.setText(label_dir)
            new_drop_label.setToolTip(label_dir)
        # 拖拽区域, 定位目录
        dir_drop_button = QPushButton(QIcon(DIRECTORY_ICON), "定位\n目录", parent=self)
        dir_drop_button.setFont(self.button_font)
        dir_drop_button.setStyleSheet(DROP_AREA_DIRECTORY_BUTTON_STYLESHEET)
        dir_drop_button.setFixedSize(DROP_AREA_DIRECTORY_BUTTON_WIDTH, DROP_AREA_HEIGHT)
        dir_drop_button.clicked.connect(lambda : self.find_drop_directory(new_drop_label))
        # 拖拽区域, 移除区域
        remove_area_button = QPushButton(QIcon(REDUCE_ICON), "移除\n区域", parent=self)
        remove_area_button.setFont(self.button_font)
        remove_area_button.setStyleSheet(DROP_AREA_REMOVE_BUTTON_STYLESHEET)
        remove_area_button.setFixedSize(DROP_AREA_REMOVE_BUTTON_WIDTH, DROP_AREA_HEIGHT)
        remove_area_button.clicked.connect(lambda : self.remove_drop_area(new_drop_label))
        # 进行排版
        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(dir_drop_button)
        hbox_layout.addWidget(remove_area_button)   
        self.form_layout.addRow(new_drop_label, hbox_layout)
        # 配置到drop_group中, 创建更方便的访问
        new_drop_label.the_id = self.the_id
        dir_drop_button.the_id = self.the_id
        remove_area_button.the_id = self.the_id
        self.drop_groups[self.the_id] = [new_drop_label, dir_drop_button, remove_area_button]
        self.the_id += 1
        # 调整大小
        if adjust_size:
            # 可自适应高度, 内置widget的建议高 + DROP_AREA_HEIGHT(单个拖拽区域高) + 工具栏高 + 状态栏高
            self.resize(-1, self.inner_widget.sizeHint().height()+DROP_AREA_HEIGHT+self.toolbar.height()+self.statusbar.height())

    def switch_mode(self, sign):
        """切换文件处理的模式, 改变样式与模式信号
            sign: 当前切换功能的模式信号
        """
        cycle_iter = itertools.cycle(SIGNS_LIST)
        signs_cycle = [next(cycle_iter) for _ in range(len(SIGNS_LIST)+1)]
        index = SIGNS_LIST.index(sign)
        new_sign = signs_cycle[index+1]
        if new_sign == CUT_SIGN:
            self.move_copy_switch_action.setData(CUT_SIGN)
            self.move_copy_switch_action.setIcon(QIcon(CUT_ICON))
            self.move_copy_switch_action.setText(self.move_action_text)
        elif new_sign == COPY_SIGN:
            self.move_copy_switch_action.setData(COPY_SIGN)
            self.move_copy_switch_action.setIcon(QIcon(COPY_ICON))
            self.move_copy_switch_action.setText(self.copy_action_text)
        else:
            self.move_copy_switch_action.setData(COMPARE_SIGN)
            self.move_copy_switch_action.setIcon(QIcon(COMPARE_ICON))
            self.move_copy_switch_action.setText(self.compare_action_text)

    def find_drop_directory(self, item_label):
        """定义拖拽区域的定位目录
            item_label: 接受拖拽的Label控件
        """
        directory = QFileDialog.getExistingDirectory(parent=self, caption="指定目录")
        if directory:
            item_label.setText(directory)
            item_label.setToolTip(directory)

    def remove_drop_area(self, item_label):
        """移除可拖拽区域
            item_label: 接受拖拽的Label控件
        """
        self.form_layout.removeRow(item_label)
        del self.drop_groups[item_label.the_id]
        # 可自适应高度, 内置widget的建议高 + DROP_AREA_HEIGHT(单个拖拽区域高)
        self.resize(-1, self.inner_widget.sizeHint().height()+DROP_AREA_HEIGHT)

    def reload_json_config(self):
        """通过文件寻找载入json配置文件"""
        directory, file_type = QFileDialog.getOpenFileName(parent=self, 
            caption="载入Json配置", 
            filter="json config file(*.json)"
        )
        if directory and file_type:
            # 获得配置文件后, 先清除当前的, 然后在重新生成
            for label in [group_list[0] for group_list in self.drop_groups.values()]:
                self.remove_drop_area(label)
            self.load_json_config(directory, disable_auto_load=True, adjust_size=False)
            # 无法使用add_drop_area的动态调整高度, 重新载入窗口没有推荐的大小数据. 拖拽清空后主窗口高 + 拖拽区域总高度 + 工具栏高
            self.resize(-1, self.height()+len(self.drop_groups)*DROP_AREA_HEIGHT+self.toolbar.height())

    def load_json_config(self, directory, disable_auto_load=False, adjust_size=False):
        """进行载入json配置文件, 
            directory: 载入配置json的目录
            disable_auto_load: 是否禁用json配置中的auto_load
            adjust_size: 是否在添加可拖拽区域时, 同时调整MainWindow的高度
        """
        self.linedit_config_path.setText(str(directory))
        self.linedit_config_path.setToolTip(f"当前使用的配置: {directory}")
        if not os.path.isfile(directory):
            return None
        with open(directory, 'r') as file:
            try:
                content_dit = json.load(file)
                if content_dit["auto_load"] or disable_auto_load:  # 判断是否进行预读取, 对于一些情况需要禁用auto_load
                        marked_paths_dit = mark_paths(content_dit["paths_list"])
                        for path in marked_paths_dit["exist"]:
                            self.add_drop_area(path, adjust_size=adjust_size)   # 生成拖拽区域
                        # 对不存在的目录进行消息提示
                        if marked_paths_dit["not_exist"]:
                            info_format = "下面的目录不存在, 将忽略.\n" + \
                                          "\n".join(marked_paths_dit["not_exist"])
                            QMessageBox.information(self, "目录解析提醒", info_format)           
            except Exception as ex:
                QMessageBox.warning(self, "Json 载入错误", f"不能解析所给定的json文件: {directory}\n{ex}")

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


### 配合功能 ###
### REVIEW 用来配合类或者主控功能的函数, 主要是一些检测性或判断的函数

def within_range_desktop(height: int, threshold: int) -> int:
    """判断高度是否在允许阈值内, 超出窗口返回1, 未超出返回-1, 差球不多返回0
        height: 被判断的高度
        threshold: 阈值
    """
    screen_geometry_height = QDesktopWidget().screenGeometry().height()
    if height + threshold > screen_geometry_height:
        return 1
    elif height + threshold < screen_geometry_height:
        return -1
    else:
        return 0


def mark_paths(paths_list: list) -> dict:
    """将有问题的路径归类为一个有序字典
        paths_list: 记录有路径字符串的列表
    """
    marked_paths_dit = dict()
    marked_paths_dit["exist"] = list()   # 存在且格式正确的路径字符串
    marked_paths_dit["not_exist"] = list()   # 字符串代表的路径不存在
    for path in paths_list:
        if os.path.exists(path):
            marked_paths_dit["exist"].append(path)
        else:
            marked_paths_dit["not_exist"].append(path)
    return marked_paths_dit


### 主控功能 ###
### REVIEW 文件操作的主功能