# -*- coding: utf-8 -*-
"""
输入区组件 — 文本输入框 + 模型选择弹出菜单 + @ 补全菜单 + 发送按钮。
两个模型选择入口（手动点击和 @ 触发）使用完全相同的 QListWidget 弹出组件，
确保视觉风格一致。
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QTextEdit,
    QPushButton, QListWidget, QListWidgetItem, QFrame,
    QLabel, QFileDialog, QMessageBox
)
from PyQt5.QtCore import pyqtSignal, Qt, QSize, QVariantAnimation
from PyQt5.QtGui import QFont, QTextCursor, QKeyEvent, QIcon, QPainter, QPen, QColor, QSyntaxHighlighter, QTextCharFormat
import os
import re
from ui.styles import INPUT_AREA_STYLE, AT_MENU_STYLE
from core.model_manager import ModelManager, MODEL_ICONS
from core.file_handler import FileHandler, FileAttachment


class AtHighlighter(QSyntaxHighlighter):
    """用于高亮 @模型名 的语法高亮器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.formats = {}
        
        configs = {
            "qwen": ("#f3e8ff", "#7e22ce"),       # 💜 紫色
            "glm": ("#dcfce7", "#15803d"),        # 💚 绿色
            "kimi": ("#ffedd5", "#c2410c"),       # 🧡 橙色
            "deepseek": ("#e0e7ff", "#1d4ed8"),   # 💙 深蓝色
            "minimax": ("#fee2e2", "#b91c1c"),    # ❤️ 红色
            "all": ("#f3f4f6", "#374151")         # 🤍 灰色
        }
        
        for name, (bg, fg) in configs.items():
            fmt = QTextCharFormat()
            fmt.setBackground(QColor(bg))
            fmt.setForeground(QColor(fg))
            fmt.setFontWeight(QFont.Bold)
            self.formats[name] = fmt

        self.default_format = QTextCharFormat()
        self.default_format.setBackground(QColor("#e8efff"))
        self.default_format.setForeground(QColor("#1a56ff"))
        self.default_format.setFontWeight(QFont.Bold)

    def highlightBlock(self, text):
        for match in re.finditer(r'@[^\s]+', text):
            tag = match.group()[1:].lower()
            fmt = self.formats.get(tag, self.default_format)
            self.setFormat(match.start(), match.end() - match.start(), fmt)

class AnimatedSendButton(QPushButton):
    """支持箭头从向右旋转到向上的发送按钮，在输出状态时变成停止按钮"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 90.0
        self.has_text = False
        self._sending = False
        self.setProperty("has_text", self.has_text)
        
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(200)
        self.anim.valueChanged.connect(self._on_angle_changed)

    def set_sending(self, sending: bool):
        self._sending = sending
        self.update()

    def _on_angle_changed(self, value):
        self.angle = float(value)
        self.update()

    def enterEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.angle)
        self.anim.setEndValue(0.0)
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.angle)
        self.anim.setEndValue(90.0)
        self.anim.start()
        super().leaveEvent(event)

    def set_has_text(self, has_text: bool):
        if self.has_text != has_text:
            self.has_text = has_text
            self.setProperty("has_text", has_text)
            self.style().unpolish(self)
            self.style().polish(self)
            self.update()

    def paintEvent(self, event):
        # 先绘制背景（按 QSS 设定）
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.translate(self.rect().center())
        
        if self._sending:
            # 绘制正方形停止图标 (Stop)
            painter.setBrush(QColor("white"))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(-4, -4, 8, 8, 2, 2)
            painter.end()
            return
            
        # 否则绘制箭头并考虑旋转
        painter.rotate(self.angle)
        
        # 绘制箭头
        pen = QPen(QColor("white"))
        pen.setWidth(2)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        
        # 使用 QPointF 浮点数画线避免因为整数转换导致的像素中心偏离
        from PyQt5.QtCore import QPointF
        painter.drawLine(QPointF(0, -4.5), QPointF(0, 5.5))        # 竖线
        painter.drawLine(QPointF(0, -4.5), QPointF(-4.5, 0))       # 左翼
        painter.drawLine(QPointF(0, -4.5), QPointF(4.5, 0))        # 右翼
        painter.end()


class InputTextEdit(QTextEdit):
    """自定义文本输入框，支持 Enter 发送和 @ 触发，自动伸缩高度"""
    enter_pressed = pyqtSignal()
    at_typed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("inputBox")
        self.setPlaceholderText("Send a message")
        self.setFixedHeight(46)
        self.setAcceptRichText(False)
        self.document().documentLayout().documentSizeChanged.connect(self._adjust_height)

    def _adjust_height(self, _=None):
        doc_height = self.document().size().height()
        margins = self.contentsMargins()
        # +14 is padding roughly
        target_height = int(doc_height + margins.top() + margins.bottom() + 14)
        new_height = max(46, min(target_height, 200))
        if self.height() != new_height:
            self.setFixedHeight(new_height)

    def keyPressEvent(self, event: QKeyEvent):
        # Enter 发送（Shift+Enter 换行）
        if event.key() == Qt.Key_Return and not (event.modifiers() & Qt.ShiftModifier):
            self.enter_pressed.emit()
            return
        super().keyPressEvent(event)
        # 检测 @ 输入
        if event.text() == "@":
            self.at_typed.emit()

    # ---- 拖拽事件处理 ----
    file_dropped = pyqtSignal(str)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    self.file_dropped.emit(url.toLocalFile())
        event.accept()


class InputWidget(QWidget):
    """输入区域：模型选择 + 文本框 + 附件按钮 + 发送按钮"""

    # 信号：(用户输入文本, 选中的模型 key 列表, 附件列表)
    message_submitted = pyqtSignal(str, list, list)
    stop_requested = pyqtSignal()

    def __init__(self, model_manager: ModelManager, parent=None):
        super().__init__(parent)
        self.model_manager = model_manager
        self.setObjectName("inputArea")
        self.setStyleSheet(INPUT_AREA_STYLE)
        self._attachments = []
        self._init_ui()
        self._init_model_popup()
        self._init_at_menu()
        self._sending = False

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(80, 8, 80, 24)
        main_layout.setSpacing(0)

        # 最外层包裹框
        self.container = QFrame()
        self.container.setObjectName("inputContainer")
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(12, 12, 12, 12)
        container_layout.setSpacing(8)

        # 附件缩略图展示区
        self.attach_container = QWidget()
        self.attach_layout = QHBoxLayout(self.attach_container)
        self.attach_layout.setContentsMargins(0, 0, 0, 0)
        self.attach_layout.setSpacing(8)
        self.attach_layout.addStretch()
        container_layout.addWidget(self.attach_container)
        self.attach_container.hide()

        # 文本输入框 (无边框)
        self.text_edit = InputTextEdit()
        self.text_edit.enter_pressed.connect(self._on_submit)
        self.text_edit.at_typed.connect(self._show_at_menu)
        self.text_edit.textChanged.connect(self._on_text_changed)
        self.text_edit.file_dropped.connect(self._add_file_attachment)
        self.highlighter = AtHighlighter(self.text_edit.document())
        self.text_edit.setAcceptDrops(True)
        container_layout.addWidget(self.text_edit)

        # 底部工具栏
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 0)

        # 模型选择按钮 (仅 SVG 图标，点击弹出 QListWidget)
        self.model_btn = QPushButton()
        self.model_btn.setObjectName("modelBtn")
        self.model_btn.setCursor(Qt.PointingHandCursor)
        self.model_btn.setToolTip("选择模型")
        icon_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icon")
        self.model_btn.setIcon(QIcon(os.path.join(icon_dir, "模型管理.svg")))
        self.model_btn.setIconSize(QSize(20, 20))
        self.model_btn.clicked.connect(self._show_model_popup)
        toolbar_layout.addWidget(self.model_btn)

        # 附件按钮
        self.attach_btn = QPushButton()
        self.attach_btn.setCursor(Qt.PointingHandCursor)
        self.attach_btn.setToolTip("添加附件 (文档)")
        self.attach_btn.setIcon(QIcon(os.path.join(icon_dir, "文件.svg")))
        self.attach_btn.setIconSize(QSize(24, 24))
        self.attach_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 4px;
            }
            QPushButton:hover {
                background: #f1f5f9;
                border-radius: 6px;
            }
        """)
        self.attach_btn.clicked.connect(self._open_file_dialog)
        toolbar_layout.addWidget(self.attach_btn)

        toolbar_layout.addStretch()

        # 发送按钮
        self.send_btn = AnimatedSendButton()
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.clicked.connect(self._on_submit)
        toolbar_layout.addWidget(self.send_btn)

        container_layout.addLayout(toolbar_layout)
        main_layout.addWidget(self.container)

    def _on_text_changed(self):
        text = self.text_edit.toPlainText().strip()
        self.send_btn.set_has_text(bool(text) or len(self._attachments) > 0)

    # ---- 统一的弹出菜单组件 ----

    def _create_popup_list(self) -> QListWidget:
        """创建统一样式的弹出 QListWidget"""
        popup = QListWidget(self)
        popup.setObjectName("atMenu")
        popup.setStyleSheet(AT_MENU_STYLE)
        popup.setWindowFlags(Qt.Popup)
        popup.setFocusPolicy(Qt.NoFocus)
        popup.hide()
        return popup

    def _populate_model_items(self, popup: QListWidget, include_all_first: bool = False):
        """向弹出列表填充模型项目"""
        popup.clear()
        enabled = self.model_manager.get_enabled_models()

        if include_all_first:
            # @ 菜单：ALL 在最前面
            item_all = QListWidgetItem(f"🌐 ALL (所有模型)")
            item_all.setData(Qt.UserRole, "all")
            popup.addItem(item_all)

        for key, config in enabled.items():
            icon = self.model_manager.get_model_icon(key)
            item = QListWidgetItem(f"{icon} {config.display_name}")
            item.setData(Qt.UserRole, key)
            popup.addItem(item)

        if not include_all_first:
            # 手动选择菜单：ALL 在最后面，带分隔
            separator = QListWidgetItem()
            separator.setFlags(Qt.NoItemFlags)
            separator.setSizeHint(QSize(0, 1))
            popup.addItem(separator)

            item_all = QListWidgetItem(f"🌐 ALL Models")
            item_all.setData(Qt.UserRole, "all")
            popup.addItem(item_all)

        return len(enabled)

    def _calc_popup_geometry(self, popup: QListWidget, item_count: int, anchor_widget, above: bool = True):
        """计算弹出列表的位置和大小"""
        popup.setFixedWidth(180)
        popup.setFixedHeight(min(item_count * 34 + 24, 280))
        
        if above:
            # 在锚点上方弹出
            global_pos = anchor_widget.mapToGlobal(anchor_widget.rect().topLeft())
            popup.move(global_pos.x(), global_pos.y() - popup.height() - 4)
        else:
            # 在光标上方弹出
            global_pos = anchor_widget
            popup.move(global_pos.x(), global_pos.y() - popup.height() - 5)

    # ---- 模型选择弹出（手动点击按钮触发） ----

    def _init_model_popup(self):
        """初始化手动模型选择弹出菜单"""
        self.model_popup = self._create_popup_list()
        self.model_popup.itemClicked.connect(self._on_model_popup_selected)
        self._current_model_sel = None

    def _show_model_popup(self):
        """点击模型按钮时弹出选择列表"""
        count = self._populate_model_items(self.model_popup, include_all_first=False)
        self._calc_popup_geometry(self.model_popup, count + 2, self.model_btn, above=True)
        self.model_popup.show()

    def _on_model_popup_selected(self, item: QListWidgetItem):
        """手动选择模型后，在输入框插入 @模型名"""
        if not item.flags() & Qt.ItemIsEnabled:
            return  # 分隔行
        key = item.data(Qt.UserRole)
        self.model_popup.hide()
        self._insert_model_tag(key)

    # ---- @ 补全弹出菜单 ----

    def _init_at_menu(self):
        """初始化 @ 补全菜单"""
        self.at_menu = self._create_popup_list()
        self.at_menu.itemClicked.connect(self._on_at_item_selected)

    def _show_at_menu(self):
        """在输入框光标位置弹出 @ 补全菜单"""
        count = self._populate_model_items(self.at_menu, include_all_first=True)
        cursor_rect = self.text_edit.cursorRect()
        global_pos = self.text_edit.mapToGlobal(cursor_rect.bottomLeft())
        self._calc_popup_geometry(self.at_menu, count + 1, global_pos, above=False)
        self.at_menu.show()

    def _on_at_item_selected(self, item: QListWidgetItem):
        """选择 @ 菜单项后插入文本"""
        key = item.data(Qt.UserRole)
        self.at_menu.hide()
        # 替换掉已输入的 @
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, 1)
        if cursor.selectedText() == "@":
            cursor.removeSelectedText()
        self._insert_model_tag(key, cursor)
        self.text_edit.setFocus()

    # ---- 共用插入逻辑 ----

    def _insert_model_tag(self, key: str, cursor=None):
        """向输入框插入 @模型名 标签"""
        self._current_model_sel = key
        if cursor is None:
            cursor = self.text_edit.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.text_edit.setTextCursor(cursor)
            # 确保与前面的文字有空格
            if self.text_edit.toPlainText().strip() and not self.text_edit.toPlainText().endswith(" "):
                cursor.insertText(" ")

        if key == "all":
            cursor.insertText("@ALL ")
        else:
            config = self.model_manager.get_model(key)
            display = config.display_name if config else key
            cursor.insertText(f"@{display} ")

        self.text_edit.setFocus()

    def _refresh_model_select(self):
        """刷新模型列表（兼容旧接口名称）"""
        pass  # 弹出菜单每次弹出时动态构建，无需预先刷新

    def _on_submit(self):
        """发送消息或停止请求"""
        if self._sending:
            self.stop_requested.emit()
            return

        text = self.text_edit.toPlainText().strip()
        if not text and not self._attachments:
            return

        # 解析目标模型
        model_keys = self._parse_model_keys(text)
        # 清理输入框中的 @前缀（提取纯内容）
        clean_text = self._clean_input(text)

        if clean_text or self._attachments:
            # 传递一份 copy 并清空
            attachments_copy = list(self._attachments)
            self.message_submitted.emit(clean_text, model_keys, attachments_copy)
            
            self.text_edit.clear()
            self._attachments.clear()
            self._update_attachment_ui()

    def _parse_model_keys(self, text: str) -> list:
        """从输入文本解析目标模型"""
        import re
        selected_key = self._current_model_sel
        BOUNDARY = r'(?![a-zA-Z0-9_])'

        # 检查首部是否为 @all
        if re.match(r'^\s*@all' + BOUNDARY, text, re.IGNORECASE):
            return list(self.model_manager.get_enabled_models().keys())

        # 构造并按名称长度降序排列（防止部分匹配）
        enabled_models = list(self.model_manager.get_enabled_models().items())
        enabled_models.sort(key=lambda x: max(len(x[0]), len(x[1].display_name)), reverse=True)

        # 仅从文本开头查找 @指令
        for key, config in enabled_models:
            pattern_display = r'^\s*@' + re.escape(config.display_name) + BOUNDARY
            pattern_key = r'^\s*@' + re.escape(key) + BOUNDARY
            if re.match(pattern_display, text, re.IGNORECASE) or re.match(pattern_key, text, re.IGNORECASE):
                return [key]

        # 如果没有匹配的开场指令，则使用菜单选择的模型
        if selected_key == "all":
            return list(self.model_manager.get_enabled_models().keys())
        elif selected_key:
            return [selected_key]

        # 默认使用第一个启用的模型
        enabled = self.model_manager.get_enabled_models()
        if enabled:
            return [list(enabled.keys())[0]]
        return []

    def _clean_input(self, text: str) -> str:
        """清理输入文本，严格只移除最开头的 @ 前缀"""
        import re
        BOUNDARY = r'(?![a-zA-Z0-9_])'
        
        # 移除首部的 @all
        if re.match(r'^\s*@all' + BOUNDARY, text, flags=re.IGNORECASE):
            return re.sub(r'^\s*@all\s*', '', text, count=1, flags=re.IGNORECASE).strip()

        all_models = list(self.model_manager.get_all_models().items())
        all_models.sort(key=lambda x: max(len(x[0]), len(x[1].display_name)), reverse=True)

        # 移除首部的 @模型名
        for key, config in all_models:
            pattern_display = r'^\s*@' + re.escape(config.display_name) + BOUNDARY
            if re.match(pattern_display, text, flags=re.IGNORECASE):
                return re.sub(r'^\s*@' + re.escape(config.display_name) + r'\s*', '', text, count=1, flags=re.IGNORECASE).strip()
            
            pattern_key = r'^\s*@' + re.escape(key) + BOUNDARY
            if re.match(pattern_key, text, flags=re.IGNORECASE):
                return re.sub(r'^\s*@' + re.escape(key) + r'\s*', '', text, count=1, flags=re.IGNORECASE).strip()
                
        return text.strip()

    def set_sending(self, sending: bool):
        """设置发送状态（变为停止按钮）"""
        self._sending = sending
        self.send_btn.set_sending(sending)
        self.text_edit.setReadOnly(sending)

    def refresh_models(self):
        """刷新模型列表（设置更改后调用）"""
        pass  # 弹出菜单每次弹出时动态构建

    # ---- 附件相关处理 ----

    def _open_file_dialog(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "选择附件",
            "",
            "文档文件 (*.txt *.md *.pdf *.docx *.xlsx *.csv)"
        )
        if filename:
            self._add_file_attachment(filename)

    def _add_file_attachment(self, filepath: str):
        try:
            attachment = FileHandler.process_file(filepath)
            if attachment:
                self._attachments.append(attachment)
                self._update_attachment_ui()
                self._on_text_changed() # 更新发送按钮状态
        except Exception as e:
            QMessageBox.warning(self, "附件加载失败", str(e))

    def _remove_attachment(self, index: int):
        if 0 <= index < len(self._attachments):
            self._attachments.pop(index)
            self._update_attachment_ui()
            self._on_text_changed()

    def _update_attachment_ui(self):
        # 先清空
        while self.attach_layout.count():
            item = self.attach_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if self._attachments:
            self.attach_container.show()
            for idx, attachment in enumerate(self._attachments):
                # 创建气泡
                btn = QPushButton()
                btn.setText(f"📄 {attachment.file_name}  ✕")
                btn.setToolTip("点击移除")
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f1f5f9;
                        border: 1px solid #cbd5e1;
                        border-radius: 12px;
                        padding: 4px 10px;
                        font-size: 12px;
                        color: #334155;
                    }
                    QPushButton:hover {
                        background-color: #fee2e2;
                        border-color: #fca5a5;
                        color: #b91c1c;
                    }
                """)
                btn.clicked.connect(lambda checked, i=idx: self._remove_attachment(i))
                self.attach_layout.addWidget(btn)
            self.attach_layout.addStretch()
        else:
            self.attach_container.hide()
