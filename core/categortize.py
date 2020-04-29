import os, shutil, filecmp, json, itertools, asyncio
from collections import OrderedDict

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox

from common.exceptions import *
from common.auxiliary_functions import *
from window.ui_config import *
from window.ui_window import FileHandleDialog, MainWindow
from window import OPEN_FILE_DIRECTORY, MAIN_WIN_TITLE
from core.move_copy import make_handle_dialog, move_copy_prepare, MoveCopyThread


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
            main_win = self.nativeParentWidget()
            if main_win.worker_count >= 1:   # 有任务的时候显示任务, 不显示磁盘信息
                return None
            if str(self.text()) == LABEL_PLACEHOLDER:   # 不为目录而为占位符时
                return None
            if not os.path.exists(self.text()):   # 目录不存在
                return None
            statusbar = main_win.statusBar()
            statusbar.clearMessage()
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

    def dropEvent(self, event):
        """重载拖入释放事件, 主要功能事件"""
        coro_list = list()
        async_event_loop = asyncio.get_event_loop()
        main_win = self.nativeParentWidget()
        if event.mimeData().hasUrls():
            # 遍历输出拖动进来的所有文件路径
            for file_url in event.mimeData().urls():
                src_path = file_url.toLocalFile()
                dst_path = self.text()
                if dst_path == LABEL_PLACEHOLDER:   # 没有设置目录的情况忽略
                    continue
                if src_path == dst_path:   # 拖入目录是自身的情况忽略
                    continue
                if not os.path.exists(dst_path):
                    try:
                        os.makedirs(dst_path)
                    except Exception as ex:
                        QMessageBox.critical(main_win, "拖入目录出错", "未发现定位目录, 尝试创建也出错.")
                        return 1
                try:
                    # 主要功能, 进行文件的处理
                    mode_sign_data = main_win.mode_switch_action.data()
                    if mode_sign_data == MOVE_SIGN:   # 剪切文件
                        if os.access(src_path, os.W_OK) and os.access(dst_path, os.W_OK):   # 检查权限
                            if os.path.split(src_path)[1] in os.listdir(dst_path):   # 如果目录或文件已经在目标目录存在
                                handle_reback = move_copy_prepare(main_win, src_path, dst_path)   # 调用询问窗口
                                if handle_reback.sign == FileHandleDialog.COVER_SIGN:   # 覆盖
                                    worker = MoveCopyThread(src_path, dst_path, MOVE_SIGN, rename=handle_reback.rename, parent=self)
                                    worker.started.connect(self.thread_worker_start)
                                    worker.finish_signal.connect(self.thread_worker_finish)
                                    worker.start()
                                elif handle_reback.sign == FileHandleDialog.IGNORE_SIGN:   # 忽略当前
                                    continue
                                elif handle_reback.sign == FileHandleDialog.CANCEL_SIGN:   # 取消所有
                                    break
                            else:
                                worker = MoveCopyThread(src_path, dst_path, MOVE_SIGN, parent=self)
                                worker.started.connect(self.thread_worker_start)
                                worker.finish_signal.connect(self.thread_worker_finish)
                                worker.start()
                        else:
                            no_permission_info = "没有处理权限."
                            if not os.access(src_path, os.W_OK):
                                no_permission_info += "\n" + str(src_path)
                            if not os.access(dst_path, os.W_OK):
                                no_permission_info += "\n" + str(dst_path)
                            QMessageBox.information(main_win, "权限提醒", no_permission_info)
                            continue
                    elif  mode_sign_data == COPY_SIGN:   # 复制文件
                        if os.access(src_path, os.R_OK) and os.access(dst_path, os.W_OK):   # 检察权限
                            if os.path.split(src_path)[1] in os.listdir(dst_path):   # 如果目录或文件已经在目标目录存在 
                                handle_reback = move_copy_prepare(main_win, src_path, dst_path)   # 调用询问窗口
                                if handle_reback.sign == FileHandleDialog.COVER_SIGN:   # 覆盖
                                    worker = MoveCopyThread(src_path, dst_path, COPY_SIGN, rename=handle_reback.rename, parent=self)
                                    worker.started.connect(self.thread_worker_start)
                                    worker.finish_signal.connect(self.thread_worker_finish)
                                    worker.start()
                                elif handle_reback.sign == FileHandleDialog.IGNORE_SIGN:   # 忽略当前
                                    continue
                                elif handle_reback.sign == FileHandleDialog.CANCEL_SIGN:   # 取消所有
                                    break
                            else:
                                worker = MoveCopyThread(src_path, dst_path, COPY_SIGN, parent=self)
                                worker.started.connect(self.thread_worker_start)
                                worker.finish_signal.connect(self.thread_worker_finish)
                                worker.start()
                        else:
                            no_permission_info = "没有处理权限."
                            if not os.access(src_path, os.R_OK):
                                no_permission_info += "\n" + str(src_path)
                            if not os.access(dst_path, os.W_OK):
                                no_permission_info += "\n" + str(dst_path)
                            QMessageBox.information(main_win, "权限提醒", no_permission_info)
                            continue
                    elif mode_sign_data == COMPARE_SIGN:   # 对比文件
                        new_coro = compare_mode_func(main_win, src_path, dst_path)
                        coro_list.append(new_coro)
                    else:
                        QMessageBox.critical(main_win, "模式错误", f"未检测到合法模式设置. {mode_sign_data}")
                
                    # 如果有协程任务, 启动, 用于文件对比
                    if coro_list:
                        future_result = async_event_loop.run_until_complete(asyncio.gather(*(coro_list)))
                        # 展示对比信息, mode_sign_data == COMPARE_SIGN
                        show_compare_message(main_win, dst_path, future_result)
                except Exception as ex:
                    QMessageBox.critical(main_win, "工作线程创建错误", str(ex))
            event.accept()
        else:
            event.ignore()
        self.setStyleSheet(LABEL_INIT_STYLESHEET)

    def thread_worker_start(self):
        """线程启动"""
        mian_win = self.nativeParentWidget()
        mian_win.worker_count += 1

    def thread_worker_finish(self, info):
        """线程结束, info是由线程返回的namedtuple信息"""
        main_win = self.nativeParentWidget()
        if info["status"] is False:
            QMessageBox.critical(main_win, "任务处理时发生错误", info["error"])
        main_win.worker_count -= 1


class RunMainWin(MainWindow):
    """调用主窗口"""
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.id_count = 0                  # 自增键
        self.drop_groups = OrderedDict()   # 用于拖拽的对象储存
        self.worker_count = 0   # 当前运行的工作数
        self.statusbar_islocked = False   # 是否为statusbar信息上锁而不让修改, False没有锁, 可以改
        # 为活动按钮绑定事件
        self.area_add_action.triggered.connect(lambda : self.add_drop_area(adjust_size=True))
        self.mode_switch_action.triggered.connect(lambda : self.switch_mode(self.mode_switch_action.data()))
        self.config_input_aciton.triggered.connect(self.reload_json_config)
        self.config_output_aciton.triggered.connect(self.down_json_config)
        # 载入设置
        self.load_json_config(DIRECTORIES_CONFIG, disable_auto_load=False, adjust_size=False)
        # 创建计时器
        self.create_timer()
    
    def create_timer(self):
        """创建一个计时器"""
        timer = QTimer(parent=self)
        timer.timeout.connect(self.monitor_worker_count)
        timer.start(1000)

    def monitor_worker_count(self):
        """监视当前worker_count的工作计数, 更新锁定statusbbar"""
        count = self.worker_count
        if count >= 1:
            self.statusbar_islocked = True   # 上锁, 不能更改statusbar信息
            self.statusbar.showMessage("当前运行的任务数: {}".format(count))
        if count < 1 and self.statusbar_islocked:
            self.statusbar_islocked = False
            self.statusbar.clearMessage()

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
        new_file_dir, file_type = QFileDialog.getSaveFileName(parent=self, 
            caption="导出新的配置", 
            directory=OPEN_FILE_DIRECTORY, 
            filter="json config file(*.json)"
        )
        if new_file_dir and file_type:
            with open(new_file_dir, 'w', encoding="utf-8") as file:
                json.dump(output_json, file, ensure_ascii=False)

    def mousePressEvent(self, event):
        """重载单击事件, 没有任务的时候, 可以不显示任务提示, 清空statusbar内容"""
        if self.worker_count < 1:
            self.statusbar.clearMessage()
        event.accept()

    def mouseDoubleClickEvent(self, event):
        """重载双击事件, 和单击保持一样"""
        self.mousePressEvent(event)

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
            

### 对比功能 ###
### REVIEW 拖入的原路径是文件, 比较在目标目录中是否有该文件; 
### 拖入的原路径是目录, 判断目标中是否存在, 然后对比这两个目录

async def compare_mode_func(widget, origin_path, direct_path):
    """单次对比目录或文件是否存在
        widget: 主窗口控件
        origin_path: 原目录或原文件目录
        direct_path: 定位目录
        返回{ 原路径: [[相同目录], [相同文件], 目录是否在目标存在] }
    """
    direct_origin = os.path.join(direct_path, os.path.split(origin_path)[1])   # 在目标目录中的
    if os.path.isfile(origin_path):
        exist_in_direct = False
        if os.path.exists(direct_origin):
            exist_in_direct = True
        return {origin_path: [[], [], exist_in_direct]}
    elif os.path.isdir(origin_path):
        directory_compare = filecmp.dircmp(origin_path, direct_path)
        common_dirs = directory_compare.common_dirs
        common_files = directory_compare.common_files
        exist_in_direct = False
        if os.path.exists(direct_origin):
            exist_in_direct = True
        return {origin_path: [common_dirs, common_files, exist_in_direct]}
    else:
        return {origin_path: [[], [], False]}


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
    info_format = "\n[×]Compare DESTINATION: {direct} DRAGED: {origin}{has_same}{common_dirs}{common_files}\n"
    for info_dit in infos_list:
        origin_path = list(info_dit.keys())[0]
        has_same_info = "\nHave nothing in common."
        has_same = list(info_dit.values())[0][2]
        if has_same:
            has_same_info = "\n -Destination directory already has \"{}\"".format(os.path.split(origin_path)[1])
        common_dirs_info = ""
        common_dirs = list(info_dit.values())[0][0]
        if common_dirs:
            common_dirs_info = "\n -Common directories:\n    " + ", ".join(common_dirs)
        common_files_info = ""
        common_files = list(info_dit.values())[0][1]
        if common_files:
            commonn_files_info = "\n -Common files:\n    " + ", ".join(common_files)
        infos_format += info_format.format(
            direct=direct_path, 
            origin=origin_path, 
            has_same = has_same_info,
            common_dirs=common_dirs_info,
            common_files=common_files_info
        )
    QMessageBox.information(widget, "比较信息", infos_format)
