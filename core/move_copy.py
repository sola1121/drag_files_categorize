import os, shutil, time

from PyQt5.QtCore import Qt, QThread
from PyQt5.QtWidgets import QLabel

from common.exceptions import *
from common.auxiliary_functions import get_format_file_size
from window.ui_config import *
from window.ui_window import FileHandleDialog


def make_handle_dialog(widget, src_path, dst_path) -> FileHandleDialog:
    name_path = os.path.split(src_path)[1]   # 被移动或复制的目录或文件名
    src2dst_path = os.path.join(dst_path, name_path)   # 移动或复制新的路径
    if os.path.exists(src2dst_path):   #　判断是否已经在目标路径存在
        # 判断移动的是啥
        if os.path.isfile(src_path):
            type_describle = "文件"
        elif os.path.isdir(src_path): 
            type_describle = "文件夹"
        else:
            type_describle = "未知"
    head_info_format = "<h3>合并{type_describle}\"{name_path}\"吗?</h3><br>\
                        <h4>在\"{dst_name_path}\"存在同名内容时, 将会被<span stle='color: red;'>覆盖</span>!</h4>".format(
                            type_describle = type_describle,
                            name_path = name_path,
                            dst_name_path = os.path.split(dst_path)[1]
    )
    dst_info_format = "<b>原{type_describle}</b><br>大小: {size}<br>上次修改: {datetime}".format(
                        type_describle = type_describle,
                        size = get_format_file_size(src2dst_path),
                        datetime = time.strftime("%Y.%m.%d %H:%M:%S", time.localtime(os.path.getmtime(src2dst_path)))
    )
    src_info_format = "<b>替换为</b><br>大小: {size}<br>上次修改: {datetime}".format(
                        size = get_format_file_size(src_path),
                        datetime = time.strftime("%Y.%m.%d %H:%M:%S", time.localtime(os.path.getmtime(src_path)))
    )
    # 初始化文件冲突对话框, 并进行必要的设置
    file_handle_dialog = FileHandleDialog(parent=widget)
    file_handle_dialog.set_name_path(name_path)
    label_header = QLabel(head_info_format, parent=file_handle_dialog)
    label_header.setTextInteractionFlags(Qt.TextSelectableByMouse)
    label_dst_info = QLabel(dst_info_format, parent=file_handle_dialog)
    label_src_info = QLabel(src_info_format, parent=file_handle_dialog)
    # 进行布局
    file_handle_dialog.grid_layout.addWidget(label_header, 0, 1)
    file_handle_dialog.grid_layout.addWidget(label_dst_info, 1, 1)
    file_handle_dialog.grid_layout.addWidget(label_src_info, 2, 1)
    return file_handle_dialog


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
    def __init__(self, widget, src_path, dst_path, mode, callback=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        if self.mode == MOVE_SIGN:
            pass
        else:
            pass
