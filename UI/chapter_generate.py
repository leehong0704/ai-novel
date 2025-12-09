"""
章节生成页面
负责创建和管理章节生成界面
"""

import tkinter as tk
from tkinter import ttk, scrolledtext


def create_chapter_generate_page(app, parent):
    """创建章节生成页面"""
    # 左侧：输入区域
    left_panel = tk.Frame(parent)
    left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
    # 当前章节索引（用于切换时自动保存）
    app.current_chapter_index = None
    # 用于检测章节内容是否改变
    app.original_chapter_prompt = ""
    app.original_chapter_content = ""
    
    # 右侧：输出区域
    right_panel = tk.Frame(parent)
    right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
    
    # 创建垂直分割窗格
    v_paned = tk.PanedWindow(right_panel, orient=tk.VERTICAL, sashwidth=6, sashrelief=tk.RAISED)
    v_paned.pack(fill=tk.BOTH, expand=True)

    # ========== 右侧：创作提示 ==========
    prompt_frame = ttk.LabelFrame(v_paned, text="📝 创作提示", padding=15)
    v_paned.add(prompt_frame, height=220)
    
    app.prompt_text = scrolledtext.ScrolledText(
        prompt_frame,
        font=("Microsoft YaHei", 11),
        wrap=tk.WORD,
        height=8
    )
    app.prompt_text.pack(fill=tk.BOTH, expand=True)
    app.prompt_text.insert(
        "1.0", 
        "请输入你的创作想法、情节设定或续写提示...\n\n例如：\n- 主角是一个失忆的剑客\n- 故事发生在未来的赛博朋克世界\n- 续写：主角推开门，发现..."
    )
    # 绑定事件：先清除占位符，再保持章节选择状态
    def on_prompt_focus_in(event):
        app.clear_placeholder(event)
        app.preserve_chapter_selection()
    
    app.prompt_text.bind("<FocusIn>", on_prompt_focus_in)
    app.prompt_text.bind("<KeyRelease>", app.update_prompt_char_count)
    # 保持章节列表选择状态
    app.prompt_text.bind("<Button-1>", lambda e: app.preserve_chapter_selection())
    
    # 创作提示字数统计
    app.prompt_char_count_label = tk.Label(
        prompt_frame,
        text="当前字数: 0 字",
        font=("Microsoft YaHei", 9),
        anchor=tk.E,
        fg="#666666"
    )
    app.prompt_char_count_label.pack(side=tk.RIGHT, pady=(5, 0))
    
    # Generate Button (Moved to bottom of output_frame)
    
    # ========== 左侧：创作提示 ==========
    # 章节管理（列表 + 按钮）
    chapters_mgmt = ttk.LabelFrame(left_panel, text="📑 章节管理", padding=10)
    chapters_mgmt.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    list_container = tk.Frame(chapters_mgmt)
    list_container.pack(fill=tk.BOTH, expand=True)
    scrollbar = tk.Scrollbar(list_container, orient=tk.VERTICAL)
    app.chapter_listbox = tk.Listbox(
        list_container,
        height=16,
        font=("Microsoft YaHei", 10),
        yscrollcommand=scrollbar.set,
        selectmode=tk.SINGLE,
        exportselection=False  # 防止焦点转移时丢失选择
    )
    app.chapter_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=app.chapter_listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    # 双击载入到编辑器
    app.chapter_listbox.bind("<Double-Button-1>", lambda e: app.load_selected_chapter())
    # 选择改变时自动载入到编辑器（静默）
    app.chapter_listbox.bind("<<ListboxSelect>>", app.on_chapter_selected)

    mgmt_btns = tk.Frame(chapters_mgmt)
    mgmt_btns.pack(fill=tk.X, pady=(8, 0))
    tk.Button(mgmt_btns, text="➕ 新增", command=app.add_new_chapter_from_editor, cursor="hand2").pack(side=tk.LEFT)
    tk.Button(mgmt_btns, text="📥 插入到所选位置", command=app.insert_chapter_at_selection, cursor="hand2").pack(side=tk.LEFT, padx=(10, 0))
    tk.Button(mgmt_btns, text="✏️ 编辑标题", command=app.rename_selected_chapter, cursor="hand2").pack(side=tk.LEFT, padx=(10, 0))
    tk.Button(mgmt_btns, text="🗑️ 删除", command=app.delete_selected_chapter, cursor="hand2").pack(side=tk.LEFT, padx=(10, 0))

    # 提示输入移至右侧
    
    # 按钮框架已移除
    # button_frame = tk.Frame(left_panel)
    # button_frame.pack(fill=tk.X)
    
    # app.generate_btn 移至右侧
    # app.save_btn 已移除
    # app.clear_btn 已移除
    
    # ========== 右侧：生成内容 ==========
    output_frame = ttk.LabelFrame(v_paned, text="📖 生成内容", padding=15)
    v_paned.add(output_frame)
    
    # 字数统计 (Moved to bottom button frame)
    
    # 底部按钮区域
    btns_frame = tk.Frame(output_frame)
    btns_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
    
    app.generate_btn = tk.Button(
        btns_frame,
        text="🚀 生成小说",
        command=app.generate_content,
        font=("Microsoft YaHei", 11, "bold"),
        bg="#1f77b4",
        fg="white",
        relief=tk.RAISED,
        cursor="hand2",
        height=1
    )
    app.generate_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
    
    
    # 续写按钮（已隐藏，但保留逻辑代码）
    app.modify_btn = tk.Button(
        btns_frame,
        text="🖊️ 续写小说",
        command=app.continue_content,
        font=("Microsoft YaHei", 11),
        bg="#ffc107",
        fg="black",
        relief=tk.RAISED,
        cursor="hand2",
        height=1
    )
    # 隐藏续写按钮 - 如需恢复，取消下面这行的注释
    # app.modify_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
    
    # 保存按钮
    save_btn = tk.Button(
        btns_frame,
        text="💾 保存章节",
        command=app.save_current_chapter,
        font=("Microsoft YaHei", 11),
        bg="#28a745",
        fg="white",
        relief=tk.RAISED,
        cursor="hand2",
        height=1
    )
    save_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
    
    # 清空按钮
    clear_btn = tk.Button(
        btns_frame,
        text="🗑️ 清空内容",
        command=app.clear_content,
        font=("Microsoft YaHei", 11),
        bg="#dc3545",
        fg="white",
        relief=tk.RAISED,
        cursor="hand2",
        height=1
    )
    clear_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
    
    # 字数统计标签
    app.word_count_label = tk.Label(
        btns_frame,
        text="字数: 0",
        font=("Microsoft YaHei", 10),
        fg="#666666"
    )
    app.word_count_label.pack(side=tk.RIGHT, padx=(10, 0))
    
    # 生成内容文本框
    app.content_text = scrolledtext.ScrolledText(
        output_frame,
        font=("Microsoft YaHei", 11),
        wrap=tk.WORD
    )
    app.content_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    app.content_text.bind("<KeyRelease>", app.update_word_count)
    # 保持章节列表选择状态
    app.content_text.bind("<Button-1>", lambda e: app.preserve_chapter_selection())
    app.content_text.bind("<FocusIn>", lambda e: app.preserve_chapter_selection())
