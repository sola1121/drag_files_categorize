import os, shutil, filecmp, pathlib

from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog

file_path = "/home/sola1121/桌面/zipfile.tar.bz2"
dir_path = "/home/sola1121/桌面/file_dir"

path1 = "/home/sola1121/桌面/c1"
path2 = "/home/sola1121/桌面/c2"

print("c1", os.listdir(path1))
print("c2", os.listdir(path2))

match, mismatch, errors = filecmp.cmpfiles(path1, path2, list())

directory_compare = filecmp.dircmp(path1, path2)
directory_compare.report_full_closure()


app = QApplication([None])
widget = QWidget()

# directory = QFileDialog.getExistingDirectory(parent=widget, caption="获取目录")

# 将会到达的新目录
print(os.path.join(path1, os.path.split(file_path)[1]))
print(os.path.join(path1, os.path.split(dir_path)[1]))

new_file = os.path.join(path1, os.path.split(file_path)[1])
new_path = os.path.join(path1, os.path.split(dir_path)[1])

print(new_file, "是否存在", os.path.exists(new_file))
print(new_file, "是否是目录", os.path.isdir(new_file))
print(new_file, "是否是文件", os.path.isfile(new_file))

print(new_path, "是否存在", os.path.exists(new_path))
print(new_path, "是否是目录", os.path.isdir(new_path))
print(new_path, "是否是文件", os.path.isfile(new_path))

# copytree(src: Union[str], dst: Union[str], symlinks: bool, ignore: Union[None, Unknown], copy_function: ..., ignore_dangling_symlinks: bool) -> Any
# 使用的复制功能: shutil.copytree()

# move(src: Union[str], dst: Union[str], copy_function: Union[Unknown]) -> Any
# 使用的移动功能: shutil.move()

# file_path_1 = pathlib.Path(file_path)
# dir_path_2 = pathlib.Path(dir_path)

# if os.path.exists():

# if filecmp.

# shutil.move(dir_path, directory, copy_function=shutil.copy2)

# shutil.move 移动目录到已有其存在的目录
# raise Error("Destination path '%s' already exists" % real_dst)
# shutil.Error: Destination path '/home/sola1121/桌面/c1/file_dir' already exists
# 就算是存在有区别也是
# raise Error("Destination path '%s' already exists" % real_dst)
# shutil.Error: Destination path '/home/sola1121/桌面/c1/file_dir' already exists