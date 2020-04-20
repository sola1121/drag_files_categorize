class DropGroupError(Exception):
    """拖入框分组错误"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class UiConfigError(Exception):
    """ui配置错误"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)