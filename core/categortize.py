import os, shutil, filecmp, json, itertools, asyncio, time
from collections import OrderedDict

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox, QDesktopWidget

from common.exceptions import *
from common.auxiliary_functions import *
from window.ui_config import *
from window.ui_window import FileHandleDialog, MainWindow
from window import OPEN_FILE_DIRECTORY
from core.move_copy import make_handle_dialog, MoveCopyThread


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
            disk_info = shutil.disk_usage(path=self.text())   # 单位B
            disk_info_format = "根 {root} , 总容量: {total} 使用: {used} 空闲: {free} 使用率: {used_rate}%".format(
                   root = (os.path.splitdrive(self.text())[0]) if (os.path.splitdrive(self.text())[0]) else "/",
                   total = get_format_file_size(disk_info.total), 
                   used = get_format_file_size(disk_info.used), 
                   free = get_format_file_size(disk_info.free),  
                   used_rate = round(disk_info.used/disk_info.total*100, 2))
            statusbar.showMessage(disk_info_format)
        except Exception as ex:
            QMessageBox.critical(self.nativeParentWidget(), "获取磁盘使用失败", f"{ex}")

    def mouseDoubleClickEvent(self, event):
        """重载双击事件, 显示磁盘容量"""
        self.mousePressEvent(event)
    
    def dragEnterEvent(self, event):
        """重载进入事件"""
        if event.mimeData().hasUrls():
            event.accept()
            self.setStyleSheet(LABEL_ENTER_STYLESHEET)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """重载离开事件"""
        event.accept()
        self.setStyleSheet(LABEL_LEAVE_STYLESHEET)

    # TODO: 主要功能开发, 使用shutil, filecmp, os开始对文件进行操作
    def dropEvent(self, event):
        """重载拖入释放事件, 主要功能事件"""
        coro_list = list()
        async_event_loop = asyncio.get_event_loop()
        main_win = self.nativeParentWidget()
        if event.mimeData().hasUrls():
            # 遍历输出拖动进来的所有文件路径
            for url in event.mimeData().urls():
                src_path = url.toLocalFile()
                print("\n拖入目录:", src_path)
                if self.text() == LABEL_PLACEHOLDER:   # 没有设置目录的情况忽略
                    continue
                if src_path == self.text():   # 拖入目录是自身的情况忽略
                    continue
                if not os.path.exists(self.text()):
                    try:
                        os.makedirs(self.text())
                    except Exception as ex:
                        QMessageBox.critical(main_win, "拖入目录出错", "未发现定位目录, 尝试创建也出错.")
                        return 1
                # 主要功能, 进行文件的处理
                mode_sign_data = main_win.mode_switch_action.data()
                # TODO: 
                if mode_sign_data == MOVE_SIGN:   # 剪切文件
                    reback = move_copy_prepare(main_win, src_path, self.text())
                    print(src_path, "-返回值%s-M->"%reback, self.text())
                elif  mode_sign_data == COPY_SIGN:   # 复制文件
                    print(src_path, "-C->", self.text())
                elif mode_sign_data == COMPARE_SIGN:   # 对比文件
                    new_coro = compare_mode_func(main_win, src_path, self.text())
                    coro_list.append(new_coro)
                else:
                    QMessageBox.critical(main_win, "模式错误", f"未检测到合法模式设置. {mode_sign_data}")
            if coro_list:
                future_result = async_event_loop.run_until_complete(asyncio.gather(*(coro_list)))
                print("Future对象:", future_result)
                if mode_sign_data == COMPARE_SIGN:   # 展示对比信息
                    show_compare_message(main_win, self.text(), future_result)
        else:
            event.ignore()
        self.setStyleSheet(LABEL_INIT_STYLESHEET)


class RunMainWin(MainWindow):
    """调用主窗口"""
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.id_count = 0                  # 自增键
        self.drop_groups = OrderedDict()   # 用于拖拽的对象储存
        self.worker_count = 0   # 当前运行的工作数

        self.area_add_action.triggered.connect(lambda : self.add_drop_area(adjust_size=True))
        self.mode_switch_action.triggered.connect(lambda : self.switch_mode(self.mode_switch_action.data()))
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
            back_warn = QMessageBox.warning(self, 
                "窗口过大提醒", "继续增加拖拽区域将超出桌面范围, 是否继续.", 
                buttons=QMessageBox.No | QMessageBox.Ok,
                defaultButton=QMessageBox.No
            )
            if back_warn == QMessageBox.No:
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
        new_drop_label.the_id = self.id_count
        dir_drop_button.the_id = self.id_count
        remove_area_button.the_id = self.id_count
        self.drop_groups[self.id_count] = [new_drop_label, dir_drop_button, remove_area_button]
        self.id_count += 1
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
        if new_sign == MOVE_SIGN:
            self.mode_switch_action.setData(MOVE_SIGN)
            self.mode_switch_action.setIcon(QIcon(MOVE_ICON))
            self.mode_switch_action.setText(self.move_action_text)
            self.setWindowTitle(MAIN_WIN_TITLE + "   [mode: move]")
        elif new_sign == COPY_SIGN:
            self.mode_switch_action.setData(COPY_SIGN)
            self.mode_switch_action.setIcon(QIcon(COPY_ICON))
            self.mode_switch_action.setText(self.copy_action_text)
            self.setWindowTitle(MAIN_WIN_TITLE + "   [mode: copy]")
        elif new_sign == COMPARE_SIGN:
            self.mode_switch_action.setData(COMPARE_SIGN)
            self.mode_switch_action.setIcon(QIcon(COMPARE_ICON))
            self.mode_switch_action.setText(self.compare_action_text)
            self.setWindowTitle(MAIN_WIN_TITLE + "   [mode: compare]")
        else:
            QMessageBox.critical(self, "模式配置错误", "模式切换获得非法模式配置.")
            return 1

    def find_drop_directory(self, item_label):
        """定义拖拽区域的定位目录
            item_label: 接受拖拽的Label控件
        """
        if item_label.text() != LABEL_PLACEHOLDER:
            root_path = item_label.text()
        else:
            root_path = OPEN_FILE_DIRECTORY
        directory = QFileDialog.getExistingDirectory(parent=self, caption="指定目录", directory=root_path)
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
            directory=OPEN_FILE_DIRECTORY,
            filter="json config file(*.json)"
        )
        if directory and file_type:
            # 获得配置文件后, 先清除当前的, 然后在重新生成
            for label in [group_list[0] for group_list in self.drop_groups.values()]:
                self.remove_drop_area(label)
            self.load_json_config(directory, disable_auto_load=True, adjust_size=False)
            # 无法使用add_drop_area的动态调整高度, 重新载入窗口没有推荐的大小数据. 拖拽清空后主窗口高 + 拖拽区域总高度 + 状态栏高
            self.resize(-1, self.height()+len(self.drop_groups)*DROP_AREA_HEIGHT+self.statusbar.height())

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
                QMessageBox.critical(self, "Json 载入错误", f"不能解析所给定的json文件: {directory}\n{ex}")

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

    def closeEvent(self, event):
        """重载关闭事件"""
        if self.worker_count < 1:
            event.accept()
        else:
            back_warn = QMessageBox.warning(self, 
                "任务执行中警告", 
                f"当前有 {self.worker_count} 个任务正在运行, 关闭可能导致数据丢失, 是否继续?",
                buttons=QMessageBox.No | QMessageBox.Ok,
                defaultButton=QMessageBox.No
            )
            if back_warn == QMessageBox.Ok:
                event.accept()
            else:
                event.ignore()
            

### 主控功能 ###
### REVIEW 文件操作的主功能

IGNORE_SIGN = 100
ACCEPT_SIGN = 200

def move_copy_prepare(widget, src_path, dst_path) -> dict:
    """预先准备, 单次询问对重名文件的处理方式
        src_path : 原目录或文件路径
        dst_path: 目标目录
        返回一个字典 {sign: 信号类型, rename: 如果是重命名信号, 有这个 }
    """
    if os.path.samefile(src_path, dst_path):
        return {}
    file_handle_dialog = make_handle_dialog(widget, src_path, dst_path)
    sign_back = file_handle_dialog.exec()
    if sign_back == FileHandleDialog.COVER_SIGN:
        #TODO: 执行重命名或覆盖操作
        pass
    elif sign_back == FileHandleDialog.IGNORE_SIGN:
        #TODO: 忽略操作, 跳过这个文件, 接着下一个, 如果有的话
        pass
    elif sign_back == FileHandleDialog.CANCEL_SIGN:
        #TODO: 取消操作, 取消之后的所有文件操作
        pass
    else:
        raise FileHandleDialogError("%s unknown sign %s" % (file_handle_dialog, sign_back))
    print("按键返回值:", sign_back, "测试name_path是否还有:", file_handle_dialog.name_path)


async def compare_mode_func(widget, origin_path, direct_path):
    """单次对比目录或文件是否存在
        widget: 主窗口控件
        origin_path: 原目录或原文件目录
        direct_path: 定位目录
        返回{ 原路径: [[相同目录], [相同文件]] }
    """
    direct_origin = os.path.join(direct_path, os.path.split(origin_path)[1])   # 在目标目录中的
    if os.path.isfile(origin_path):
        return {origin_path: [[], [os.path.split(origin_path)[1]] if os.path.exists(direct_origin) else []]}
    elif os.path.isdir(origin_path):
        if os.path.exists(direct_origin):   # 在目标目录中是否存在
            directory_compare = filecmp.dircmp(origin_path, direct_origin)
            common_dirs = directory_compare.common_dirs
            common_files = directory_compare.common_files
            return {origin_path: [common_dirs, common_files]}
        else:
            return {origin_path: [[], []]}


def show_compare_message(widget, direct_path, infos_list):
    """显示目录对比信息
        widget: 主窗口控件
        direct_path: 定位目录
        infos_list: 如
            [
                {'/home/c1': [ ['deep2'], ['file1.png'] ]}, 
                {'/home/backup': [ ['deep2'], ['file1.png'] ]},
                {'/home/file1.png': [ [], [''] ]}
            ]
    """
    infos_format = str()
    info_format = "\n[×]Compare {origin} && {direct}\n -Common dirs:\n    {directories}\n -Common files:\n    {files}\n"
    for info_dit in infos_list:
        origin_path = list(info_dit.keys())[0]
        infos_format += info_format.format(
            origin=origin_path, 
            direct=os.path.join(direct_path, os.path.split(origin_path)[1]), 
            directories=", ".join(list(info_dit.values())[0][0]), 
            files=", ".join(list(info_dit.values())[0][1])
        )
    QMessageBox.information(widget, "比较信息", infos_format)