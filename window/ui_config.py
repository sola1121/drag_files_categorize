# incon files
MAIN_ICON = "window/icons/main.ico"
SETTING_INPUT = "window/icons/setting-input.png"
SETTING_OUTPUT = "window/icons/setting-output.png"
PLUS_ICON = "window/icons/plus.png"
COMPARE_ICON = "window/icons/compare.png"
COPY_ICON = "window/icons/copy.png"
MOVE_ICON = "window/icons/cut.png"
REDUCE_ICON = "window/icons/reduce.png"
DIRECTORY_ICON = "window/icons/directory.png"
DIALOG_QUESTION_ICON = "window/icons/dialog-question.png"

# ui_window config
MAINWIN_WIDTH = 520
MAINWIN_HEIGHT = 60

# action, may don't do any thing about these is the best
COMPARE_SIGN = 3
COPY_SIGN = 2
MOVE_SIGN = 1
DEFAULT_SIGN = MOVE_SIGN   # default move file mode
SIGNS_LIST = [MOVE_SIGN, COPY_SIGN, COMPARE_SIGN]   # mode switch order

# status bar
STATUSBAR_STYLESHEET = "font-size: 10px;"

# drop file areas config
BUTTON_FONT_SIZE = 9
DROP_AREA_HEIGHT = 60
DROP_AREA_LABEL_WIDTH = MAINWIN_WIDTH * 0.65
DROP_AREA_DIRECTORY_BUTTON_WIDTH = MAINWIN_WIDTH * 0.15
DROP_AREA_REMOVE_BUTTON_WIDTH = MAINWIN_WIDTH * 0.15
DROP_AREA_DIRECTORY_BUTTON_STYLESHEET = ""
DROP_AREA_REMOVE_BUTTON_STYLESHEET = ""

LABEL_PLACEHOLDER = "-----"
LABEL_FONT_SIZE = 9   # can be covered by LABEL_INIT_STYLESHEET with font-size css style
LABEL_INIT_STYLESHEET = "font-size: 12px; border: 1px solid black;"
LABEL_ENTER_STYLESHEET = "font-size: 10px; border: 2px solid rgb(115, 115, 115); background-color: rgb(185, 185, 185);"
LABEL_LEAVE_STYLESHEET = LABEL_INIT_STYLESHEET

# default load directory json config
DIRECTORIES_CONFIG = "directories.json"

# whether logging
LOGGING = True

# default config file
CONFIG_FILE = "config.json"


# 允许外部通过json文件定义的一些
import os, json


if CONFIG_FILE and os.path.exists(os.path.join(os.path.dirname(__file__), CONFIG_FILE)):
    try:
        with open(os.path.join(os.path.dirname(__file__), CONFIG_FILE), 'r') as file:
            configs_dit = json.load(file)
            DIRECTORIES_CONFIG = configs_dit["defaultDirectoriesConfig"]
            if configs_dit["historyLog"] in (True, False):
                LOGGING = configs_dit["historyLog"]
    except:
        pass
