import os, shutil, time, filecmp
from collections import namedtuple

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QLabel

from common.exceptions import *
from common.auxiliary_functions import logging, get_format_file_size
from window.ui_config import *
from window.ui_window import FileHandleDialog


### 移动和复制的相关功能实现 ###
### REVIEW: 进行移动和复制功能操作时, 要对比拖入路径和目标目录, 然后确认后在进行操作

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
        file_handle_dialog.set_origin_name(src_name, os.listdir(dst_path))
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
        返回: namedtuple("HandleFile", ["FileHandleDialog", "sign", "rename"])
    """
    HandleFile = namedtuple("HandleFile", ["FileHandleDialog", "sign", "rename"])
    file_handle_dialog = make_handle_dialog(widget, src_path, dst_path)
    sign_back = file_handle_dialog.exec()
    if sign_back == FileHandleDialog.COVER_SIGN:
        # 执行重命名或覆盖操作
        old_src_name = file_handle_dialog.origin_name
        new_src_name = file_handle_dialog.new_name
        if new_src_name == None or new_src_name == old_src_name:   # 没有新名字, 就覆盖
            if LOGGING:
                logging.info("prepare cover, name \"%s\"" % old_src_name)
            handle_file = HandleFile(FileHandleDialog=file_handle_dialog, sign=sign_back, rename=None)
        else:
            if LOGGING:
                logging.info("prepare rename, old \"%s\" new \"%s\"" % (old_src_name, new_src_name))
            handle_file = HandleFile(FileHandleDialog=file_handle_dialog, sign=sign_back, rename=new_src_name)
    elif sign_back == FileHandleDialog.IGNORE_SIGN:
        # 忽略操作, 跳过这个文件, 接着下一个, 如果有的话
        handle_file = HandleFile(FileHandleDialog=file_handle_dialog, sign=sign_back, rename=None)
    elif sign_back == FileHandleDialog.CANCEL_SIGN:
        # 取消操作, 取消之后的所有文件操作
        handle_file = HandleFile(FileHandleDialog=file_handle_dialog, sign=sign_back, rename=None)
    else:
        raise FileHandleDialogError("%s unknown sign %s" % (file_handle_dialog, sign_back))
    return handle_file


class MoveCopyThread(QThread):
    """工作线程
    __init__(
        src_path: 原路径
        dst_path: 目标路径
        mode: 操作模式
        parent: 父控件(缺省就挺好)
    )
    """
    finish_signal = pyqtSignal(dict)   # 返回dict

    def __init__(self, src_path, dst_path, mode, rename=None, parent=None):
        super().__init__(parent=parent)
        self.src_path = src_path
        self.dst_path = dst_path
        if mode not in [MOVE_SIGN, COPY_SIGN]:
            raise ModeSwitchError("%s mode sign error, given %s" %(self, mode))
        else:
            self.mode = mode
        self.rename = rename

    def run(self):
        info_back = {"status": True, "error": None}   # 默认完成
        if self.mode == MOVE_SIGN:   # 移动
            try:
                if os.path.isfile(self.src_path):   # 对文件
                    if self.rename:
                        shutil.move(self.src_path, os.path.join(self.dst_path, self.rename), copy_function=shutil.copy2)
                    else:
                        new_dst_path = os.path.join(self.dst_path, os.path.split(self.src_path)[1])
                        shutil.move(self.src_path, new_dst_path, copy_function=shutil.copy2)
                        # shutil.copy2(self.src_path, self.new_dst_path)   # NOTE: 备份解决方案
                        # os.remove(self.src_path)
                    if LOGGING:
                        logging.info("move file complete, path \"%s\" -> path \"%s\"" %(self.src_path, self.dst_path ))
                else:   # 对目录
                    if self.rename:
                        shutil.move(self.src_path, os.path.join(self.dst_path, self.rename), copy_function=shutil.copy2)
                    else:
                        move2(self.src_path, self.dst_path)
                        shutil.rmtree(self.src_path)
                    if LOGGING:
                        logging.info("move directory complete, path \"%s\" -> path \"%s\"" %(self.src_path, self.dst_path ))
            except Exception as ex:
                info_back["status"] = False
                info_back["error"] = f"{self.src_path} 移动到 {self.dst_path} 发生错误!\n{ex}"
        else:   # 复制
            try:
                if os.path.isfile(self.src_path):   # 对文件
                    if self.rename:
                        shutil.copy2(self.src_path, os.path.join(self.dst_path, self.rename))
                    else:
                        shutil.copy2(self.src_path, self.dst_path)
                    if LOGGING:
                        logging.info("copy file complete, path \"%s\" -> \"%s\"" %(self.src_path, self.dst_path))
                else:   # 对目录
                    if self.rename:
                        shutil.copytree(self.src_path, os.path.join(self.dst_path, self.rename), copy_function=shutil.copy2)
                    else:
                        copytree2(self.src_path, self.dst_path)
                    if LOGGING:
                        logging.info("copy directory complete, path \"%s\" -> \"%s\"" %(self.src_path, self.dst_path))
            except Exception as ex:
                info_back["status"] = False
                info_back["error"] = f"{self.src_path} 复制到 {self.dst_path} 发生错误!\n{ex}"
        self.finish_signal.emit(info_back)


def move2(src_path, dst_path):
    """专用于移动目录的方法, 将src_path移动到dst_path中 
        src_path : 原目录
        dst_path :目标目录
    """
    src_name = os.path.split(src_path)[1]
    new_dst_path = os.path.join(dst_path, src_name)
    
    os.makedirs(new_dst_path, exist_ok=True)
    
    for name in os.listdir(src_path):
        src_path_name = os.path.join(src_path, name)   # 在原目录中的文件或子目录的完整路径
        if os.path.isdir(src_path_name):   # 如果是目录
            move2(src_path_name, new_dst_path)
        elif os.path.isfile(src_path_name):   # 如果是文件
            shutil.move(src_path_name, os.path.join(new_dst_path, name))

    shutil.copystat(src_path, new_dst_path)   # 不必要, 因为已经将文件信息复制了


def copytree2(src_path, dst_path):
    """专用于复制目录的方法, 将src_path复制到dst_path中
        src_path : 原目录
        dst_path : 目标目录
    """
    src_name = os.path.split(src_path)[1]
    new_dst_path = os.path.join(dst_path, src_name)
    
    os.makedirs(new_dst_path, exist_ok=True)
    
    for name in os.listdir(src_path):
        src_path_name = os.path.join(src_path, name)   # 在原目录中的文件或子目录的完整路径
        if os.path.isdir(src_path_name):   # 如果是目录
            copytree2(src_path_name, new_dst_path)
        elif os.path.isfile(src_path_name):   # 如果是文件
            shutil.copy2(src_path_name, os.path.join(new_dst_path, name))

    shutil.copystat(src_path, new_dst_path)   # 不必要, 因为已经将文件信息复制了
