"""
章节策划页面
负责管理章节列表以及每章的剧情策划（标题、概述、高潮、钩子）
"""

import tkinter as tk
from tkinter import ttk, scrolledtext

def create_chapter_generate_page(app, parent):
    """创建章节策划页面"""
    # 左侧：章节管理
    left_panel = tk.Frame(parent)
    left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
    
    # 章节列表管理
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
        exportselection=False
    )
    app.chapter_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=app.chapter_listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # 绑定选择事件
    app.chapter_listbox.bind("<<ListboxSelect>>", lambda e: app.on_chapter_selected(e, source="plan"))
    
    # 按钮组
    mgmt_btns = tk.Frame(chapters_mgmt)
    mgmt_btns.pack(fill=tk.X, pady=(8, 0))
    tk.Button(mgmt_btns, text="➕ 新增章节", command=app.add_new_chapter_from_editor, cursor="hand2").pack(side=tk.LEFT)
    tk.Button(mgmt_btns, text="📥 插入", command=app.insert_chapter_at_selection, cursor="hand2").pack(side=tk.LEFT, padx=(10, 0))
    tk.Button(mgmt_btns, text="✏️ 标题", command=app.rename_selected_chapter, cursor="hand2").pack(side=tk.LEFT, padx=(10, 0))
    tk.Button(mgmt_btns, text="🗑️ 删除", command=app.delete_selected_chapter, cursor="hand2").pack(side=tk.LEFT, padx=(10, 0))
    tk.Button(mgmt_btns, text="📤 导出全文", command=app.novel_service.export_novel_text, cursor="hand2", bg="#f8f9fa").pack(side=tk.RIGHT)

    # 右侧：策划详情容器
    right_panel = tk.Frame(parent)
    right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
    
    # 子标签页容器
    sub_notebook = ttk.Notebook(right_panel)
    sub_notebook.pack(fill=tk.BOTH, expand=True)
    
    # ==================== Tab 1: 章节大纲 ====================
    outline_tab = tk.Frame(sub_notebook, padx=10, pady=10)
    sub_notebook.add(outline_tab, text="🎯 章节大纲")
    
    # 章节大纲内容容器
    plot_frame = tk.Frame(outline_tab)
    plot_frame.pack(fill=tk.BOTH, expand=True)
    
    # 1. 章节标题
    title_info = tk.Frame(plot_frame)
    title_info.pack(fill=tk.X, pady=(0, 10))
    tk.Label(title_info, text="章节标题：", font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)
    app.chapter_title_var = tk.StringVar()
    tk.Entry(title_info, textvariable=app.chapter_title_var, font=("Microsoft YaHei", 11)).pack(side=tk.LEFT, fill=tk.X, expand=True)

    # 2. 章节细纲 (原内容概述)
    prompt_header = tk.Frame(plot_frame)
    prompt_header.pack(fill=tk.X, pady=(5, 5))
    tk.Label(prompt_header, text="📑 章节细纲 (AI创作提示)：", font=("Microsoft YaHei", 10, "bold")).pack(side=tk.LEFT)
    app.prompt_word_count_label = tk.Label(prompt_header, text="字数: 0", font=("Microsoft YaHei", 9), fg="gray")
    app.prompt_word_count_label.pack(side=tk.RIGHT)
    
    app.prompt_text = scrolledtext.ScrolledText(
        plot_frame,
        font=("Microsoft YaHei", 11),
        wrap=tk.WORD,
        height=10
    )
    app.prompt_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
    # 绑定字数统计
    def on_prompt_keypress(event=None):
        if hasattr(app, 'update_prompt_char_count'):
            app.update_prompt_char_count(event)
    
    app.prompt_text.bind("<KeyRelease>", on_prompt_keypress)

    # 3. 章节高潮与钩子
    grid_container = tk.Frame(plot_frame)
    grid_container.pack(fill=tk.X, pady=5)
    
    # 高潮
    tk.Label(grid_container, text="章节高潮：", font=("Microsoft YaHei", 10)).pack(anchor=tk.W)
    app.chapter_climax_text = scrolledtext.ScrolledText(grid_container, height=3, font=("Microsoft YaHei", 10), wrap=tk.WORD)
    app.chapter_climax_text.pack(fill=tk.X, pady=(0, 10))
    
    # 钩子
    tk.Label(grid_container, text="章节钩子：", font=("Microsoft YaHei", 10)).pack(anchor=tk.W)
    app.chapter_hook_text = scrolledtext.ScrolledText(grid_container, height=3, font=("Microsoft YaHei", 10), wrap=tk.WORD)
    app.chapter_hook_text.pack(fill=tk.X, pady=(0, 10))

    # 大纲页按钮
    outline_btn_container = tk.Frame(outline_tab)
    outline_btn_container.pack(fill=tk.X, pady=(5, 0))
    
    tk.Button(
        outline_btn_container,
        text="💾 保存大纲",
        command=app.save_current_chapter,
        font=("Microsoft YaHei", 9, "bold"),
        bg="#28a745",
        fg="white",
        height=1,
        cursor="hand2"
    ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
    
    tk.Button(
        outline_btn_container,
        text="🚀 AI 自动构思",
        command=app.generate_outline,
        font=("Microsoft YaHei", 9, "bold"),
        bg="#6f42c1",
        fg="white",
        height=1,
        cursor="hand2"
    ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

    # ==================== Tab 2: 章节摘要 ====================
    summary_tab = tk.Frame(sub_notebook, padx=10, pady=10)
    sub_notebook.add(summary_tab, text="📝 章节总结")
    
    # 摘要内容容器
    summary_scroll_container = tk.Frame(summary_tab)
    summary_scroll_container.pack(fill=tk.BOTH, expand=True)

    # 1. 全局摘要
    tk.Label(summary_scroll_container, text="🌐 全局摘要 (精炼全书主线)：", font=("Microsoft YaHei", 10, "bold"), fg="#1f77b4").pack(anchor=tk.W, pady=(0, 5))
    app.global_summary_text = scrolledtext.ScrolledText(summary_scroll_container, height=5, font=("Microsoft YaHei", 10), wrap=tk.WORD)
    app.global_summary_text.pack(fill=tk.X, pady=(0, 15))
    
    # 2. 本章摘要
    tk.Label(summary_scroll_container, text="🕒 本章摘要 (当前章节内容深度总结)：", font=("Microsoft YaHei", 10, "bold"), fg="#28a745").pack(anchor=tk.W, pady=(5, 5))
    app.recent_summary_text = scrolledtext.ScrolledText(summary_scroll_container, height=6, font=("Microsoft YaHei", 10), wrap=tk.WORD)
    app.recent_summary_text.pack(fill=tk.X, pady=(0, 15))
    
    # 3. 角色状态
    tk.Label(summary_scroll_container, text="👤 角色状态 (当前各角色所处情况)：", font=("Microsoft YaHei", 10, "bold"), fg="#fd7e14").pack(anchor=tk.W, pady=(5, 5))
    app.char_status_text = scrolledtext.ScrolledText(summary_scroll_container, height=6, font=("Microsoft YaHei", 10), wrap=tk.WORD)
    app.char_status_text.pack(fill=tk.X, pady=(0, 15))

    # 摘要页按钮
    summary_btn_container = tk.Frame(summary_tab)
    summary_btn_container.pack(fill=tk.X, pady=(10, 0))
    
    app.generate_summary_btn = tk.Button(
        summary_btn_container,
        text="✨ 生成/更新定稿摘要",
        command=app.finalize_content,
        font=("Microsoft YaHei", 10, "bold"),
        bg="#17a2b8",
        fg="white",
        height=2,
        cursor="hand2"
    )
    app.generate_summary_btn.pack(fill=tk.X)

    # 初始化变量
    app.current_chapter_index = None
