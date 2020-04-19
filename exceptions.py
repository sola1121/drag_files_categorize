class DropGroupError(Exception):
    """提供拖入框分组错误"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)