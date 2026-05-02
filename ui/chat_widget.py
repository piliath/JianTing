# -*- coding: utf-8 -*-
"""
聊天展示区组件 — 使用 QWebEngineView 渲染聊天消息。
支持流式追加、Markdown 代码块渲染和打字动画。
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtCore import QUrl, pyqtSlot
import html as html_module
from ui.styles import CHAT_HTML_CSS
from core.model_manager import MODEL_ICONS


class ChatPage(QWebEnginePage):
    """自定义页面，禁止导航到外部链接"""
    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        if nav_type == QWebEnginePage.NavigationTypeLinkClicked:
            return False
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)


class ChatWidget(QWidget):
    """聊天消息展示区"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._message_ids = {}  # model_key -> 当前正在流式输出的消息 DOM id
        self._msg_counter = 0

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.web_view = QWebEngineView()
        page = ChatPage(self.web_view)
        self.web_view.setPage(page)
        layout.addWidget(self.web_view)

        self._load_base_html()

    def _load_base_html(self):
        """加载基础 HTML 模板"""
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>{CHAT_HTML_CSS}</style>
<!-- 引入特定版本的 marked.js 保证 API 稳定 -->
<script src="https://cdn.jsdelivr.net/npm/marked@4.3.0/marked.min.js"></script>
<!-- 引入云端鸿蒙字体 -->
<link rel="stylesheet" href="https://s1.hdslb.com/bfs/static/jinkela/long/font/regular.css" />
</head>
<body>
<div id="chat-container">
    <div class="welcome">
        <div class="welcome-icon">
            <svg viewBox="0 0 256 256" stroke="currentColor" stroke-width="8" fill="none" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <mask id="brain-cutout">
                        <rect width="256" height="256" fill="white" stroke="none" />
                        <circle cx="180" cy="76" r="32" fill="black" stroke="none" />
                    </mask>
                </defs>
                <circle cx="124" cy="132" r="76" mask="url(#brain-cutout)" />
                <circle cx="180" cy="76" r="28" />
            </svg>
        </div>
        <div class="welcome-text">Listen to both sides and you will be enlightened</div>
    </div>
</div>
<script>
var autoScroll = true;
window.addEventListener('scroll', function() {{
    var scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
    var windowHeight = window.innerHeight;
    var documentHeight = document.body.offsetHeight;
    autoScroll = (scrollPosition + windowHeight >= documentHeight - 50);
}});

function scrollToBottom() {{
    if (autoScroll) {{
        window.scrollTo(0, document.body.scrollHeight);
    }}
}}

function clearWelcome() {{
    var w = document.querySelector('.welcome');
    if (w) w.remove();
}}

function addMessage(id, role, modelKey, modelIcon, modelName, content) {{
    clearWelcome();
    var container = document.getElementById('chat-container');
    var div = document.createElement('div');
    div.id = id;
    div.className = 'message ' + role + (modelKey ? ' ' + modelKey.replace('.', '') : '');

    var userSvg = '<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg" width="18" height="18" style="vertical-align: middle;"><path d="M509.44 1018.368c-141.312 0-277.504-59.904-372.736-164.352l-19.968-21.504 19.968-21.504c95.744-104.448 231.424-164.352 372.736-164.352 141.312 0 277.504 59.904 372.736 164.352l19.968 21.504-19.968 21.504c-95.232 104.448-231.424 164.352-372.736 164.352zM204.8 832.512c81.92 77.824 190.976 121.856 304.64 121.856 113.664 0 222.72-44.032 304.64-121.856-81.92-77.824-190.976-121.856-304.64-121.856-113.664 0-222.72 44.032-304.64 121.856zM509.952 600.576c-89.088 0-161.792-72.704-161.792-161.792 0-89.088 72.704-161.792 161.792-161.792s161.792 72.704 161.792 161.792c0 89.088-72.192 161.792-161.792 161.792z m0-259.584c-53.76 0-97.792 44.032-97.792 97.792s44.032 97.792 97.792 97.792 97.792-44.032 97.792-97.792-43.52-97.792-97.792-97.792z" fill="#555555"></path><path d="M119.296 719.36c-33.792-63.488-51.2-134.144-51.2-206.848 0-243.712 198.144-441.344 441.344-441.344s441.344 198.144 441.344 441.344c0 72.192-17.92 143.36-51.2 206.336 16.384 15.36 31.744 31.744 46.08 49.152 45.568-77.312 69.12-165.376 69.12-255.488 0-279.04-226.816-505.856-505.856-505.856C230.4 7.168 4.096 233.984 4.096 512.512c0 90.112 24.064 178.688 69.632 255.488 13.824-16.896 29.184-33.28 45.568-48.64z" fill="#555555"></path></svg>';
    var header = '';
    if (role === 'user') {{
        header = '<div class="message-header"><span class="model-icon">' + userSvg + '</span><span>You</span></div>';
    }} else if (role === 'error') {{
        header = '<div class="message-header"><span class="model-icon">⚠️</span><span>错误</span></div>';
    }} else {{
        header = '<div class="message-header"><span class="model-icon">' + modelIcon + '</span><span class="model-name">' + modelName + '</span></div>';
    }}

    div.innerHTML = header + '<div class="message-content">' + escapeHtml(content) + '<span class="typing-indicator"></span></div>';
    container.appendChild(div);
    scrollToBottom();
}}

function appendChunk(id, chunk) {{
    var div = document.getElementById(id);
    if (!div) return;
    var contentEl = div.querySelector('.message-content');
    if (!contentEl) return;
    var text = contentEl.textContent;
    // 获取当前纯文本并追加
    var currentText = contentEl.getAttribute('data-raw') || '';
    currentText += chunk;
    contentEl.setAttribute('data-raw', currentText);
    contentEl.innerHTML = formatContent(currentText) + '<span class="typing-indicator"></span>';
    scrollToBottom();
}}

function finishMessage(id) {{
    var div = document.getElementById(id);
    if (!div) return;
    var contentEl = div.querySelector('.message-content');
    if (!contentEl) return;
    var indicator = contentEl.querySelector('.typing-indicator');
    if (indicator) indicator.remove();
    var rawText = contentEl.getAttribute('data-raw') || contentEl.textContent;
    contentEl.innerHTML = formatContent(rawText);
    scrollToBottom();
}}

function escapeHtml(text) {{
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}}

function formatContent(text) {{
    try {{
        if (typeof marked !== 'undefined') {{
            marked.setOptions({{ breaks: true }});
            if (typeof marked.parse === 'function') {{
                return marked.parse(text);
            }} else if (typeof marked === 'function') {{
                return marked(text);
            }}
        }}
    }} catch (e) {{
        console.error("Markdown parse error:", e);
    }}
    // 如果无 marked 则走备用极简解析
    return escapeHtml(text).replace(/\\n/g, '<br>');
}}

function clearChat() {{
    var container = document.getElementById('chat-container');
    container.innerHTML = '<div class="welcome"><div class="welcome-icon"><svg viewBox="0 0 256 256" stroke="currentColor" stroke-width="8" fill="none" xmlns="http://www.w3.org/2000/svg"><defs><mask id="brain-cutout"><rect width="256" height="256" fill="white" stroke="none" /><circle cx="180" cy="76" r="32" fill="black" stroke="none" /></mask></defs><circle cx="124" cy="132" r="76" mask="url(#brain-cutout)" /><circle cx="180" cy="76" r="28" /></svg></div><div class="welcome-text">Listen to both sides and you will be enlightened</div></div>';
    scrollToBottom();
}}

function setUserMessage(id, content, attachmentsJson) {{
    clearWelcome();
    var container = document.getElementById('chat-container');
    var div = document.createElement('div');
    div.id = id;
    div.className = 'message user';
    var userSvg = '<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg" width="18" height="18" style="vertical-align: middle;"><path d="M509.44 1018.368c-141.312 0-277.504-59.904-372.736-164.352l-19.968-21.504 19.968-21.504c95.744-104.448 231.424-164.352 372.736-164.352 141.312 0 277.504 59.904 372.736 164.352l19.968 21.504-19.968 21.504c-95.232 104.448-231.424 164.352-372.736 164.352zM204.8 832.512c81.92 77.824 190.976 121.856 304.64 121.856 113.664 0 222.72-44.032 304.64-121.856-81.92-77.824-190.976-121.856-304.64-121.856-113.664 0-222.72 44.032-304.64 121.856zM509.952 600.576c-89.088 0-161.792-72.704-161.792-161.792 0-89.088 72.704-161.792 161.792-161.792s161.792 72.704 161.792 161.792c0 89.088-72.192 161.792-161.792 161.792z m0-259.584c-53.76 0-97.792 44.032-97.792 97.792s44.032 97.792 97.792 97.792 97.792-44.032 97.792-97.792-43.52-97.792-97.792-97.792z" fill="#555555"></path><path d="M119.296 719.36c-33.792-63.488-51.2-134.144-51.2-206.848 0-243.712 198.144-441.344 441.344-441.344s441.344 198.144 441.344 441.344c0 72.192-17.92 143.36-51.2 206.336 16.384 15.36 31.744 31.744 46.08 49.152 45.568-77.312 69.12-165.376 69.12-255.488 0-279.04-226.816-505.856-505.856-505.856C230.4 7.168 4.096 233.984 4.096 512.512c0 90.112 24.064 178.688 69.632 255.488 13.824-16.896 29.184-33.28 45.568-48.64z" fill="#555555"></path></svg>';
    
    var attachHtml = "";
    if (attachmentsJson) {{
        try {{
            var attachments = JSON.parse(attachmentsJson);
            if (attachments && attachments.length > 0) {{
                attachHtml += '<div style="margin-bottom: 8px; display: flex; flex-wrap: wrap; gap: 8px;">';
                attachments.forEach(function(a) {{
                    attachHtml += '<div style="padding: 8px 12px; background: #f1f5f9; border-radius: 6px; font-size: 13px; color: #475569; border: 1px solid #cbd5e1; display: inline-flex; align-items: center; gap: 6px;"><span style="font-size: 16px;">📄</span>' + escapeHtml(a.file_name) + '</div>';
                }});
                attachHtml += '</div>';
            }}
        }} catch(e) {{
            console.error("Failed to parse attachments", e);
        }}
    }}

    div.innerHTML = '<div class="message-header"><span class="model-icon">' + userSvg + '</span><span>You</span></div>' +
                    '<div class="message-content">' + attachHtml + escapeHtml(content) + '</div>';
    container.appendChild(div);
    scrollToBottom();
}}
</script>
</body>
</html>"""
        self.web_view.setHtml(html)

    def clear_chat(self):
        """清空聊天内容，显示欢迎信息"""
        self.web_view.page().runJavaScript("clearChat();")
        self._message_ids.clear()
        self._msg_counter = 0

    def add_user_message(self, content: str, attachments: list = None):
        """添加用户消息"""
        self._msg_counter += 1
        msg_id = f"msg_{self._msg_counter}"
        escaped = content.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
        
        import json
        if attachments:
            # 根据对象类型进行处理，如果是字典(从历史中恢复)，或者是 FileAttachment 对象(直接发送)
            attach_dicts = [a.to_dict() if hasattr(a, 'to_dict') else a for a in attachments]
            attachments_json = json.dumps(attach_dicts).replace("\\", "\\\\").replace("'", "\\'")
            self.web_view.page().runJavaScript(f"setUserMessage('{msg_id}', '{escaped}', '{attachments_json}');")
        else:
            self.web_view.page().runJavaScript(f"setUserMessage('{msg_id}', '{escaped}', '');")

    def start_assistant_message(self, model_key: str, model_name: str):
        """开始一个新的 assistant 流式消息"""
        self._msg_counter += 1
        msg_id = f"msg_{self._msg_counter}"
        self._message_ids[model_key] = msg_id
        icon = MODEL_ICONS.get(model_key, "🤖")
        escaped_name = model_name.replace("'", "\\'")
        self.web_view.page().runJavaScript(
            f"addMessage('{msg_id}', 'assistant', '{model_key}', '{icon}', '{escaped_name}', '');"
        )
        return msg_id

    def append_chunk(self, model_key: str, chunk: str):
        """追加流式文本块"""
        msg_id = self._message_ids.get(model_key)
        if not msg_id:
            return
        escaped = chunk.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "")
        self.web_view.page().runJavaScript(f"appendChunk('{msg_id}', '{escaped}');")

    def finish_message(self, model_key: str):
        """完成某个模型的流式消息"""
        msg_id = self._message_ids.get(model_key)
        if msg_id:
            self.web_view.page().runJavaScript(f"finishMessage('{msg_id}');")

    def add_error_message(self, model_key: str, error: str):
        """显示错误消息"""
        self._msg_counter += 1
        msg_id = f"msg_{self._msg_counter}"
        escaped = error.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
        self.web_view.page().runJavaScript(
            f"addMessage('{msg_id}', 'error', '{model_key}', '⚠️', '错误', '{escaped}');"
        )

    def load_history_messages(self, messages: list):
        """加载历史消息（非流式，直接显示）"""
        self.clear_chat()
        for msg in messages:
            if msg.role == "user":
                self.add_user_message(msg.content, getattr(msg, 'attachments_meta', None))
            elif msg.role == "assistant":
                model_key = msg.model_key or "unknown"
                model_name = msg.model_name or model_key
                self._msg_counter += 1
                msg_id = f"msg_{self._msg_counter}"
                icon = MODEL_ICONS.get(model_key, "🤖")
                escaped_name = model_name.replace("'", "\\'")
                escaped_content = msg.content.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "")
                self.web_view.page().runJavaScript(
                    f"addMessage('{msg_id}', 'assistant', '{model_key}', '{icon}', '{escaped_name}', '{escaped_content}');"
                )
                self.web_view.page().runJavaScript(f"finishMessage('{msg_id}');")
