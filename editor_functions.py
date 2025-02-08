import os
import re
import io
import sys

from PyQt5.QtGui import QTextDocument, QIcon
from PyQt5.QtWidgets import QMessageBox, QWidget, QVBoxLayout

def get_resource_path(relative_path: str) -> str:
    """
    根据运行环境返回资源文件的绝对路径，
    如果使用 PyInstaller 打包，则使用 sys._MEIPASS 作为基础路径，
    否则使用当前模块所在的目录。
    """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def get_resource_url(relative_path: str) -> str:
    """
    将资源文件路径转换为 QSS 使用的格式：
    返回绝对路径，使用正斜杠，不附带 file:/// 前缀。
    例如返回：D:/AppTests/tetee/close_icon.png
    """
    path = get_resource_path(relative_path)
    path = os.path.abspath(path)  # 确保是绝对路径
    path = path.replace("\\", "/")  # 替换为正斜杠
    return path

def save_file(text_edit, file_path: str) -> None:
    """
    将 text_edit 的内容保存到指定文件路径（覆盖写入）
    """
    try:
        if file_path:
            with io.open(file_path, 'w', encoding='utf-8') as file:
                file.write(text_edit.toPlainText())
        else:
            raise ValueError("无法获取文件路径！")
    except Exception as e:
        QMessageBox.critical(text_edit, "错误", f"保存文件时出错: {e}")

def find_text(query: str, text_edit, match_case: bool = False):
    """
    在 text_edit 中查找 query，从当前位置开始查找，未找到则从头开始
    """
    try:
        cursor = text_edit.textCursor()
        options = QTextDocument.FindFlags()
        if match_case:
            options |= QTextDocument.FindCaseSensitively

        if cursor.isNull():
            cursor.setPosition(0)

        while True:
            cursor = text_edit.document().find(query, cursor, options)
            if cursor.isNull():
                cursor.setPosition(0)
                cursor = text_edit.document().find(query, cursor, options)
                if cursor.isNull():
                    QMessageBox.information(text_edit, "提示", "未找到指定文本！")
                    return None

            text_edit.setTextCursor(cursor)
            text_edit.ensureCursorVisible()
            text_edit.setFocus()
            return cursor
    except Exception as e:
        QMessageBox.critical(text_edit, "错误", f"发生错误: {e}")
        return None

def replace_text(find_query: str, replace_query: str, text_edit, match_case: bool = False) -> None:
    """
    在 text_edit 中替换第一个匹配项
    """
    try:
        if not find_query.strip():
            QMessageBox.warning(text_edit, "警告", "查找文本不能为空")
            return

        cursor = text_edit.textCursor()
        options = QTextDocument.FindFlags()
        if match_case:
            options |= QTextDocument.FindCaseSensitively

        while True:
            cursor = text_edit.document().find(find_query, cursor, options)
            if cursor.isNull():
                cursor.setPosition(0)
                cursor = text_edit.document().find(find_query, cursor, options)
                if cursor.isNull():
                    QMessageBox.information(text_edit, "提示", "没有更多的文本可以替换！")
                    return
            cursor.insertText(replace_query)
            text_edit.setTextCursor(cursor)
            text_edit.ensureCursorVisible()
            return
    except Exception as e:
        QMessageBox.critical(text_edit, "错误", f"替换时出现问题: {e}")

def replace_all_text(find_query: str, replace_query: str, text_edit, match_case: bool = False) -> None:
    """
    在 text_edit 中替换所有匹配项（支持撤销操作）
    """
    try:
        if not find_query.strip():
            QMessageBox.warning(text_edit, "警告", "查找文本不能为空")
            return

        cursor = text_edit.textCursor()
        document = text_edit.document()

        cursor.beginEditBlock()
        full_text = document.toPlainText()
        flags = 0 if match_case else re.IGNORECASE
        new_text, count = re.subn(find_query, replace_query, full_text, flags=flags)

        if count > 0:
            cursor.select(cursor.Document)
            cursor.insertText(new_text)
        else:
            QMessageBox.information(text_edit, "结果", "未找到匹配项。")
        cursor.endEditBlock()
        text_edit.setFocus()
    except Exception as e:
        QMessageBox.critical(text_edit, "错误", f"替换时出现问题: {e}")

def update_tab_title(parent, text_edit) -> None:
    """
    根据文件名和保存状态更新标签标题，
    parent 为包含 tabs 的主窗口对象
    """
    index = parent.tabs.indexOf(text_edit.parent())
    if index != -1:
        file_name = os.path.basename(text_edit.file_path) if text_edit.file_path else "未命名"
        suffix = "*" if not text_edit.is_saved else ""
        max_length = 7
        if len(file_name) + len(suffix) > max_length:
            truncated_name = f"{file_name[:max_length - 3 - len(suffix)]}..."
        else:
            truncated_name = file_name
        tab_text = f"{truncated_name}{suffix}"
        parent.tabs.setTabText(index, tab_text)
        parent.tabs.setTabToolTip(index, text_edit.file_path if text_edit.file_path else "")

def new_file_e(parent, text_edit) -> None:
    """
    在新的标签页中创建一个新文件
    """
    tab_widget = QWidget()
    tab_layout = QVBoxLayout(tab_widget)
    tab_layout.setContentsMargins(0, 0, 0, 0)
    tab_layout.addWidget(text_edit)

    tab_index = parent.tabs.addTab(tab_widget, "未命名")
    parent.tabs.setCurrentIndex(tab_index)
    update_tab_title(parent, text_edit)

def add_new_tab_e(parent, text_edit, file_path: str, file_name: str) -> None:
    """
    添加一个新标签页，并加载指定文件的内容
    """
    tab_widget = QWidget()
    tab_layout = QVBoxLayout(tab_widget)
    tab_layout.setContentsMargins(0, 0, 0, 0)
    tab_layout.addWidget(text_edit)

    tab_index = parent.tabs.addTab(tab_widget, file_name)
    parent.tabs.setCurrentIndex(tab_index)
    text_edit.load_file_content(file_path)
    update_tab_title(parent, text_edit)
    parent.tabs.setTabToolTip(tab_index, file_path)

def close_tab(widget, tabs) -> None:
    """
    关闭包含 widget 的标签页
    """
    tab_index = tabs.indexOf(widget)
    if tab_index != -1:
        tabs.removeTab(tab_index)
        widget.deleteLater()

def show_hint(message: str, title: str, icon_path: str = None) -> int:
    """
    显示提示对话框，包含“保存”、“不保存”、“取消”按钮，返回用户点击结果
    """
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setText(message)
    msg.setWindowTitle(title)
    msg.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
    msg.button(QMessageBox.Save).setText("保存")
    msg.button(QMessageBox.Discard).setText("不保存")
    msg.button(QMessageBox.Cancel).setText("取消")
    msg.setDefaultButton(QMessageBox.Save)
    if icon_path:
        msg.setWindowIcon(QIcon(icon_path))
        msg.setIcon(QMessageBox.NoIcon)
    result = msg.exec()
    return result

def show_hint_e(message: str, title: str, icon_path: str = None) -> int:
    """
    显示提示对话框，包含“不保存”和“取消”按钮，返回用户点击结果
    """
    msg = QMessageBox()
    msg.setText(message)
    msg.setWindowTitle(title)
    msg.setStandardButtons(QMessageBox.Discard | QMessageBox.Cancel)
    msg.button(QMessageBox.Discard).setText("不保存")
    msg.button(QMessageBox.Cancel).setText("取消")
    msg.setDefaultButton(QMessageBox.Discard)
    if icon_path:
        msg.setWindowIcon(QIcon(icon_path))
        msg.setIcon(QMessageBox.NoIcon)
    result = msg.exec()
    return result
