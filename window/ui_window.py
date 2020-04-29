import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from common.exceptions import *
from window.ui_config import *


class DownLabel(QtWidgets.QLabel):
    """具有点击事件的标签"""
    def __init__(self, parent=None, flags=QtCore.Qt.WindowFlags()):
        super().__init__(parent=parent, flags=flags)
        self.up_clicked_text = "▶ 为目标选择一个新名称"
        self.down_clicked_text = "▼ 为目标选择一个新名称"
        self.is_clicked = False

        self.setText(self.up_clicked_text)
    
    def mousePressEvent(self, event):
        """重载单击事件, 配合FileHandleDialog使用"""
        handle_dialog = self.nativeParentWidget()
        parent_layout = handle_dialog.vbox_layout
        if self.is_clicked:   # 未点击时, 隐藏lineedit
            self.is_clicked = False
            self.setText(self.up_clicked_text)
            handle_dialog.linedit_rename.setVisible(False)
            handle_dialog.resize(handle_dialog.width(), parent_layout.sizeHint().height())   #NOTE: 工作的不是很好
            # parent_layout.removeWidget(handle_dialog.linedit_rename)
        else:   # 点击时, 显示lineedit
            self.is_clicked = True
            self.setText(self.down_clicked_text)
            handle_dialog.linedit_rename.setVisible(True)
            # index = parent_layout.indexOf(self) + 1
            # parent_layout.insertWidget(index, handle_dialog.linedit_rename)
            

class FileHandleDialog(QtWidgets.QDialog):
    """文件冲突处理框
    内置接口
        origin_name : 原始的目录或文件名
        linedit_rename : 重命名单行编辑框
        grid_layout : 信息的主显示
        button_cover : 覆盖或重命名按钮
        button_ignore : 跳过按钮
        button_cancel : 取消按钮
    """
    COVER_SIGN = 1
    IGNORE_SIGN = 2
    CANCEL_SIGN = 3

    def __init__(self, parent=None, flags=QtCore.Qt.WindowFlags()):
        super().__init__(parent=parent, flags=flags)
        self.setWindowTitle("文件冲突")
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setModal(True)

        self.name_black_list = list()   # 保存名字黑名单, 包括同名与系统禁止的
        self.origin_name = None   # 原始的文件名
        self.new_name = None   # 新的文件名

        self.create_linedit()
        self.create_label()
        self.create_buttons()
        self.set_layout()


    def create_buttons(self):
        """创建按钮"""
        self.button_cover = QtWidgets.QPushButton("覆盖", parent=self)
        self.button_cover.setToolTip("Cover")
        self.button_ignore = QtWidgets.QPushButton("跳过(&S)", parent=self)
        self.button_ignore.setToolTip("Skip")
        self.button_cancel = QtWidgets.QPushButton("取消", parent=self)
        self.button_cancel.setToolTip("Cancel")
        self.button_cancel.setDefault(True)
        self.button_cover.clicked.connect(self.to_cover)
        self.button_ignore.clicked.connect(self.to_ignore)
        self.button_cancel.clicked.connect(self.to_cancle)

    def create_label(self):
        """操作重命名标签"""
        self.label_down = DownLabel(parent=self)

    def create_linedit(self):
        if sys.platform == "win32":
            name_regx = QtCore.QRegExp(r"^[^\.][^\/\?\*:\|\\<>]+$")    # 开头不能 . 里面不能有 / ?  * : | \  <  >
            self.name_black_list.extend(["con","aux","nul","prn","com0","com1","com2","com3","com4",
                                         "com5","com6","com7", "com8","com9","lpt0","lpt1","lpt2",
                                         "lpt3", "lpt4","lpt5","lpt6","lpt7","lpt8","lpt9"])
        else:
            name_regx = QtCore.QRegExp(r"^[^\.\/][^\/]+$")  # 开头不能 . /  里面不能有 /
            self.name_black_list.extend([])
        self.linedit_rename = QtWidgets.QLineEdit()
        # 正则验证, 字母和数字
        validator_regex = QtGui.QRegExpValidator()
        validator_regex.setRegExp(name_regx)
        self.linedit_rename.setValidator(validator_regex)
        self.linedit_rename.setMaxLength(255)
        self.linedit_rename.textChanged.connect(self.linedit_change)

    def set_layout(self):
        """进行窗口布局"""
        hbox_layout = QtWidgets.QHBoxLayout()
        hbox_layout.addSpacing(QtGui.QPixmap(DIALOG_QUESTION_ICON).width())
        hbox_layout.addWidget(self.button_cancel)
        hbox_layout.addWidget(self.button_ignore)
        hbox_layout.addWidget(self.button_cover)

        label_question_pixmap = QtWidgets.QLabel(parent=self)
        label_question_pixmap.setPixmap(QtGui.QPixmap(DIALOG_QUESTION_ICON))

        self.grid_layout = QtWidgets.QGridLayout()
        self.grid_layout.addWidget(label_question_pixmap, 0, 0)
        self.grid_layout.setSpacing(10)

        self.vbox_layout = QtWidgets.QVBoxLayout()
        self.vbox_layout.addLayout(self.grid_layout)
        self.vbox_layout.addWidget(self.label_down)
        self.vbox_layout.addWidget(self.linedit_rename)
        self.linedit_rename.setVisible(False)
        self.vbox_layout.addLayout(hbox_layout)

        self.setLayout(self.vbox_layout)

    def set_origin_name(self, value, black_list):
        """设置重命名单行编辑框文本
            value: 原文件名
            blcak_list: 已存在与目标目录中的名字
        """
        self.origin_name = value
        self.name_black_list.extend(black_list)
        self.name_black_list.remove(value)
        self.linedit_rename.setText(value)

    def linedit_change(self, value):
        """重命名编辑框文本改变事件"""
        if len(value) <= 0:
            self.button_cover.setEnabled(False)
        else:
            self.button_cover.setEnabled(True)
        if value == self.origin_name:
            self.button_cover.setText("覆盖")
            self.button_cover.setToolTip("Cover")
        else:
            self.button_cover.setText("重命名")
            self.button_cover.setToolTip("Rename")
    
    def to_cover(self):
        """覆盖按钮槽函数"""
        if self.linedit_rename.text() in self.name_black_list:
            QtWidgets.QMessageBox.information(self, 
                "重命名错误", 
                "当前名称 %s 已存在, 请修改." % self.linedit_rename.text()
            )
            self.linedit_rename.setText(self.origin_name)
            self.linedit_change(self.origin_name)
        else:
            self.new_name = self.linedit_rename.text()
            self.done(FileHandleDialog.COVER_SIGN)

    def to_ignore(self):
        """跳过按钮槽函数"""
        self.done(FileHandleDialog.IGNORE_SIGN)

    def to_cancle(self):
        """取消按钮槽函数"""
        # self.setResult(self.CANCEL_SIGN)
        self.done(FileHandleDialog.CANCEL_SIGN)

    def closeEvent(self, event):
        """重载关闭事件"""
        self.setResult(FileHandleDialog.CANCEL_SIGN)
        event.accept()


class MyInfoLabel(QtWidgets.QLabel):
    """相关信息标签"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOpenExternalLinks(True)
        self.setText("<span style='font-size: 10px;'><a href='https://github.com/sola1121/drag_files_categorize'>Github</a> LGPL v3.0<span>")
        self.setToolTip("Developer: sola1121, Main Page: https://github.com/sola1121/drag_files_categorize")


class MainWindow(QtWidgets.QMainWindow):
    """主窗口样式"""
    def __init__(self, parent=None, flags=QtCore.Qt.WindowFlags()):
        super().__init__(parent=parent, flags=flags)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint |   # 置顶显示按钮
                            QtCore.Qt.WindowMinimizeButtonHint |   # 使能最小化按钮
                            QtCore.Qt.WindowCloseButtonHint   # 关闭按钮
            )
        self.setFixedWidth(MAINWIN_WIDTH)
        self.setMinimumHeight(MAINWIN_HEIGHT)
        self.setWindowIcon(QtGui.QIcon(MAIN_ICON))
        self.setWindowTitle(MAIN_WIN_TITLE)

        self.button_font = QtGui.QFont()         # 用于button的QFont
        self.button_font.setPointSize(BUTTON_FONT_SIZE)   # 设置按钮的字体大小

        self.move_action_text = "当前模式: 移动MOVE (Ctrl+Shift+M)"
        self.copy_action_text = "当前模式: 复制COPY (Ctrl+Shift+M)"
        self.compare_action_text = "当前模式: 比较COMPARE (Ctrl+Shift+M)"

        self.set_center_layout()
        self.create_action()
        self.create_toolbar()
        self.create_statusbar()

    def set_center_layout(self):
        """添加布局管理器"""
        self.inner_widget = QtWidgets.QWidget()
        self.form_layout = QtWidgets.QFormLayout()
        self.inner_widget.setLayout(self.form_layout)
        self.form_layout.setAlignment(QtCore.Qt.AlignLeft)
        self.setCentralWidget(self.inner_widget)

    def create_action(self):
        """创建动作"""
        # 添加拖拽区域的动作
        self.area_add_action = QtWidgets.QAction(
            QtGui.QIcon(PLUS_ICON),
            "添加拖拽区域(Ctrl+Shift+A)",
            parent=self
        )
        self.area_add_action.setShortcut("Ctrl+Shift+A")
        # 切换复制或剪切模式的动作
        self.mode_switch_action = QtWidgets.QAction(parent=self)
        if DEFAULT_SIGN == MOVE_SIGN:
            icon_file = MOVE_ICON 
            move_copy_text = self.move_action_text
        elif DEFAULT_SIGN == COPY_SIGN:
            icon_file = COPY_ICON
            move_copy_text = self.copy_action_text
        elif DEFAULT_SIGN == COMPARE_SIGN:
            icon_file = COMPARE_ICON
            move_copy_text = self.compare_action_text
        else:
            raise ModeSwitchError("%s mode switch action config error, ui config DEFAULT_SIGN is %s"\
                                 % (self.mode_switch_action, DEFAULT_SIGN))
        self.mode_switch_action.setData(DEFAULT_SIGN)
        self.mode_switch_action.setIcon(QtGui.QIcon(icon_file))
        self.mode_switch_action.setText(move_copy_text)
        self.mode_switch_action.setShortcut("Ctrl+Shift+M")
        # 导入json配置的动作
        self.config_input_aciton = QtWidgets.QAction(
            QtGui.QIcon(SETTING_INPUT),
            "导入配置好的分类目录",
            parent=self
        )
        # 导出json配置的动作
        self.config_output_aciton = QtWidgets.QAction(
            QtGui.QIcon(SETTING_OUTPUT),
            "导出配置好的分类目录",
            parent=self
        )
        self.linedit_config_path = QtWidgets.QLineEdit()
        self.linedit_config_path.setToolTip("载入的目录配置文件")
        self.linedit_config_path.setDisabled(True)

    def create_toolbar(self):
        """创建工具栏, 并添加动作"""
        self.toolbar = self.addToolBar("add area")
        self.toolbar.addAction(self.area_add_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.mode_switch_action)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.linedit_config_path)
        self.toolbar.addAction(self.config_input_aciton)
        self.toolbar.addAction(self.config_output_aciton)

    def create_statusbar(self):
        """创建状态栏"""
        label = MyInfoLabel()
        self.statusbar = QtWidgets.QStatusBar(self)
        self.statusbar.setStyleSheet(STATUSBAR_STYLESHEET)
        self.setStatusBar(self.statusbar)
        self.statusbar.addPermanentWidget(label, 0)
