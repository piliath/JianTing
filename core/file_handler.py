# -*- coding: utf-8 -*-
"""
文件处理器 — 提供对用户上传文档的支持。
支持：TXT/MD/PDF/DOCX/XLSX/CSV
使用鸭子类型和延迟导入避免强制依赖。
"""

import os
from dataclasses import dataclass
from typing import Optional

try:
    from PyPDF2 import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


@dataclass
class FileAttachment:
    file_name: str
    file_type: str  # "text"
    content: str    # 提取的文本内容
    mime_type: str  # e.g., "text/plain"
    file_size: int

    def to_dict(self):
        """用于保存到持久化。注意这里不保存内容，避免 json 过大"""
        return {
            "file_name": self.file_name,
            "file_type": self.file_type,
            "mime_type": self.mime_type,
            "file_size": self.file_size
        }


class FileHandler:
    SUPPORTED_TEXT = {'.txt', '.md', '.pdf', '.docx', '.xlsx', '.csv'}
    
    # 限制文本文件的字符数，太大会撑爆 openai API 且超过我们的 limit
    MAX_TEXT_CHARS = 10000 

    @staticmethod
    def process_file(filepath: str) -> Optional[FileAttachment]:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")

        ext = os.path.splitext(filepath)[1].lower()
        file_size = os.path.getsize(filepath)
        filename = os.path.basename(filepath)

        if ext in FileHandler.SUPPORTED_TEXT:
            content = FileHandler._read_text_document(filepath, ext)
            return FileAttachment(
                file_name=filename,
                file_type="text",
                content=content,
                mime_type="text/plain",
                file_size=file_size
            )
        else:
            raise ValueError(f"不支持的文件格式: {ext}\n支持的格式: {', '.join(FileHandler.SUPPORTED_TEXT)}")

    @staticmethod
    def _read_text_document(filepath: str, ext: str) -> str:
        content = ""
        if ext in {'.txt', '.md'}:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        elif ext == '.pdf':
            if not HAS_PYPDF:
                raise ImportError("处理 PDF 需要安装 PyPDF2: pip install PyPDF2")
            reader = PdfReader(filepath)
            for page in reader.pages:
                content += page.extract_text() + "\n"
        elif ext == '.docx':
            if not HAS_DOCX:
                raise ImportError("处理 DOCX 需要安装 python-docx: pip install python-docx")
            doc = docx.Document(filepath)
            content = "\n".join([p.text for p in doc.paragraphs])
        elif ext == '.xlsx':
            content = FileHandler._read_xlsx(filepath)
        elif ext == '.csv':
            content = FileHandler._read_csv(filepath)
            
        if len(content) > FileHandler.MAX_TEXT_CHARS:
            content = content[:FileHandler.MAX_TEXT_CHARS] + "\n...[文件过大已截断]"
            
        return content

    @staticmethod
    def _read_xlsx(filepath: str) -> str:
        """读取 Excel 文件，将每个工作表转为纯文本表格"""
        if not HAS_OPENPYXL:
            raise ImportError("处理 XLSX 需要安装 openpyxl: pip install openpyxl")
        
        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        parts = []
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            rows = []
            for row in ws.iter_rows(values_only=True):
                # 将每个单元格转为字符串，None 转为空
                cells = [str(c) if c is not None else "" for c in row]
                rows.append("\t".join(cells))
            if rows:
                parts.append(f"[工作表: {sheet_name}]\n" + "\n".join(rows))
        wb.close()
        return "\n\n".join(parts)

    @staticmethod
    def _read_csv(filepath: str) -> str:
        """读取 CSV 文件为纯文本"""
        import csv
        rows = []
        # 先尝试 utf-8，失败则 gbk
        for encoding in ('utf-8', 'gbk', 'latin-1'):
            try:
                with open(filepath, 'r', encoding=encoding, newline='') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        rows.append("\t".join(row))
                break
            except (UnicodeDecodeError, UnicodeError):
                rows.clear()
                continue
        return "\n".join(rows)
