# -*- coding: utf-8 -*-
"""
设置弹窗 — 管理 API Key、上下文数量和模型启用/禁用。
使用分区卡片式布局，与整体极简白色主题保持一致。
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QSpinBox, QCheckBox, QPushButton,
    QFrame, QWidget, QGridLayout
)
from PyQt5.QtCore import Qt
from ui.styles import SETTINGS_DIALOG_STYLE
from core.model_manager import ModelManager, MODEL_ICONS


class SettingsDialog(QDialog):
    """设置弹窗"""

    def __init__(self, model_manager: ModelManager, parent=None):
        super().__init__(parent)
        self.model_manager = model_manager
        self.setWindowTitle("Settings")
        self.setFixedSize(520, 600)
        self.setStyleSheet(SETTINGS_DIALOG_STYLE)
        self._checkboxes = {}
        self._init_ui()
        self._load_values()

    def _create_section_title(self, text: str) -> QLabel:
        """创建分区标题"""
        label = QLabel(text)
        label.setObjectName("sectionTitle")
        return label

    def _create_section_card(self) -> QFrame:
        """创建分区卡片容器"""
        card = QFrame()
        card.setObjectName("sectionCard")
        return card

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        # 标题
        title = QLabel("Settings")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        # ────────────── API 设置 ──────────────
        layout.addWidget(self._create_section_title("API 设置"))

        api_card = self._create_section_card()
        api_grid = QGridLayout(api_card)
        api_grid.setContentsMargins(16, 14, 16, 14)
        api_grid.setHorizontalSpacing(12)
        api_grid.setVerticalSpacing(10)

        api_label = QLabel("API Key")
        api_label.setFixedWidth(90)
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("sk-xxxxxxxxxxxxxxxx")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        api_grid.addWidget(api_label, 0, 0)
        api_grid.addWidget(self.api_key_input, 0, 1)

        layout.addWidget(api_card)

        # ────────────── 上下文策略 ──────────────
        layout.addWidget(self._create_section_title("上下文策略"))

        ctx_card = self._create_section_card()
        ctx_grid = QGridLayout(ctx_card)
        ctx_grid.setContentsMargins(16, 14, 16, 14)
        ctx_grid.setHorizontalSpacing(12)
        ctx_grid.setVerticalSpacing(10)

        token_label = QLabel("Token 限制")
        token_label.setFixedWidth(90)
        self.token_limit_spin = QSpinBox()
        self.token_limit_spin.setRange(500, 8000)
        self.token_limit_spin.setSingleStep(500)
        self.token_limit_spin.setSuffix(" Tokens")
        ctx_grid.addWidget(token_label, 0, 0)
        ctx_grid.addWidget(self.token_limit_spin, 0, 1)

        self.enable_summary_cb = QCheckBox("智能摘要")
        self.enable_summary_cb.setToolTip("超出 Token 限制时自动生成摘要")
        ctx_grid.addWidget(self.enable_summary_cb, 1, 0)

        self.summary_model_input = QLineEdit()
        self.summary_model_input.setPlaceholderText("摘要模型，如 qwen-plus")
        ctx_grid.addWidget(self.summary_model_input, 1, 1)

        layout.addWidget(ctx_card)

        # ────────────── 模型管理 ──────────────
        layout.addWidget(self._create_section_title("模型管理"))

        model_card = self._create_section_card()
        model_grid = QGridLayout(model_card)
        model_grid.setContentsMargins(16, 12, 16, 12)
        model_grid.setHorizontalSpacing(8)
        model_grid.setVerticalSpacing(8)

        # 列宽：图标 | 名称 | 模型ID | 开关
        model_grid.setColumnMinimumWidth(0, 24)   # 图标列
        model_grid.setColumnMinimumWidth(1, 80)   # 名称列
        model_grid.setColumnStretch(2, 1)         # ID列拉伸
        model_grid.setColumnMinimumWidth(3, 44)   # 开关列

        all_models = self.model_manager.get_all_models()
        for row, (key, config) in enumerate(all_models.items()):
            # 彩色圆点
            icon_text = MODEL_ICONS.get(key, "🤖")
            icon_label = QLabel(icon_text)
            icon_label.setFixedWidth(24)
            icon_label.setStyleSheet("font-size: 12px;")
            icon_label.setAlignment(Qt.AlignCenter)
            model_grid.addWidget(icon_label, row, 0)

            # 模型名称
            name_label = QLabel(config.display_name)
            name_label.setStyleSheet("font-size: 13px; font-weight: 500; color: #222;")
            name_label.setFixedWidth(80)
            model_grid.addWidget(name_label, row, 1)

            # 模型 ID
            id_label = QLabel(config.model_id)
            id_label.setStyleSheet("font-size: 12px; color: #aaa;")
            model_grid.addWidget(id_label, row, 2)

            # 开关 toggle
            cb = QCheckBox()
            cb.setObjectName("modelToggle")
            cb.setFixedWidth(40)
            self._checkboxes[key] = cb
            model_grid.addWidget(cb, row, 3, Qt.AlignRight)

        layout.addWidget(model_card)

        # ────────────── 按钮行 ──────────────
        layout.addStretch()
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        btn_row.addSpacing(8)

        save_btn = QPushButton("保存")
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _load_values(self):
        """从 ModelManager 加载当前设置"""
        self.api_key_input.setText(self.model_manager.api_key)
        self.token_limit_spin.setValue(self.model_manager.max_token_limit)
        self.enable_summary_cb.setChecked(self.model_manager.enable_summary)
        self.summary_model_input.setText(self.model_manager.summary_model)
        all_models = self.model_manager.get_all_models()
        for key, config in all_models.items():
            if key in self._checkboxes:
                self._checkboxes[key].setChecked(config.enabled)

    def _save(self):
        """保存设置"""
        self.model_manager.api_key = self.api_key_input.text().strip()
        self.model_manager.max_token_limit = self.token_limit_spin.value()
        self.model_manager.enable_summary = self.enable_summary_cb.isChecked()
        self.model_manager.summary_model = self.summary_model_input.text().strip()
        for key, cb in self._checkboxes.items():
            self.model_manager.set_model_enabled(key, cb.isChecked())
        self.model_manager.save_settings()
        self.accept()
