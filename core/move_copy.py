import os, shutil, time, filecmp
from collections import namedtuple

from PyQt5.QtCore import Qt, QThread
from PyQt5.QtWidgets import QWidget, QLabel, QMessageBox

from common.exceptions import *
from common.auxiliary_functions import get_format_file_size
from window.ui_config import *
from window.ui_window import FileHandleDialog


def make_handle_dialog(widget, src_path, dst_path) -> FileHandleDialog:
    """创建文件冲突对话框FileHandleDialog, 并返回.
        widget : 父窗口控件
        src_path : 原文件路径
        dst_path : 目标文件路径
    """
    src_name = os.path.split(src_path)[1]   # 被移动或复制的目录或文件名
    src2dst_path = os.path.join(dst_path, src_name)   # 移动或复制新的路径
    if os.path.exists(src2dst_path):   #　判断是否已经在目标路径存在
        # 判断移动的是啥
        if os.path.isfile(src_path):
            type_describle = "文件"
        elif os.path.isdir(src_path): 
            type_describle = "文件夹"
        else:
            type_describle = "未知"
        src_stat_info = os.stat(src_path)
        src2dst_stat_info = os.stat(src2dst_path)
        head_info_format = "<h3>合并{type_describle}\"{src_name}\"吗?</h3><br>\
                            <h4>在\"{dst_name_path}\"存在同名内容时, 将会被<span style='color: red;'>覆盖</span>!</h4>".format(
                                type_describle = type_describle,
                                src_name = src_name,
                                dst_name_path = os.path.split(dst_path)[1]
        )
        dst_info_format = "<b>原{type_describle}</b><br>项目: {number}, 大小: {size}<br>上次修改: {datetime}".format(
                            type_describle = type_describle,
                            number = src2dst_stat_info.st_nlink,
                            size = get_format_file_size(src2dst_stat_info.st_size),
                            datetime = time.strftime("%Y.%m.%d %H:%M:%S", time.localtime(os.path.getmtime(src2dst_path)))
        )
        src_info_format = "<b>替换为</b><br>项目: {number}, 大小: {size}<br>上次修改: {datetime}".format(
                            number = src_stat_info.st_nlink,
                            size = get_format_file_size(src_stat_info.st_size),
                            datetime = time.strftime("%Y.%m.%d %H:%M:%S", time.localtime(os.path.getmtime(src_path)))
        )
        # 初始化文件冲突对话框, 并进行必要的设置
        file_handle_dialog = FileHandleDialog(parent=widget)
        file_handle_dialog.set_origin_name(src_name)
        label_header = QLabel(head_info_format, parent=file_handle_dialog)
        label_header.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label_dst_info = QLabel(dst_info_format, parent=file_handle_dialog)
        label_src_info = QLabel(src_info_format, parent=file_handle_dialog)
        # 进行布局
        file_handle_dialog.grid_layout.addWidget(label_header, 0, 1)
        file_handle_dialog.grid_layout.addWidget(label_dst_info, 1, 1)
        file_handle_dialog.grid_layout.addWidget(label_src_info, 2, 1)
        return file_handle_dialog


def move_copy_prepare(widget, src_path, dst_path) -> namedtuple:
    """预先准备, 单次询问对重名文件的处理方式
        src_path : 原目录或文件路径
        dst_path: 目标目录
    """
    HandleFile = namedtuple("HandleFile", ["FileHandleDialog", "sign", "rename"])
    file_handle_dialog = make_handle_dialog(widget, src_path, dst_path)
    sign_back = file_handle_dialog.exec()
    if sign_back == FileHandleDialog.COVER_SIGN:
        #TODO: 执行重命名或覆盖操作
        old_src_name = file_handle_dialog.origin_name
        new_src_name = file_handle_dialog.new_name
        if new_src_name == None or new_src_name == old_src_name:   # 没有新名字, 就覆盖
            print("要覆盖, 新旧同名%s" % old_src_name)
            handle_file = HandleFile(FileHandleDialog=file_handle_dialog, sign=sign_back, rename=None)
        else:
            print("旧的名字:", old_src_name, "新的名字:", new_src_name)
            handle_file = HandleFile(FileHandleDialog=file_handle_dialog, sign=sign_back, rename=new_src_name)
    elif sign_back == FileHandleDialog.IGNORE_SIGN:
        #TODO: 忽略操作, 跳过这个文件, 接着下一个, 如果有的话
        print("忽略当前文件")
        handle_file = HandleFile(FileHandleDialog=file_handle_dialog, sign=sign_back, rename=None)
    elif sign_back == FileHandleDialog.CANCEL_SIGN:
        #TODO: 取消操作, 取消之后的所有文件操作
        handle_file = HandleFile(FileHandleDialog=file_handle_dialog, sign=sign_back, rename=None)
        print("取消所有操作")
    else:
        raise FileHandleDialogError("%s unknown sign %s" % (file_handle_dialog, sign_back))
    return handle_file


class MoveCopyThread(QThread):
    """工作线程
    __init__(
        widget: 父窗口
        src_path: 原路径
        dst_path: 目标路径
        mode: 操作模式
        callback: 回调函数
    )
    """
    def __init__(self, widget, src_path, dst_path, mode, callback=None, parent=None):
        super().__init__(parent=parent)
        self.widget = widget
        self.src_path = src_path
        self.dst_path = dst_path
        if mode not in [MOVE_SIGN, COPY_SIGN]:
            raise ModeSwitchError("%s mode sign error, given %s" %(self, mode))
        else:
            self.mode = mode
        if callable:
            self.finished.connect(callback)

    def run(self):
        null_widget = QWidget()
        if self.mode == MOVE_SIGN:   # 移动
            try:
                QMessageBox.information(null_widget, "文件移动提醒", "{} -> {}".format(self.src_path, self.dst_path))
                # shutil.move(self.src_path, self.dst_path, copy_function=shutil.copy2)
            except Exception as ex:
                QMessageBox.critical(null_widget, "文件移动时错误", "测试测试测试内容.")
        else:   # 复制
            try:
                if os.path.isfile(self.src_path):
                    QMessageBox.information(null_widget, "文件复制提醒", "{} -> {}".format(self.src_path, self.dst_path))
                    # shutil.copy2(self.src_path, self.dst_path)
                else: 
                    QMessageBox.information(null_widget, "目录复制提醒", "{} -> {}".format(self.src_path, self.dst_path))
                    # shutil.copytree(self.src_path, self.dst_path, copy_function=shutil.copy2, dirs_exist_ok=False)
            except Exception as ex:
                QMessageBox.critical(null_widget, "文件复制时错误", "测试测试测试内容.")
        self.sleep(3)


# TODO: may use recursive method to every directories and 
# let user to decide if cover a common file.
class MoveCopyRecursiveThread(QThread):
    """基于递归遍历目录, 每有一个重复会提示"""
    def __init__(self, widget, src_path, dst_path, mode, callback=None, parent=None):
        super().__init__(parent=parent)
        self.widget = widget
        self.src_path = src_path
        self.dst_path = dst_path
        if mode not in [MOVE_SIGN, COPY_SIGN]:
            raise ModeSwitchError("%s mode sign error, given %s" %(self, mode))
        else:
            self.mode = mode
        if callable:
            self.finished.connect(callback)

    def run(self):
        pass


# TODO: recursive function
def recursive_dir(widget, src_path, dst_path, mode):
    src_name = os.path.split(src_path)[1]
    src2dst_path = os.path.join(dst_path, os.path.split(src_path)[1])
    if src_name in os.listdir(dst_path):
        dir_cmp = filecmp.dircmp(src_path, src2dst_path)
        for directory in dir_cmp.common_dirs:
            print("同样的目录:", directory)
            if mode == MOVE_SIGN:
                pass
            else:
                pass
            recursive_dir(widget, os.path.join(src_path, directory), os.path.join(dst_path, directory))

        for file in dir_cmp.common_files:
            if mode == MOVE_SIGN:
                pass
            else:
                pass
            print("同样的文件:", file)
    else:
        print("新的目录或文件", src_path)

