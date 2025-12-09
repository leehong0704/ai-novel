# AI小说生成器

一个基于Python的AI小说创作工具，利用人工智能技术自动生成小说内容。  
📦 便捷下载：[`ai-novel.zip`](release/ai-novel.zip)（打包好的 Windows 发行版）

## 项目简介

本项目旨在通过AI技术辅助或自动生成小说内容，帮助创作者快速生成小说章节、情节发展等内容。项目支持多种AI模型，可以生成不同风格和类型的小说。

## 功能特性

- 🤖 **AI驱动创作**：使用先进的AI模型生成高质量小说内容
- 🔧 **多API配置管理**：支持配置多个AI接口，一键切换（DeepSeek、OpenAI、Gemini等）
- 📚 **多类型支持**：支持多种小说类型（玄幻、都市、科幻等）
- 📝 **章节管理**：支持章节划分和管理
- 🎨 **风格定制**：可自定义写作风格和语言特点
- 💾 **内容保存**：自动保存生成的小说内容
- 🔄 **续写功能**：支持基于已有内容继续创作


## 技术栈

- Python 3.7+
- Tkinter - Windows桌面GUI框架（Python内置）
- DeepSeek API - AI模型接口（已集成）
- Requests - HTTP请求库
- 其他依赖库（详见requirements.txt）

## 安装说明

### 环境要求

- Python 3.7+

### 安装步骤

1. 克隆项目到本地
```bash
git clone <项目地址>
cd 小说AI
```

2. 创建虚拟环境（推荐）
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置API密钥

   **方式1：通过UI界面配置（推荐）**
   - 运行程序后，进入"🤖 AI设置"页面
   - 左侧显示所有API配置列表
   - 点击"➕ 新建"添加新的API配置
   - 在右侧编辑API详细信息（API地址、模型、密钥等）
   - 点击"💾 保存当前配置"
   - 使用"✓ 设为当前"切换使用的API

   **方式2：手动编辑配置文件**
   - 复制 `config/config.ini.example` 为 `config/config.ini`
   - 编辑配置文件，添加您的API配置：
     ```ini
     [APP]
     current_api = DEEPSEEK  # 当前使用的API名称

     [DEEPSEEK]
     api_key = sk-xxx...
     api_base = https://api.deepseek.com/v1
     model = deepseek-chat

     [OPENAI]
     api_key = sk-xxx...
     api_base = https://api.openai.com/v1
     model = gpt-4
     ```
   - 可以配置多个API，通过修改 `current_api` 切换使用

   **详细文档**：查看 `docs/多API配置说明.md` 或 `多API配置-快速开始.md`


## 使用方法

### 启动主界面

1. 确保已安装所有依赖
2. 运行主程序：
```bash
python main.py
```

3. 程序会打开Windows桌面窗口，显示主界面

### 界面功能说明（多标签页）

- 🤖 **AI设置**：
  - **左侧**：API配置列表，显示所有已配置的API接口
  - **右侧**：API配置详情，编辑选中API的详细信息
  - **功能**：添加、删除、切换API配置，调整Temperature、Max Tokens参数
  - **特点**：支持多个API配置，一键切换，实时生效
  
- 📖 **小说设置**：填写标题、类型、写作风格、主题；创建/读取/保存 `novel.ini`

- 🧩 **小说设定**：维护"小说设置列表/人物设定列表"，内容与勾选状态持久化到 `novel.ini`

- ✍️ **章节生成**：输入提示生成内容，右侧显示生成文本与字数统计，可保存/清空


### 使用步骤

1. 在"小说标题"输入框中输入小说标题
2. 选择小说类型和写作风格
3. 调整AI参数（创造性、最大长度）
4. 在"创作提示"区域输入你的创作想法
5. 点击"🚀 生成内容"按钮
6. 生成的内容会显示在右侧，可以继续编辑
7. 点击"💾 保存小说"将内容保存到output目录

## 项目结构

```
小说AI/
├── main.py                 # 主程序入口（Tkinter 桌面应用）
├── UI/                     # 界面模块
│   ├── ai_settings.py      # AI 设置页面
│   ├── novel_settings.py   # 小说设置页面
│   └── novel_profile.py    # 小说设定页面（设定/人物管理）
├── config/
│   ├── config.ini          # 运行时配置（应用内可保存，优先读取）
│   └── config.ini.example  # 配置示例
├── output/                 # 输出目录（运行时创建）
└── README.md               # 项目说明文档
```

## 开发计划

- [x] 基础框架搭建
- [x] 用户界面开发（Windows Form桌面应用）
- [x] 内容保存和导出
- [x] AI模型集成（DeepSeek API）
- [x] 小说生成功能实现
- [x] 章节管理功能
- [x] 配置文件管理
- [x] 内容编辑功能
- [x] **多API配置管理**（支持配置多个AI接口，一键切换）
- [ ] 流式输出（实时显示生成内容）
- [ ] 批量生成功能
- [ ] 导出为多种格式（Word、PDF等）
- [ ] 打包为可执行文件（.exe）


## 贡献指南

欢迎提交Issue和Pull Request来帮助改进项目。

## 许可证

（待补充）

## 联系方式

（待补充）

