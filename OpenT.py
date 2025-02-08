#OpenT.py
import mimetypes
import os
import sys

import chardet
from PyQt5.QtCore import QStandardPaths, Qt
from PyQt5.QtGui import QIcon, QFont, QMouseEvent
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QFileDialog, QAction, QTabWidget, QWidget, \
    QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QCheckBox, QLabel, QMessageBox

from editor_functions import save_file, replace_text, find_text, close_tab, replace_all_text, new_file_e, show_hint, show_hint_e, add_new_tab_e


class CustomTextEdit(QTextEdit):
    def __init__(self):
        super().__init__()
        self.is_saved = True
        self.is_new_file = False
        self.file_path = None
        self.font_size = 11
        self.setFont(QFont("微软雅黑", self.font_size))

        # 监听文本变化
        self.textChanged.connect(self.on_text_changed)

    def on_text_changed(self):
        """文本内容发生变化时调用"""
        if self.is_saved:
            self.is_saved = False
            self.window().update_tab_title(self)

    def dragEnterEvent(self, event):
        """重写拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """重写drop事件"""
        files = event.mimeData().urls()
        for file in files:
            file_path = file.toLocalFile()
            if os.path.exists(file_path):
                self.window().add_new_tab(file_path)
        event.accept()

    def load_file_content(self, file_path):
        """加载文件内容"""
        try:
            with open(file_path, 'rb') as file:
                raw_data = file.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']

            with open(file_path, 'r', encoding=encoding, errors='ignore') as file:
                text = file.read()

            # 统一换行符为\n，并保留所有空格
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            self.setPlainText(text)
            self.file_path = file_path
            self.is_saved = True
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载文件时出错: {e}")

    def insertFromMimeData(self, source):
        """处理粘贴操作，只保留纯文本并统一换行符"""
        if source.hasText():
            text = source.text()
            # 统一换行符并保留所有空格
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            self.insertPlainText(text)

class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('OpenT')
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon('D:/AppTests/tetee/icon.ico'))

        # 记录已经打开的文件路径，防止重复打开
        self.opened_files = set()

        # 创建标签栏
        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)

        # 创建查找栏
        self.find_bar = QWidget(self)
        self.find_layout = QHBoxLayout(self.find_bar)
        self.find_input = QLineEdit(self)
        self.find_button = QPushButton('查找', self)
        self.match_case_find_checkbox = QCheckBox("匹配大小写", self)

        # 设置固定宽度的标签栏
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                max-width: 120px;
                min-width: 120px;
                text-overflow: ellipsis;
                overflow: hidden;
            }
            QTabBar::tab:selected {
                font-weight: bold;
            }
            QTabBar::close-button {
                image: url(D:/AppTests/tetee/close_icon.png);
                background: transparent;
                padding: 3px;
                margin: 1px;
            }
            QTabBar::close-button:hover {
                background-color: rgba(128, 128, 128, 50);  /* 半透明灰色 */
                border-radius: 2px;
            }
            QTabBar::close-button:pressed {
                background-color: rgba(96, 96, 96, 50);    /* 半透明深灰色 */
            }
        """)

        # 查找栏边距设置为0，去掉间距
        self.find_layout.addWidget(QLabel('查找:', self))
        self.find_layout.addWidget(self.find_input)
        self.find_layout.addWidget(self.find_button)
        self.find_layout.addWidget(self.match_case_find_checkbox)

        # 设置查找按钮的初始状态为禁用
        self.find_button.setEnabled(False)

        # 创建替换栏
        self.replace_bar = QWidget(self)
        self.replace_layout = QHBoxLayout(self.replace_bar)
        self.find_replace_input = QLineEdit(self)
        self.replace_input = QLineEdit(self)
        self.replace_button = QPushButton('替换', self)
        self.replace_all_button = QPushButton('全部替换', self)
        self.match_case_replace_checkbox = QCheckBox("匹配大小写", self)

        # 设置替换按钮的初始状态为禁用
        self.replace_button.setEnabled(False)
        self.replace_all_button.setEnabled(False)

        # 替换栏边距设置为0，去掉间距
        self.replace_layout.addWidget(QLabel('查找内容:', self))
        self.replace_layout.addWidget(self.find_replace_input)
        self.replace_layout.addWidget(QLabel('替换为:', self))
        self.replace_layout.addWidget(self.replace_input)
        self.replace_layout.addWidget(self.replace_button)
        self.replace_layout.addWidget(self.replace_all_button)
        self.replace_layout.addWidget(self.match_case_replace_checkbox)

        # 设置主布局的边距为0
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.addWidget(self.find_bar)
        layout.addWidget(self.replace_bar)
        layout.addWidget(self.tabs)

        # 设置中央控件的边距为0
        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        central_widget.setContentsMargins(0, 0, 0, 0)

        self.setCentralWidget(central_widget)

        self.create_actions()
        self.create_menubar()

        # 初始时查找和替换栏不可见
        self.find_bar.setVisible(False)
        self.replace_bar.setVisible(False)

        # 连接按钮
        self.find_button.clicked.connect(self.find_text)
        self.replace_button.clicked.connect(self.replace_text)
        self.replace_all_button.clicked.connect(self.replace_all_text)

        # 支持拖放文件
        self.setAcceptDrops(True)

    def create_actions(self):
        """创建操作"""
        self.new_file_action = QAction('新建(&N)', self)
        self.new_file_action.triggered.connect(self.new_file)
        self.new_file_action.setShortcut('Ctrl+N')

        self.open_action = QAction('打开(&O)', self)
        self.open_action.triggered.connect(self.open_file)
        self.open_action.setShortcut('Ctrl+O')

        self.save_action = QAction('保存(&S)', self)
        self.save_action.triggered.connect(self.save_file_ot)
        self.save_action.setShortcut('Ctrl+S')

        self.save_as_action = QAction('另存为(&A)', self)
        self.save_as_action.triggered.connect(self.save_as_file_ot)
        self.save_as_action.setShortcut('Ctrl+Shift+S')

        self.close_tab_action = QAction('关闭标签页(&C)', self)
        self.close_tab_action.triggered.connect(self.close_current_tab)
        self.close_tab_action.setShortcut('Ctrl+W')

        self.toggle_find_action = QAction('显示/隐藏查找栏(&F)', self)
        self.toggle_find_action.triggered.connect(self.toggle_find_bar)
        self.toggle_find_action.setShortcut('Ctrl+F')

        self.toggle_replace_action = QAction('显示/隐藏替换栏(&R)', self)
        self.toggle_replace_action.triggered.connect(self.toggle_replace_bar)
        self.toggle_replace_action.setShortcut('Ctrl+H')

        self.increase_font_size_action = QAction('增大字体', self)
        self.increase_font_size_action.triggered.connect(self.increase_font_size)

        self.decrease_font_size_action = QAction('减小字体', self)
        self.decrease_font_size_action.triggered.connect(self.decrease_font_size)

        self.reset_font_size_action = QAction('恢复默认字体', self)
        self.reset_font_size_action.triggered.connect(self.reset_font_size)

    def create_menubar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        file_menu = menubar.addMenu('文件(&F)')
        file_menu.addAction(self.new_file_action)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addAction(self.close_tab_action)

        edit_menu = menubar.addMenu('编辑(&E)')
        edit_menu.addAction(self.toggle_find_action)
        edit_menu.addAction(self.toggle_replace_action)
        edit_menu.addAction(self.increase_font_size_action)
        edit_menu.addAction(self.decrease_font_size_action)
        edit_menu.addAction(self.reset_font_size_action)
        edit_menu.addAction(self.toggle_replace_action)
        edit_menu.addAction(self.toggle_find_action)

    def save_file_ot(self):
        """保存文件"""
        current_text_edit = self.get_current_text_edit()
        if current_text_edit:
            if current_text_edit.is_new_file or current_text_edit.file_path is None:
                self.save_as_file_ot()
                return True
            else:
                try:
                    save_file(current_text_edit, current_text_edit.file_path)
                    current_text_edit.is_saved = True
                    self.update_tab_title(current_text_edit)
                    return True
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"保存失败: {e}")
                    return False
        return False

    def save_as_file_ot(self):
        '''另存为文件'''
        current_text_edit = self.get_current_text_edit()
        if current_text_edit:
            file_path, _ = QFileDialog.getSaveFileName(self, "另存为", "", "文本文件 (*.txt);;所有文件 (*)")
            if file_path:
                save_file(current_text_edit, file_path)
                current_text_edit.file_path = file_path  # 更新文件路径
                current_text_edit.is_saved = True
                self.update_tab_title(current_text_edit)

    def update_tab_title(self, text_edit):
        """更新标签标题，确保星号和省略号正确显示"""
        index = self.tabs.indexOf(text_edit.parent())
        if index != -1:
            file_name = os.path.basename(text_edit.file_path)
            is_unsaved = not text_edit.is_saved  # 如果未保存，显示星号

            # 设置最大可显示字符数
            max_length = 7
            suffix = "*" if is_unsaved else ""  # 星号表示未保存

            # 如果文件名过长，截断并添加省略号
            if len(file_name) + len(suffix) > max_length:
                truncated_name = f"{file_name[:max_length - 3 - len(suffix)]}..."  # 保留省略号空间
            else:
                truncated_name = file_name

            tab_text = f"{truncated_name}{suffix}"  # 最终标签文字
            self.tabs.setTabText(index, tab_text)

            # 更新工具提示为完整文件路径
            self.tabs.setTabToolTip(index, text_edit.file_path)

    def increase_font_size(self):
        """增大字体，最大为24"""
        current_text_edit = self.get_current_text_edit()
        if current_text_edit:
            font = current_text_edit.font()
            current_size = font.pointSize()
            new_size = min(current_size + 1, 24)  # 增加字体，最大为24
            font.setPointSize(new_size)
            current_text_edit.setFont(font)  # 更新字体
            self.update_font_size_buttons()

    def decrease_font_size(self):
        """减小字体，最小为8"""
        current_text_edit = self.get_current_text_edit()
        if current_text_edit:
            font = current_text_edit.font()
            current_size = font.pointSize()
            new_size = max(current_size - 1, 8)  # 减小字体，最小为8
            font.setPointSize(new_size)
            current_text_edit.setFont(font)  # 更新字体
            self.update_font_size_buttons()

    def reset_font_size(self):
        """恢复默认字体大小"""
        current_text_edit = self.get_current_text_edit()
        if current_text_edit:
            font = current_text_edit.font()
            font.setPointSize(11)  # 恢复默认字体大小
            current_text_edit.setFont(font)
            self.update_font_size_buttons()

    def get_current_text_edit(self):
        """获取当前活动标签页的 CustomTextEdit"""
        current_widget = self.tabs.currentWidget()
        if current_widget:
            return current_widget.findChild(CustomTextEdit)
        return None

    def update_font_size_buttons(self):
        """更新字体大小按钮的状态"""
        current_text_edit = self.get_current_text_edit()
        if current_text_edit:
            font = current_text_edit.font()
            current_size = font.pointSize()

            # 增大字体时，如果当前字体已最大，则禁用增大按钮
            self.increase_font_size_action.setEnabled(current_size < 24)  # 最大字体为24
            self.decrease_font_size_action.setEnabled(current_size > 8)  # 最小字体为8
        else:
            self.increase_font_size_action.setEnabled(False)
            self.decrease_font_size_action.setEnabled(False)

    def open_file(self):
        """打开文件"""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, '打开文件', '', '文本文件 (*.txt);;所有文件 (*)',
                                                   options=options)
        if file_name:
            self.add_new_tab(file_name)

    def new_file(self):
        """新建一个空白文件"""
        text_edit = CustomTextEdit()
        text_edit.is_new_file = True  # 标记为新文件
        desktop_path = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
        text_edit.file_path = desktop_path
        try:
            new_file_e(self, text_edit)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"新建文件时发生错误：{str(e)}")  # 提示用户错误信息
        self.enable_find_replace(True)

    def add_new_tab(self, file_path):
        """添加新标签，如果文件已打开则不再重复打开，并验证文件格式"""
        file_name = os.path.basename(file_path)

        # 使用 MIME 类型检测文件类型
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and not mime_type.startswith('text'):
            # 如果文件不是文本文件，弹出提示
            QMessageBox.critical(self, "错误", "请选择一个有效的TXT文件")
            return

        if file_path in self.opened_files:
            # 如果文件已打开，则跳转到该标签
            for index in range(self.tabs.count()):
                tab_widget = self.tabs.widget(index)
                text_edit = tab_widget.findChild(CustomTextEdit)
                if text_edit and text_edit.file_path == file_path:
                    self.tabs.setCurrentIndex(index)
                    return
        else:
            self.opened_files.add(file_path)

            # 创建新的文本编辑器
            text_edit = CustomTextEdit()
            text_edit.file_path = file_path

            # 创建新的标签页
            add_new_tab_e(self, text_edit, file_path, file_name)

        # 启用查找和替换按钮
        self.enable_find_replace(True)
        self.update_font_size_buttons()

    def close_current_tab(self):
        """关闭当前标签页并清理文件路径"""
        index = self.tabs.currentIndex()  # 获取当前活动标签页的索引
        current_widget = self.tabs.widget(index)  # 获取当前活动标签页的小部件
        if current_widget:
            # 获取标签页的 CustomTextEdit 控件
            text_edit = current_widget.findChild(CustomTextEdit)
            if text_edit and hasattr(text_edit, 'file_path') and not text_edit.is_saved:
                # 调用 show_hint 方法处理保存提示
                result = show_hint("文件未保存，是否保存？", "提示", "D:/AppTests/tetee/icon.ico")
                if result == QMessageBox.Save:
                    # 用户点击了保存，调用保存逻辑
                    if self.save_file_ot():
                        # 保存成功后再关闭标签页
                        close_tab(current_widget, self.tabs)
                        if text_edit and hasattr(text_edit, 'file_path'):
                            self.opened_files.discard(text_edit.file_path)
                elif result == QMessageBox.Discard:
                    # 用户点击了不保存，直接关闭标签页
                    close_tab(current_widget, self.tabs)
                    if text_edit and hasattr(text_edit, 'file_path'):
                        self.opened_files.discard(text_edit.file_path)
            else:
                # 如果文件已经保存或没有路径，直接关闭标签页
                close_tab(current_widget, self.tabs)
                if text_edit and hasattr(text_edit, 'file_path'):
                    self.opened_files.discard(text_edit.file_path)

        # 如果没有打开文件，禁用查找和替换按钮
        if not self.opened_files:
            self.enable_find_replace(False)

    def enable_find_replace(self, enable):
        """启用或禁用查找和替换功能"""
        self.find_button.setEnabled(enable)
        self.replace_button.setEnabled(enable)
        self.replace_all_button.setEnabled(enable)

    def find_text(self):
        """查找文本"""
        query = self.find_input.text()
        match_case = self.match_case_find_checkbox.isChecked()
        current_text_edit = self.get_current_text_edit()
        find_text(query, current_text_edit, match_case)

    def replace_all_text(self):
        """替换所有文本"""
        find_query = self.find_replace_input.text()  # 查找内容
        replace_query = self.replace_input.text()  # 替换为内容
        match_case = self.match_case_replace_checkbox.isChecked()
        current_text_edit = self.get_current_text_edit()
        replace_all_text(find_query, replace_query, current_text_edit, match_case=match_case)

    def replace_text(self):
        """替换文本"""
        find_query = self.find_replace_input.text()  # 查找内容
        replace_query = self.replace_input.text()  # 替换为内容
        match_case = self.match_case_replace_checkbox.isChecked()
        current_text_edit = self.get_current_text_edit()
        replace_text(find_query, replace_query, current_text_edit, match_case=match_case)

    def toggle_find_bar(self):
        """切换查找栏的显示与隐藏"""
        if self.replace_bar.isVisible():  # 如果替换栏已经显示
            self.replace_bar.setVisible(False)  # 隐藏替换栏
        current_visible = self.find_bar.isVisible()
        self.find_bar.setVisible(not current_visible)
        if not current_visible:
            self.find_input.setFocus()  # 显示时自动聚焦到查找输入框

    def toggle_replace_bar(self):
        """切换替换栏的显示与隐藏"""
        if self.find_bar.isVisible():  # 如果查找栏已经显示
            self.find_bar.setVisible(False)  # 隐藏查找栏
        current_visible = self.replace_bar.isVisible()
        self.replace_bar.setVisible(not current_visible)
        if not current_visible:
            self.find_replace_input.setFocus()  # 显示时自动聚焦到替换输入框

    def closeEvent(self, event):
        """关闭应用时检查未保存的文件"""
        unsaved_files = [tab for tab in range(self.tabs.count())
                         if self.tabs.widget(tab).findChild(CustomTextEdit).is_saved is False]
        if unsaved_files:
            # 存在未保存的文件
            result = show_hint_e("有未保存的文件，是否保存？", "提示", "D:/AppTests/tetee/icon.ico")
            if result == QMessageBox.Save:
                # 用户选择保存
                if not self.save_file_ot():
                    # 如果保存失败，阻止关闭
                    event.ignore()
                    return
            elif result == QMessageBox.Discard:
                # 用户选择不保存
                event.accept()  # 直接关闭应用
            else:
                # 用户取消关闭
                event.ignore()  # 阻止关闭
        else:
            event.accept()  # 没有未保存文件，直接关闭

    def dragEnterEvent(self, event):
        """处理拖拽事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()  # 接受拖拽的文件
        else:
            event.ignore()  # 如果不是文件则忽略事件

    def dropEvent(self, event):
        """处理文件放置事件"""
        files = event.mimeData().urls()
        for file in files:
            file_path = file.toLocalFile()
            if os.path.exists(file_path):
                self.add_new_tab(file_path)  # 添加新标签页并加载文件
        event.accept()  # 确保事件被接受

    def wheelEvent(self, event):
        """处理鼠标滚轮事件，通过Ctrl+滚轮控制字体大小"""
        # 检查Ctrl键是否被按下
        if event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y()  # 获取鼠标滚轮的滚动值
            if delta > 0:
                self.increase_font_size()  # 增大字体
            elif delta < 0:
                self.decrease_font_size()  # 减小字体

        # 调用父类处理其他滚轮事件
        event.accept()

    def mousePressEvent(self, event: QMouseEvent):
        """处理鼠标按下事件"""
        if event.button() == Qt.MiddleButton and event.modifiers() == Qt.ControlModifier:
            # 检测到 Ctrl + 鼠标中键点击时恢复默认字体大小
            self.reset_font_size()

        # 如果没有按下 Ctrl+鼠标中键，继续处理其他鼠标事件
        super().mousePressEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TextEditor()
    window.show()
    sys.exit(app.exec_())