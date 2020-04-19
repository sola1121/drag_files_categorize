from PyQt5 import QtCore, QtGui, QtWidgets

from ui_config import *


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

        self.set_center_layout()
        self.create_action()
        self.create_toolbar()
        self.create_statusbar()

    def set_center_layout(self):
        widget = QtWidgets.QWidget()
        self.form_layout = QtWidgets.QFormLayout()
        widget.setLayout(self.form_layout)
        self.form_layout.setAlignment(QtCore.Qt.AlignLeft)
        self.setCentralWidget(widget)

    def create_action(self):
        self.area_add_action = QtWidgets.QAction(
            QtGui.QIcon(PLUS_ICON),
            "添加拖拽区域(Ctrl+Shift+A)",
            parent=self
        )
        self.area_add_action.setShortcut("Ctrl+Shift+A")
        self.config_input_aciton = QtWidgets.QAction(
            QtGui.QIcon(SETTING_INPUT),
            "导入配置好的分类目录",
            parent=self
        )
        self.config_output_aciton = QtWidgets.QAction(
            QtGui.QIcon(SETTING_OUTPUT),
            "导出配置好的分类目录",
            parent=self
        )
        self.linedit_config_path = QtWidgets.QLineEdit()
        self.linedit_config_path.setToolTip("载入的目录配置文件")
        self.linedit_config_path.setDisabled(True)

    def create_toolbar(self):
        self.toolbar = self.addToolBar("add area")
        self.toolbar.addAction(self.area_add_action)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.linedit_config_path)
        self.toolbar.addAction(self.config_input_aciton)
        self.toolbar.addAction(self.config_output_aciton)

    def create_statusbar(self):
        label = QtWidgets.QLabel()
        label.setOpenExternalLinks(True)
        label.setText("<a style='font-size: 10px;' href='https://github.com/sola1121/drag_files_categorize'>Github</a>")
        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)

        self.statusbar.addPermanentWidget(label)
        self.statusbar.showMessage("-----")