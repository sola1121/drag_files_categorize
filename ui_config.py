# incon files
MAIN_WIN_TITLE = "Drop Files Categortize"
MAIN_ICON = "icons/android.ico"
SETTING_INPUT = "icons/setting-input.png"
SETTING_OUTPUT = "icons/setting-output.png"
PLUS_ICON = "icons/plus.png"
COMPARE_ICON = "icons/compare.png"
COPY_ICON = "icons/copy.png"
CUT_ICON = "icons/cut.png"
REDUCE_ICON = "icons/reduce.png"
DIRECTORY_ICON = "icons/directory.png"
DIALOG_QUESTION_ICON = "icons/dialog-question.png"

# ui_window config
MAINWIN_WIDTH = 520
MAINWIN_HEIGHT = 60

# action
COMPARE_SIGN = 3
COPY_SIGN = 2
CUT_SIGN = 1
DEFAULT_SIGN = CUT_SIGN   # default move file mode
SIGNS_LIST = [CUT_SIGN, COPY_SIGN, COMPARE_SIGN]   # mode switch order

# status bar
STATUSBAR_STYLESHEET = "font-size: 10px;"

# drop_files_categortize config
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
LABEL_ENTER_STYLESHEET = "border: 2px solid rgb(117, 117, 117); background-color: rgb(175, 175, 175); font-size: 10px;"
LABEL_LEAVE_STYLESHEET = LABEL_INIT_STYLESHEET

# default load directory json config
DIRECTORIES_CONFIG = "directories.json"