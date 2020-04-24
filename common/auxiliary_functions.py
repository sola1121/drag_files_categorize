import os

from PyQt5.QtWidgets import QDesktopWidget


### 配合功能 ###
### REVIEW 用来配合类或者主控功能的函数, 主要是一些检测性或判断的函数

def within_range_desktop(height: int, threshold: int) -> int:
    """判断高度是否在允许阈值内, 超出窗口返回1, 未超出返回-1, 差球不多返回0
        height: 被判断的高度
        threshold: 阈值
    """
    screen_geometry_height = QDesktopWidget().screenGeometry().height()
    if height + threshold > screen_geometry_height:
        return 1
    elif height + threshold < screen_geometry_height:
        return -1
    else:
        return 0


def mark_paths(paths_list: list) -> dict:
    """将有问题的路径归类为一个有序字典
        paths_list: 记录有路径字符串的列表
    """
    marked_paths_dit = dict()
    marked_paths_dit["exist"] = list()   # 存在且格式正确的路径字符串
    marked_paths_dit["not_exist"] = list()   # 字符串代表的路径不存在
    for path in paths_list:
        if os.path.exists(path):
            marked_paths_dit["exist"].append(path)
        else:
            marked_paths_dit["not_exist"].append(path)
    return marked_paths_dit


def get_format_file_size(path_or_size) -> str:
    """返回文件大小, 含单位
        path_or_size : 文件路径, 或大小值
    """
    # 判断是给的文件路径还是大小值
    if isinstance(path_or_size, str):
        path = path_or_size
        if not os.path.exists(path):
            return "error"
        size = float(os.path.getsize(path))   # 单位B(字节)
    elif isinstance(path_or_size, (int, float)):
        size = float(path_or_size)
    # 开始计算, 以1000为间隔单位, 精度2
    K = 1000; pec = 2
    units = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    for i, unit in enumerate(units):
        meet_num = size / K**i
        if meet_num < K:
            return str(round(meet_num, pec)) + unit
    else:
        return str(round(size/pow(K, i-1), pec)) + unit
