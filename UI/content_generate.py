"""
正文生成页面
负责显示和编辑选定章节的正文内容，并提供AI生成与内容修改功能
"""

import tkinter as tk
from tkinter import ttk, scrolledtext

def create_content_generate_page(app, parent):
    """创建正文生成页面"""
    # 左侧：章节管理
    left_panel = tk.Frame(parent)
    left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
    
    chapters_mgmt = ttk.LabelFrame(left_panel, text="📑 章节列表", padding=10)
    chapters_mgmt.pack(fill=tk.BOTH, expand=True)

    list_container = tk.Frame(chapters_mgmt)
    list_container.pack(fill=tk.BOTH, expand=True)
    
    scrollbar = tk.Scrollbar(list_container, orient=tk.VERTICAL)
    app.content_chapter_listbox = tk.Listbox(
        list_container,
        height=20,
        font=("Microsoft YaHei", 10),
        yscrollcommand=scrollbar.set,
        selectmode=tk.SINGLE,
        exportselection=False
    )
    app.content_chapter_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=app.content_chapter_listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # 同步逻辑
    def on_select(event):
        app.on_chapter_selected(event, source="content")

    app.content_chapter_listbox.bind("<<ListboxSelect>>", on_select)

    # 右侧：生成区域
    right_panel = tk.Frame(parent)
    right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

    # ========== 正文编辑器 ==========
    output_frame = ttk.LabelFrame(right_panel, text="📖 正文内容", padding=15)
    output_frame.pack(fill=tk.BOTH, expand=True)
    
    # 正文文本框 (删除了上方的章节标题显示标签)
    app.content_page_title = tk.Label(output_frame) # 保持变量存在以防报错，但不渲染
    app.content_text = scrolledtext.ScrolledText(
        output_frame,
        font=("Microsoft YaHei", 11),
        wrap=tk.WORD,
        undo=True
    )
    app.content_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    app.content_text.bind("<KeyRelease>", app.update_word_count)

    # ========== 修改提示词区域 ==========
    modify_frame = tk.Frame(right_panel)
    modify_frame.pack(fill=tk.X, pady=(5, 5))
    
    tk.Label(modify_frame, text="✨ 修改要求：", font=("Microsoft YaHei", 10, "bold")).pack(side=tk.TOP, anchor=tk.W)
    app.modify_instruction_entry = tk.Text(
        modify_frame, 
        height=3,
        font=("Microsoft YaHei", 10),
        fg="#666666",
        padx=5,
        pady=5
    )
    app.modify_instruction_entry.pack(side=tk.TOP, fill=tk.X, expand=True, pady=5)
    
    placeholder_text = "输入整体修改意见，或直接描述如何改进当前章节内容（如：增加心理描写、精简开场等）..."
    app.modify_instruction_entry.insert("1.0", placeholder_text)
    
    # 占位符提示效果
    def on_entry_click(event):
        content = app.modify_instruction_entry.get("1.0", tk.END).strip()
        if content == placeholder_text:
            app.modify_instruction_entry.delete("1.0", tk.END)
            app.modify_instruction_entry.config(fg='black')

    def on_focusout(event):
        content = app.modify_instruction_entry.get("1.0", tk.END).strip()
        if content == '':
            app.modify_instruction_entry.delete("1.0", tk.END)
            app.modify_instruction_entry.insert("1.0", placeholder_text)
            app.modify_instruction_entry.config(fg='#666666')

    app.modify_instruction_entry.bind('<FocusIn>', on_entry_click)
    app.modify_instruction_entry.bind('<FocusOut>', on_focusout)

    # 底部按钮区域
    btns_frame = tk.Frame(right_panel)
    btns_frame.pack(fill=tk.X, pady=(5, 0))
    
    # 1. 生成按钮
    app.generate_btn = tk.Button(
        btns_frame,
        text="🚀 开始 AI 生成",
        command=app.generate_content,
        font=("Microsoft YaHei", 10, "bold"),
        bg="#1f77b4",
        fg="white",
        relief=tk.RAISED,
        height=1
    )
    app.generate_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
    
    # 2. 修改按钮 (新增)
    app.modify_content_btn = tk.Button(
        btns_frame,
        text="🪄 AI 修改正文",
        command=lambda: app.generation_service.modify_content(),
        font=("Microsoft YaHei", 10, "bold"),
        bg="#6f42c1",
        fg="white",
        relief=tk.RAISED,
        height=1
    )
    app.modify_content_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 2))
    
    # 3. 定稿按钮 (复用，同步至大纲摘要页)
    app.finalize_btn = tk.Button(
        btns_frame,
        text="📝 章节定稿",
        command=app.finalize_content,
        font=("Microsoft YaHei", 10, "bold"),
        bg="#007bff",
        fg="white",
        relief=tk.RAISED,
        height=1
    )
    app.finalize_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 2))
    
    # 4. 保存按钮
    save_btn = tk.Button(
        btns_frame,
        text="💾 保存修改",
        command=app.save_current_chapter,
        font=("Microsoft YaHei", 10),
        bg="#28a745",
        fg="white",
        relief=tk.RAISED,
        height=1
    )
    save_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 2))

    # 5. 导出单章 (新增至并列)
    app.export_chapter_btn = tk.Button(
        btns_frame,
        text="📄 导出单章",
        command=app.novel_service.export_current_chapter,
        font=("Microsoft YaHei", 10, "bold"),
        bg="#f8f9fa",
        relief=tk.RAISED,
        height=1
    )
    app.export_chapter_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
    
    # 字数统计
    app.word_count_label = tk.Label(
        btns_frame,
        text="字数: 0",
        font=("Microsoft YaHei", 10),
        fg="#666666"
    )
    app.word_count_label.pack(side=tk.RIGHT, padx=(5, 0))

    # 初始状态
    app.content_text.config(state=tk.DISABLED)
