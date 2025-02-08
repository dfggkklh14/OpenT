import io
import mimetypes
import os
import sys
from typing import Optional

import chardet
from PyQt5.QtCore import QStandardPaths, Qt
from PyQt5.QtGui import QIcon, QFont, QMouseEvent
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QFileDialog, QAction, QTabWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QCheckBox, QLabel, QMessageBox
)

from editor_functions import (
    save_file, replace_text, find_text, close_tab, replace_all_text,
    new_file_e, add_new_tab_e, show_hint, show_hint_e, update_tab_title, get_resource_path, get_resource_url
)

# 常量定义
DEFAULT_FONT_SIZE = 11
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 24


class CustomTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_saved = True
        self.is_new_file = False
        # 新建文件的 file_path 为 None，从而显示“未命名”
        self.file_path: Optional[str] = None
        self.font_size = DEFAULT_FONT_SIZE
        self.setFont(QFont("微软雅黑", self.font_size))
        # 监听文本变化
        self.textChanged.connect(self.on_text_changed)

    def on_text_changed(self) -> None:
        """文本变化时标记为未保存并更新标签标题"""
        if self.is_saved:
            self.is_saved = False
            update_tab_title(self.window(), self)

    def dragEnterEvent(self, event) -> None:
        """拖拽进入时如果包含 URL 则接受"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        """处理拖放事件：添加新标签加载文件"""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.exists(file_path):
                self.window().add_new_tab(file_path)
        event.accept()

    def load_file_content(self, file_path: str) -> None:
        """加载指定文件内容到编辑器"""
        try:
            with open(file_path, 'rb') as file:
                raw_data = file.read()
                result = chardet.detect(raw_data)
                encoding = result.get('encoding', 'utf-8')

            with open(file_path, 'r', encoding=encoding, errors='ignore') as file:
                text = file.read()

            text = text.replace('\r\n', '\n').replace('\r', '\n')
            self.setPlainText(text)
            self.file_path = file_path
            self.is_saved = True
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载文件时出错: {e}")

    def insertFromMimeData(self, source) -> None:
        """粘贴时只插入纯文本并统一换行符"""
        if source.hasText():
            text = source.text().replace('\r\n', '\n').replace('\r', '\n')
            self.insertPlainText(text)

class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('OpenT')
        self.setWindowIcon(QIcon(get_resource_path("icon.ico")))
        self.setGeometry(100, 100, 800, 600)

        self.setStyleSheet("""
                    * {
                        font-family: 'Microsoft YaHei', sans-serif;
                    }
                """)

        # 记录已打开文件路径（防止重复打开）
        self.opened_files = set()

        # 创建标签页控件，并设置现代化简洁样式
        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.tabs.setStyleSheet("""
            /* 标签页样式 */
            QTabBar::tab {
                background: #f0f0f0;
                border: 1px solid #dcdcdc;
                border-bottom: none;
                padding: 2px 5px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 100px;
                max-width: 100px;
                text-overflow: ellipsis;
                overflow: hidden;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                font-weight: bold;
                border: 1px solid #b0b0b0;
                border-bottom: 1px solid #ffffff;
            }
            QTabBar::close-button {
                image: url(%s);
                background: transparent;
                width: 16px;
                height: 16px;
                margin-left: 4px;
            }
            QTabBar::close-button:hover {
                background-color: #e0e0e0;
                border-radius: 2px;
            }
            QTabBar::close-button:pressed {
                background-color: #c0c0c0;
            }
        """ % get_resource_url("close_icon.png"))

        # 构建查找栏
        self.find_bar = QWidget(self)
        self.find_layout = QHBoxLayout(self.find_bar)
        self.find_layout.setContentsMargins(10, 0, 10, 0)
        self.find_label = QLabel('查找:', self)
        self.find_input = QLineEdit(self)
        self.find_button = QPushButton('查找', self)
        self.match_case_find_checkbox = QCheckBox("匹配大小写", self)
        self.find_layout.addWidget(self.find_label)
        self.find_layout.addWidget(self.find_input)
        self.find_layout.addWidget(self.find_button)
        self.find_layout.addWidget(self.match_case_find_checkbox)
        self.find_button.setEnabled(False)

        # 构建替换栏
        self.replace_bar = QWidget(self)
        self.replace_layout = QHBoxLayout(self.replace_bar)
        self.replace_layout.setContentsMargins(10, 0, 10, 0)
        self.find_replace_label = QLabel('查找内容:', self)
        self.find_replace_input = QLineEdit(self)
        self.replace_label = QLabel('替换为:', self)
        self.replace_input = QLineEdit(self)
        self.replace_button = QPushButton('替换', self)
        self.replace_all_button = QPushButton('全部替换', self)
        self.match_case_replace_checkbox = QCheckBox("匹配大小写", self)
        self.replace_layout.addWidget(self.find_replace_label)
        self.replace_layout.addWidget(self.find_replace_input)
        self.replace_layout.addWidget(self.replace_label)
        self.replace_layout.addWidget(self.replace_input)
        self.replace_layout.addWidget(self.replace_button)
        self.replace_layout.addWidget(self.replace_all_button)
        self.replace_layout.addWidget(self.match_case_replace_checkbox)
        self.replace_button.setEnabled(False)
        self.replace_all_button.setEnabled(False)

        # 主布局（查找栏、替换栏、标签页）
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.find_bar)
        main_layout.addWidget(self.replace_bar)
        main_layout.addWidget(self.tabs)

        central_widget = QWidget(self)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # 创建菜单动作和菜单栏
        self.create_actions()
        self.create_menubar()

        # 初始时隐藏查找和替换栏
        self.find_bar.setVisible(False)
        self.replace_bar.setVisible(False)

        # 连接查找、替换按钮
        self.find_button.clicked.connect(self.find_text)
        self.replace_button.clicked.connect(self.replace_text)
        self.replace_all_button.clicked.connect(self.replace_all_text)

        # 支持拖放文件
        self.setAcceptDrops(True)

    def create_actions(self) -> None:
        """创建菜单动作"""
        self.new_file_action = QAction('新建(&N)', self)
        self.new_file_action.setShortcut('Ctrl+N')
        self.new_file_action.triggered.connect(self.new_file)

        self.open_action = QAction('打开(&O)', self)
        self.open_action.setShortcut('Ctrl+O')
        self.open_action.triggered.connect(self.open_file)

        self.save_action = QAction('保存(&S)', self)
        self.save_action.setShortcut('Ctrl+S')
        self.save_action.triggered.connect(self.save_file_ot)

        self.save_as_action = QAction('另存为(&A)', self)
        self.save_as_action.setShortcut('Ctrl+Shift+S')
        self.save_as_action.triggered.connect(self.save_as_file_ot)

        self.close_tab_action = QAction('关闭标签页(&C)', self)
        self.close_tab_action.setShortcut('Ctrl+W')
        self.close_tab_action.triggered.connect(self.close_current_tab)

        self.toggle_find_action = QAction('显示/隐藏查找栏(&F)', self)
        self.toggle_find_action.setShortcut('Ctrl+F')
        self.toggle_find_action.triggered.connect(self.toggle_find_bar)

        self.toggle_replace_action = QAction('显示/隐藏替换栏(&R)', self)
        self.toggle_replace_action.setShortcut('Ctrl+H')
        self.toggle_replace_action.triggered.connect(self.toggle_replace_bar)

        self.increase_font_size_action = QAction('增大字体', self)
        self.increase_font_size_action.triggered.connect(self.increase_font_size)

        self.decrease_font_size_action = QAction('减小字体', self)
        self.decrease_font_size_action.triggered.connect(self.decrease_font_size)

        self.reset_font_size_action = QAction('恢复默认字体', self)
        self.reset_font_size_action.triggered.connect(self.reset_font_size)

    def create_menubar(self) -> None:
        """创建菜单栏并添加动作"""
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

    def save_file_ot(self) -> bool:
        """
        保存当前文件；如果是新文件且未保存则调用“另存为”，否则直接保存
        """
        current_text_edit = self.get_current_text_edit()
        if current_text_edit:
            if current_text_edit.is_new_file and not current_text_edit.file_path:
                self.save_as_file_ot()
                return True
            else:
                try:
                    save_file(current_text_edit, current_text_edit.file_path)
                    current_text_edit.is_saved = True
                    current_text_edit.is_new_file = False
                    update_tab_title(self, current_text_edit)
                    return True
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"保存失败: {e}")
                    return False
        return False

    def save_as_file_ot(self) -> None:
        """另存为当前文件，同时默认文件名自动填入当前文件名（或新文件“未命名”）"""
        current_text_edit = self.get_current_text_edit()
        if current_text_edit:
            # 如果当前文件已有路径，则取其文件名，否则使用"未命名"
            default_name = os.path.basename(current_text_edit.file_path) if current_text_edit.file_path else "未命名"
            file_path, _ = QFileDialog.getSaveFileName(
                self, "另存为", default_name, "文本文件 (*.txt);;所有文件 (*)"
            )
            if file_path:
                save_file(current_text_edit, file_path)
                current_text_edit.file_path = file_path
                current_text_edit.is_saved = True
                current_text_edit.is_new_file = False
                update_tab_title(self, current_text_edit)

    def increase_font_size(self) -> None:
        """增大当前编辑器字体"""
        current_text_edit = self.get_current_text_edit()
        if current_text_edit:
            font = current_text_edit.font()
            new_size = min(font.pointSize() + 1, MAX_FONT_SIZE)
            font.setPointSize(new_size)
            current_text_edit.setFont(font)
            self.update_font_size_buttons()

    def decrease_font_size(self) -> None:
        """减小当前编辑器字体"""
        current_text_edit = self.get_current_text_edit()
        if current_text_edit:
            font = current_text_edit.font()
            new_size = max(font.pointSize() - 1, MIN_FONT_SIZE)
            font.setPointSize(new_size)
            current_text_edit.setFont(font)
            self.update_font_size_buttons()

    def reset_font_size(self) -> None:
        """恢复默认字体大小"""
        current_text_edit = self.get_current_text_edit()
        if current_text_edit:
            font = current_text_edit.font()
            font.setPointSize(DEFAULT_FONT_SIZE)
            current_text_edit.setFont(font)
            self.update_font_size_buttons()

    def get_current_text_edit(self) -> Optional[CustomTextEdit]:
        """获取当前活动标签页中的 CustomTextEdit"""
        current_widget = self.tabs.currentWidget()
        if current_widget:
            return current_widget.findChild(CustomTextEdit)
        return None

    def update_font_size_buttons(self) -> None:
        """根据当前字体大小更新按钮状态"""
        current_text_edit = self.get_current_text_edit()
        if current_text_edit:
            font_size = current_text_edit.font().pointSize()
            self.increase_font_size_action.setEnabled(font_size < MAX_FONT_SIZE)
            self.decrease_font_size_action.setEnabled(font_size > MIN_FONT_SIZE)
        else:
            self.increase_font_size_action.setEnabled(False)
            self.decrease_font_size_action.setEnabled(False)

    def open_file(self) -> None:
        """打开文件并添加到新标签页"""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, '打开文件', '', '文本文件 (*.txt);;所有文件 (*)', options=options)
        if file_name:
            self.add_new_tab(file_name)

    def new_file(self) -> None:
        """
        新建空白文件标签页，新建文件 file_path 为 None，
        标签页标题显示为“未命名”
        """
        text_edit = CustomTextEdit()
        text_edit.is_new_file = True
        text_edit.file_path = None
        try:
            new_file_e(self, text_edit)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"新建文件时发生错误：{e}")
        self.enable_find_replace(True)

    def add_new_tab(self, file_path: str) -> None:
        """添加新标签页并加载指定文件"""
        file_name = os.path.basename(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and not mime_type.startswith('text'):
            QMessageBox.critical(self, "错误", "请选择一个有效的TXT文件")
            return

        if file_path in self.opened_files:
            for index in range(self.tabs.count()):
                tab_widget = self.tabs.widget(index)
                text_edit = tab_widget.findChild(CustomTextEdit)
                if text_edit and text_edit.file_path == file_path:
                    self.tabs.setCurrentIndex(index)
                    return
        else:
            self.opened_files.add(file_path)
            text_edit = CustomTextEdit()
            text_edit.file_path = file_path
            add_new_tab_e(self, text_edit, file_path, file_name)

        self.enable_find_replace(True)
        self.update_font_size_buttons()

    def close_current_tab(self, index: Optional[int] = None) -> None:
        """
        关闭当前标签页；若有未保存内容则提示
        """
        if index is None:
            index = self.tabs.currentIndex()
        current_widget = self.tabs.widget(index)
        if current_widget:
            text_edit = current_widget.findChild(CustomTextEdit)
            if text_edit.file_path and not text_edit.is_saved:
                icon_path = get_resource_path("icon.ico")
                result = show_hint("文件未保存，是否保存？", "提示", icon_path)
                if result == QMessageBox.Save:
                    if self.save_file_ot():
                        close_tab(current_widget, self.tabs)
                        self.opened_files.discard(text_edit.file_path)
                elif result == QMessageBox.Discard:
                    close_tab(current_widget, self.tabs)
                    self.opened_files.discard(text_edit.file_path)
            else:
                close_tab(current_widget, self.tabs)
                if text_edit and text_edit.file_path:
                    self.opened_files.discard(text_edit.file_path)

        if not self.opened_files:
            self.enable_find_replace(False)

    def enable_find_replace(self, enable: bool) -> None:
        """启用或禁用查找与替换功能"""
        self.find_button.setEnabled(enable)
        self.replace_button.setEnabled(enable)
        self.replace_all_button.setEnabled(enable)

    def find_text(self) -> None:
        """触发查找操作"""
        query = self.find_input.text()
        match_case = self.match_case_find_checkbox.isChecked()
        current_text_edit = self.get_current_text_edit()
        if current_text_edit:
            find_text(query, current_text_edit, match_case)

    def replace_text(self) -> None:
        """替换当前匹配项"""
        find_query = self.find_replace_input.text()
        replace_query = self.replace_input.text()
        match_case = self.match_case_replace_checkbox.isChecked()
        current_text_edit = self.get_current_text_edit()
        if current_text_edit:
            replace_text(find_query, replace_query, current_text_edit, match_case)

    def replace_all_text(self) -> None:
        """替换所有匹配项"""
        find_query = self.find_replace_input.text()
        replace_query = self.replace_input.text()
        match_case = self.match_case_replace_checkbox.isChecked()
        current_text_edit = self.get_current_text_edit()
        if current_text_edit:
            replace_all_text(find_query, replace_query, current_text_edit, match_case)

    def toggle_find_bar(self) -> None:
        """显示或隐藏查找栏；若替换栏显示则先隐藏"""
        if self.replace_bar.isVisible():
            self.replace_bar.setVisible(False)
        visible = not self.find_bar.isVisible()
        self.find_bar.setVisible(visible)
        if visible:
            self.find_input.setFocus()

    def toggle_replace_bar(self) -> None:
        """显示或隐藏替换栏；若查找栏显示则先隐藏"""
        if self.find_bar.isVisible():
            self.find_bar.setVisible(False)
        visible = not self.replace_bar.isVisible()
        self.replace_bar.setVisible(visible)
        if visible:
            self.find_replace_input.setFocus()

    def closeEvent(self, event) -> None:
        """关闭程序前检查未保存文件"""
        unsaved_files = [
            self.tabs.widget(i).findChild(CustomTextEdit)
            for i in range(self.tabs.count())
            if not self.tabs.widget(i).findChild(CustomTextEdit).is_saved
        ]
        if unsaved_files:
            icon_path = get_resource_path("icon.ico")
            result = show_hint_e("有未保存的文件，是否保存？", "提示", icon_path)
            if result == QMessageBox.Save:
                if not self.save_file_ot():
                    event.ignore()
                    return
            elif result == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
                return
        event.accept()

    def dragEnterEvent(self, event) -> None:
        """接受包含 URL 的拖拽事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        """处理拖放文件事件，添加新标签页"""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.exists(file_path):
                self.add_new_tab(file_path)
        event.accept()

    def wheelEvent(self, event) -> None:
        """Ctrl+滚轮调节字体大小"""
        if event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.increase_font_size()
            elif delta < 0:
                self.decrease_font_size()
        event.accept()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Ctrl+中键恢复默认字体大小"""
        if event.button() == Qt.MiddleButton and event.modifiers() == Qt.ControlModifier:
            self.reset_font_size()
        super().mousePressEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TextEditor()
    window.show()
    sys.exit(app.exec())
