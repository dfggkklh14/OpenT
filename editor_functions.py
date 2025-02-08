#editor_functions.py
import re
from PyQt5.QtGui import QTextDocument, QPixmap
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QWidget, QVBoxLayout


def save_file(text_edit, file_path):
    """保存文件内容到原路径，作用是覆写"""
    try:
        if file_path:  # 如果传入了有效的路径
            # 使用 io.open 来显式指定编码方式
            import io
            with io.open(file_path, 'w', encoding='utf-8') as file:
                file.write(text_edit.toPlainText())
        else:
            raise ValueError("无法获取文件路径！")
    except Exception as e:
        QMessageBox.critical(text_edit, "错误", f"保存文件时出错: {e}")

def save_as_file(text_edit, parent):
    """另存为指定路径，作用是保存其他名称的文件，从而不影响原文件"""
    file_name, _ = QFileDialog.getSaveFileName(parent, '另存为', '', '文本文件 (*.txt)')
    if file_name:
        save_file(text_edit, file_name, overwrite=False)  # 另存为时不覆盖原文件

def find_text(query, text_edit, match_case=False):
    """循环查找文本，直到文本末尾，之后从文本开始再查找"""
    try:
        cursor = text_edit.textCursor()  # 获取当前光标
        options = QTextDocument.FindFlags()
        if match_case:
            options |= QTextDocument.FindCaseSensitively  # 设置匹配大小写选项

        if cursor.isNull():  # 如果光标为空，设置为文档开头
            cursor.setPosition(0)

        while True:
            cursor = text_edit.document().find(query, cursor, options)
            if cursor.isNull():  # 如果未找到文本
                # 一轮查找完毕后，重新从文档开头开始查找
                cursor.setPosition(0)
                cursor = text_edit.document().find(query, cursor, options)
                if cursor.isNull():  # 再次没有找到，提示并结束
                    QMessageBox.information(text_edit, "提示", "未找到指定文本！")
                    return None

            text_edit.setTextCursor(cursor)  # 将光标定位到找到的文本位置
            text_edit.ensureCursorVisible()  # 确保光标可见
            text_edit.setFocus()  # 自动切换焦点到文本框
            return cursor  # 返回光标，以便后续操作
    except Exception as e:
        QMessageBox.critical(text_edit, "错误", f"发生错误: {e}")
        return None

def replace_text(find_query, replace_query, text_edit, match_case=False):
    """逐个替换文本"""
    try:
        if not find_query or not find_query.strip():
            QMessageBox.warning(text_edit, "警告", "查找文本不能为空")
            return
        cursor = text_edit.textCursor()  # 获取当前光标
        # 如果匹配大小写敏感
        options = QTextDocument.FindFlags()
        if match_case:
            options |= QTextDocument.FindCaseSensitively
        while True:
            cursor = text_edit.document().find(find_query, cursor, options)  # 查找下一个匹配项
            if cursor.isNull():  # 没有找到匹配文本
                cursor.setPosition(0)  # 如果到达末尾，重新从开头查找
                cursor = text_edit.document().find(find_query, cursor, options)
                if cursor.isNull():  # 如果重新查找还是没有匹配文本，退出
                    QMessageBox.information(text_edit, "提示", "没有更多的文本可以替换！")
                    return
            cursor.insertText(replace_query)  # 直接插入替换文本
            # 更新光标并确保可见
            text_edit.setTextCursor(cursor)
            text_edit.ensureCursorVisible()
            return  # 只替换一个匹配项后返回，等待下一次调用
    except Exception as e:
        QMessageBox.critical(text_edit, "错误", f"替换时出现问题: {e}")

def replace_all_text(find_query, replace_query, text_edit, match_case=False):
    """使用 re.sub 替换文本，支持撤销功能"""
    try:
        if not find_query or not find_query.strip():
            QMessageBox.warning(text_edit, "警告", "查找文本不能为空")
            return
        # 获取当前 QTextEdit 的文本内容
        document = text_edit.document()
        cursor = text_edit.textCursor()

        # 开始一个撤销块
        cursor.beginEditBlock()

        # 获取完整文本
        full_text = document.toPlainText()

        # 使用 re.sub 替换文本
        flags = 0 if match_case else re.IGNORECASE
        new_text, count = re.subn(find_query, replace_query, full_text, flags=flags)

        # 如果有替换内容
        if count > 0:
            # 将新的文本内容设置到 QTextEdit 中
            cursor.select(cursor.Document)
            cursor.insertText(new_text)
        else:
            QMessageBox.information(text_edit, "结果", "未找到匹配项。")

        # 结束撤销块
        cursor.endEditBlock()

        text_edit.setFocus()

    except Exception as e:
        QMessageBox.critical(text_edit, "错误", f"替换时出现问题: {e}")

def new_file_e(self, text_edit):
    """创建新标签并初始化"""
    tab_widget = QWidget()
    tab_layout = QVBoxLayout(tab_widget)
    tab_layout.setContentsMargins(0, 0, 0, 0)
    tab_layout.addWidget(text_edit)

    tab_index = self.tabs.addTab(tab_widget, "未命名")  # 默认标签为“未命名”
    self.tabs.setCurrentIndex(tab_index)

    # 初始化标签名称
    self.update_tab_title(text_edit)

def add_new_tab_e(self, text_edit, file_path, file_name):
    """创建新的标签页"""
    tab_widget = QWidget()
    tab_layout = QVBoxLayout(tab_widget)
    tab_layout.setContentsMargins(0, 0, 0, 0)  # 取消CustomTextEdit的边距
    tab_layout.addWidget(text_edit)

    # 添加新标签
    tab_index = self.tabs.addTab(tab_widget, file_name)
    self.tabs.setCurrentIndex(tab_index)

    # 加载文件内容
    text_edit.load_file_content(file_path)

    # 初始化标签名称
    self.update_tab_title(text_edit)

    # 设置工具提示为文件完整路径
    self.tabs.setTabToolTip(tab_index, file_path)

def close_tab(widget, tabs):
    """关闭标签页"""
    tab_index = tabs.indexOf(widget)
    if tab_index != -1:
        tabs.removeTab(tab_index)  # 删除标签页
        widget.deleteLater()  # 删除控件

def show_hint(message, tips, icon_path=None):
    """显示提示信息弹窗，返回按钮点击结果"""
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)  # 使用正确的图标类型
    msg.setText(message)
    msg.setWindowTitle(tips)
    # 设置按钮文本为中文
    msg.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
    msg.button(QMessageBox.Save).setText("保存")
    msg.button(QMessageBox.Discard).setText("不保存")
    msg.button(QMessageBox.Cancel).setText("取消")
    msg.setDefaultButton(QMessageBox.Save)  # 默认选择“保存”
    if icon_path:
        msg.setWindowIcon(QIcon(icon_path))  # 设置窗口图标
        msg.setIcon(QMessageBox.NoIcon)  # 移除默认图标
    # 使用 exec() 而不是 exec_()
    result = msg.exec()  # 使用 exec() 替代 exec_()
    # 返回按钮点击的结果
    return result

from PyQt5.QtWidgets import QMessageBox, QDialog
from PyQt5.QtGui import QIcon

def show_hint_e(message, tips, icon_path=None):
    """显示提示信息弹窗，返回按钮点击结果"""
    msg = QMessageBox()
    msg.setText(message)
    msg.setWindowTitle(tips)

    # 设置按钮文本为中文
    msg.setStandardButtons(QMessageBox.Discard | QMessageBox.Cancel)
    msg.button(QMessageBox.Discard).setText("不保存")
    msg.button(QMessageBox.Cancel).setText("取消")
    msg.setDefaultButton(QMessageBox.Save)  # 默认选择“保存”

    # 设置自定义图标（如果提供了图标路径）
    if icon_path:
        msg.setWindowIcon(QIcon(icon_path))  # 设置窗口图标
        msg.setIcon(QMessageBox.NoIcon)  # 移除默认图标

    # 使用 exec() 而不是 exec_()
    result = msg.exec()  # 使用 exec() 替代 exec_()
    # 返回按钮点击的结果
    return result
