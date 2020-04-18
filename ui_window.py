from PyQt5 import QtCore, QtGui, QtWidgets


class MainWindow(QtWidgets.QMainWindow):
    """主窗口样式"""
    def __init__(self, parent=None, flags=QtCore.Qt.WindowFlags()):
        super().__init__(parent=parent, flags=flags)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint |   # 置顶显示按钮
                            QtCore.Qt.WindowMinimizeButtonHint |   # 使能最小化按钮
                            QtCore.Qt.WindowCloseButtonHint   # 关闭按钮
            )
        self.setFixedWidth(520)
        self.setMinimumHeight(60)
        self.setWindowIcon(QtGui.QIcon("icons/android.ico"))
        self.setWindowTitle("Drop files category")

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
            QtGui.QIcon("icons/plus.png"),
            "添加拖拽区域",
            parent=self
        )
        self.config_input_aciton = QtWidgets.QAction(
            QtGui.QIcon("icons/setting-input.png"),
            "导入配置好的分类目录",
            parent=self
        )
        self.config_output_aciton = QtWidgets.QAction(
            QtGui.QIcon("icons/setting-output.png"),
            "导出配置好的分类目录",
            parent=self
        )
        self.linedit_config_path = QtWidgets.QLineEdit()
        self.linedit_config_path.setDisabled(True)

    def create_toolbar(self):
        self.toolbar = self.addToolBar("add area")
        self.toolbar.addAction(self.area_add_action)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.linedit_config_path)
        self.toolbar.addAction(self.config_input_aciton)
        self.toolbar.addAction(self.config_output_aciton)

    def create_statusbar(self):
        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Hello")