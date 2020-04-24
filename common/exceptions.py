class DropGroupError(Exception):
    """拖入框分组错误"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ModeSwitchError(Exception):
    """ui切换模式配置错误"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class FileHandleDialogError(Exception):
    """文件冲突对话框错误"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)