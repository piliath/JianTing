# JianTing (兼听) AI Client

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

**English** | **[简体中文](README.md)**

> **"Listen to both sides and you will be enlightened" (兼听则明)** — This is the design philosophy of **JianTing**.
> It is a cross-platform, **multi-model concurrent intelligent chat client** built with PyQt5. Breaking the limits of traditional single-point AI clients, JianTing allows you to simultaneously hear the voices of multiple artificial intelligences.

![JianTing Screenshot](JianTing.png)

---

## 🎯 The Problems We Solve

Common AI clients in the market suffer from several pain points, which JianTing resolves systematically:

1. **Single-Model Hallucinations**: A single model can confidently generate completely fabricated information.
   - **JianTing's Solution**: Introduces concurrent multi-model responses. By putting top-tier models like DeepSeek, Qwen, Kimi, and GLM on the same stage, you can compare multiple answers side-by-side to easily spot hallucinations.
2. **Context Pollution from Large Documents**: Uploading a massive document usually forces the AI to abruptly truncate memory or summarize your original prompt into a system message, leading to a disastrous multi-turn chat experience.
   - **JianTing's Solution**: An exclusive **"Single-Turn Temporary Concatenation" strategy**. Massive documents are injected purely as background knowledge for a single inference step without polluting the global LangChain Memory, keeping long-term conversations perfectly on track.
3. **UI Freezes During History Switching**: As context grows, calculating tokens or generating summaries can cause the app to freeze for several seconds.
   - **JianTing's Solution**: A fully asynchronous, **anti-freeze memory manager**. It uses background threading to take over all LangChain summarization (`prune`) calculations and file I/O operations, ensuring buttery-smooth typing and UI switching at all times.

---

## ✨ Core Highlights

- 🌟 **Pioneering "Model Cross-Review" Engine**: It doesn't just chat concurrently; it allows models to engage in cross-temporal debates. Using precise identity context tags, you can ask DeepSeek to read and directly critique what Qwen said a second ago.
- 🎨 **Strict Minimalist Aesthetics**: Features the HarmonyOS Sans font, finely-tuned dynamic shadows, rounded corners, and hover states. We rejected basic OS default components (including right-click menus) to create a highly immersive, modern interactive experience.
- ⚡ **Seamless Multi-Modal Parsing**: Local, lightning-fast parsing for TXT, PDF, Word (`.docx`), Excel (`.xlsx`), and CSV files. Upload easily via drag-and-drop or visual buttons.
- 🔧 **Highly Engineered Architecture**: Connects seamlessly via an OpenAI-compatible format (defaulted to Alibaba Cloud's DashScope), making it incredibly easy to plug in any new LLM.

---

## ⌨️ Command Syntax & Usage

JianTing is entirely driven by a highly flexible `@` command system. **All commands must start with an `@` at the very beginning of the sentence** to orchestrate the models:

1. **Single Model Query**
   - Syntax: `@ModelName [Your prompt]`
   - Example: `@DeepSeek Help me write a Python script`
   - *Result: Only DeepSeek is summoned to answer the prompt.*

2. **Concurrent Query**
   - Syntax: `@ModelA @ModelB [Your prompt]`
   - Example: `@Qwen @MiniMax Compare the pros and cons of React and Vue`
   - *Result: Both Qwen and MiniMax will concurrently generate their perspectives in their respective chat bubbles.*

3. **Broadcast to All**
   - Syntax: `@ALL [Your prompt]`
   - Example: `@ALL Tell me a joke`
   - *Result: Instantly triggers all enabled models to reply.*

4. **Advanced Usage: Cross-Model Commenting (Review)**
   - Syntax: Place the designated answering model at the start, and mention the target model in the body text.
   - Example: `@DeepSeek please comment on @Qwen's answer`
   - *Result: The system strictly extracts the leading `@DeepSeek` as the command, and securely passes the exact text `please comment on @Qwen's answer` to DeepSeek. Thanks to the built-in identity memory tags, DeepSeek will accurately find Qwen's previous statement and provide a targeted critique.*

> **Tip**: If no `@` command is included at the start of your message, the system defaults to sending the prompt to the model currently selected in the dropdown menu left of the input box.

---

## 📦 Requirements

Running this project requires Python 3.10+. Please ensure the following dependencies are installed:

```text
# Core UI and Browser Engine
PyQt5>=5.15.0
PyQtWebEngine>=5.15.0

# Core AI Framework and Network
openai>=1.0.0
langchain>=0.1.0
tiktoken>=0.5.0
requests>=2.28.0

# Local Document Parsing Engines
PyMuPDF>=1.23.0    # Used instead of basic fitz for lightning-fast PDF parsing
python-docx>=1.1.0 # For parsing Word documents
pandas>=2.0.0      # For parsing CSV tables
openpyxl>=3.1.0    # For parsing Excel workbooks
```

**Installation Command:**
```bash
pip install PyQt5 PyQtWebEngine openai langchain tiktoken requests PyMuPDF python-docx pandas openpyxl
```

*(Running on Windows is recommended to get the best UI rendering compatibility and window shadow effects.)*

---

## 🚀 Quick Start

1. Clone this repository.
2. Install the `Requirements` listed above.
3. Run `python main.py`.
4. Upon the first launch, click the **⚙️ Settings** button in the bottom left corner, enter your API Key (defaults to Alibaba DashScope), and start your JianTing journey!
