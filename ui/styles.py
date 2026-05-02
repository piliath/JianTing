# -*- coding: utf-8 -*-
"""
全局 QSS 样式定义 — 参考 Ollama 极简白色主题。
"""

# 主窗口背景
MAIN_WINDOW_STYLE = """
QMainWindow {
    background-color: #ffffff;
}
"""

# 侧边栏
SIDEBAR_STYLE = """
QWidget#sidebar {
    background-color: #f9f9f9;
    border-right: 1px solid #e5e5e5;
}

QPushButton#newChatBtn, QPushButton#settingsBtn {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 10px 12px;
    text-align: left;
    font-size: 15px;
    font-weight: 500;
    color: #111111;
}

QPushButton#newChatBtn:hover, QPushButton#settingsBtn:hover {
    background-color: #eaeaea;
}

QListWidget#historyList {
    background-color: transparent;
    border: none;
    font-size: 14px;
    color: #444444;
    outline: none;
}

QListWidget#historyList::item {
    padding: 8px 12px;
    border-radius: 6px;
    margin: 2px 4px;
}

QListWidget#historyList::item:hover {
    background-color: #eaeaea;
}

QListWidget#historyList::item:selected {
    background-color: #e0e0e0;
    color: #000000;
    font-weight: 500;
}

QLabel#historyLabel {
    font-size: 13px;
    font-weight: 600;
    color: #888888;
    padding: 16px 12px 6px 12px;
}

QMenu {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 20px;
    border-radius: 4px;
    color: #444444;
    font-size: 14px;
}

QMenu::item:selected {
    background-color: #ffebee; /* 柔和的浅红色背景提示删除操作 */
    color: #d32f2f;
}
"""

# 输入区域
INPUT_AREA_STYLE = """
QWidget#inputArea {
    background-color: #ffffff;
}

QFrame#inputContainer {
    background-color: #f7f7f7;
    border: 1px solid #e5e5e5;
    border-radius: 20px;
}

QTextEdit#inputBox {
    font-family: "HarmonyOS Sans SC", "HarmonyOS Sans", "Microsoft YaHei", sans-serif;
    background-color: transparent;
    border: none;
    padding: 8px 10px;
    font-size: 15px;
    color: #111111;
    selection-background-color: #b3d7ff;
}

QPushButton#modelBtn {
    background-color: transparent;
    border: none;
    border-radius: 16px;
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
    margin-left: 4px;
    margin-bottom: 4px;
}

QPushButton#modelBtn:hover {
    background-color: #eaeaea;
}

QPushButton#modelBtn::menu-indicator {
    image: none;
}

QPushButton#sendBtn {
    background-color: #d8e1f8;  /* 低饱和度 (无输入) */
    color: #ffffff;
    border: none;
    border-radius: 16px;
    font-size: 16px;
    font-weight: bold;
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
    margin-right: 4px;
    margin-bottom: 4px;
}

QPushButton#sendBtn[has_text="true"] {
    background-color: #567cff;  /* 高饱和度亮蓝 (有输入) */
}

QPushButton#sendBtn[has_text="true"]:hover {
    background-color: #3b66fb;
}

QPushButton#sendBtn[has_text="false"]:hover {
    background-color: #c2cff2;
}

QPushButton#sendBtn:disabled {
    background-color: #e0e0e0;
}
"""

# 设置弹窗
SETTINGS_DIALOG_STYLE = """
QDialog {
    background-color: #ffffff;
}

QLabel {
    font-size: 13px;
    color: #444444;
}

QLabel#sectionTitle {
    font-size: 13px;
    font-weight: 600;
    color: #888888;
    padding: 0;
    margin: 0;
}

QLabel#dialogTitle {
    font-size: 18px;
    font-weight: 700;
    color: #111111;
}

QFrame#sectionCard {
    background-color: #f9f9f9;
    border: 1px solid #eeeeee;
    border-radius: 12px;
}

QLineEdit {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 7px 12px;
    font-size: 13px;
    color: #333333;
}

QLineEdit:focus {
    border: 1px solid #aaaaaa;
}

QSpinBox {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 7px 12px;
    font-size: 13px;
    color: #333333;
}

QSpinBox:focus {
    border: 1px solid #aaaaaa;
}

QCheckBox {
    font-size: 13px;
    color: #555555;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #cccccc;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #111111;
    border-color: #111111;
}

QCheckBox#modelToggle {
    font-size: 13px;
    color: #333333;
    spacing: 10px;
}

QCheckBox#modelToggle::indicator {
    width: 32px;
    height: 18px;
    border-radius: 9px;
    border: none;
    background-color: #d0d0d0;
}

QCheckBox#modelToggle::indicator:checked {
    background-color: #111111;
}

QPushButton#saveBtn {
    background-color: #111111;
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 10px 28px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton#saveBtn:hover {
    background-color: #333333;
}

QPushButton#cancelBtn {
    background-color: #f4f4f4;
    color: #444444;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 10px 28px;
    font-size: 13px;
}

QPushButton#cancelBtn:hover {
    background-color: #e8e8e8;
}
"""

# 模型选择弹出菜单（手动选择和 @ 触发共用同一组件样式）
AT_MENU_STYLE = """
QListWidget#atMenu {
    background-color: #ffffff;
    border: 1px solid #e5e5e5;
    border-radius: 12px;
    font-size: 14px;
    color: #333333;
    padding: 6px;
    outline: none;
}

QListWidget#atMenu::item {
    padding: 7px 14px;
    border-radius: 8px;
    margin: 1px 2px;
}

QListWidget#atMenu::item:hover {
    background-color: #f5f5f5;
}

QListWidget#atMenu::item:selected {
    background-color: #f0f0f0;
}
"""

# 聊天区域的 HTML/CSS 主题（注入到 QWebEngineView 中）
CHAT_HTML_CSS = """
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: "HarmonyOS_Regular", "HarmonyOS Sans SC", "HarmonyOS Sans", -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    background-color: #ffffff;
    color: #111111;
    line-height: 1.6;
    padding: 20px 10%;
    margin: 0;
    overflow-x: hidden;
}

.welcome {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 70vh;
    color: #999999;
}

.welcome-icon svg {
    width: 64px;
    height: 64px;
    stroke: #cccccc;
    margin-bottom: 24px;
}

.welcome-text {
    font-size: 24px;
    font-weight: 400;
    letter-spacing: 1px;
    color: #888888;
}

.message {
    position: relative;
    max-width: 900px;
    margin: 0 auto 32px auto;
    padding: 0;
    animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

.message.user {
    background-color: #f4f4f4;
    padding: 24px 32px;
    border-radius: 20px;
    max-width: 80%;
    margin-left: auto;
    margin-right: 0;
}

.message.user .message-header {
    justify-content: flex-start;
}

.message.assistant {
    background-color: #f9f9f9;
    padding: 24px 32px;
    border-radius: 20px;
    margin-left: 0;
}

.message.error {
    background-color: #fff5f5;
    border: 1px solid #fed7d7;
    color: #c53030;
    padding: 16px 20px;
    border-radius: 16px;
}

.message-header {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 8px;
    font-size: 13px;
    font-weight: 600;
    color: #555555;
}

.message.assistant .message-header {
    position: sticky;
    top: 12px;
    z-index: 10;
    background-color: rgba(255, 255, 255, 0.65);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    display: inline-flex;
    padding: 4px 10px;
    border-radius: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
    border: 1px solid rgba(0, 0, 0, 0.05);
    margin-left: -10px;
}

.model-icon {
    font-size: 13px;
}

.model-name {
    text-transform: capitalize;
    font-size: 12px;
    font-weight: 500;
    color: #666666;
}

.message-content {
    font-size: 15px;
    line-height: 1.7;
    word-wrap: break-word;
}

.message-content p {
    margin-bottom: 0.8em;
}

.message-content p:last-child {
    margin-bottom: 0;
}

.message-content code {
    background-color: #f0f0f0;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 13px;
}

.message-content pre {
    background-color: #1e1e1e;
    color: #d4d4d4;
    padding: 16px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 12px 0;
}

.message-content pre code {
    background-color: transparent;
    padding: 0;
    color: inherit;
    font-size: 13px;
}

.typing-indicator {
    display: inline-block;
    width: 6px;
    height: 16px;
    background-color: #333;
    animation: blink 0.8s infinite;
    margin-left: 2px;
    vertical-align: text-bottom;
    border-radius: 1px;
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
}

.divider {
    max-width: 800px;
    margin: 8px auto;
    border: none;
    border-top: 1px solid #f0f0f0;
}
"""
