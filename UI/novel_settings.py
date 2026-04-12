import tkinter as tk
from tkinter import ttk, scrolledtext


def create_novel_settings_page(app, parent):
    """创建小说设置页面（独立模块）

    参数:
        app: 主应用实例，用于挂载/访问控件与回调
        parent: 承载该页面的父容器
    """
    # 小说基本信息框架
    novel_info_frame = ttk.LabelFrame(parent, text="小说基本信息", padding=20)
    novel_info_frame.pack(fill=tk.X, pady=(0, 20))

    # 小说目录（只读） - 排在第一位
    row = 0
    tk.Label(novel_info_frame, text="小说目录:", font=("Microsoft YaHei", 10)).grid(
        row=row, column=0, sticky=tk.W, pady=15, padx=10
    )
    app.novel_dir_var = tk.StringVar(value=getattr(app, "current_novel_dir", ""))
    novel_dir_entry = tk.Entry(
        novel_info_frame,
        textvariable=app.novel_dir_var,
        font=("Microsoft YaHei", 10),
        width=40,
        state="readonly"
    )
    novel_dir_entry.grid(row=row, column=1, sticky=tk.EW, pady=15, padx=10)
    novel_info_frame.columnconfigure(1, weight=1)

    # 小说标题
    row = 1
    tk.Label(novel_info_frame, text="小说标题:", font=("Microsoft YaHei", 10)).grid(
        row=row, column=0, sticky=tk.W, pady=15, padx=10
    )
    app.title_entry = tk.Entry(
        novel_info_frame,
        font=("Microsoft YaHei", 11),
        width=40
    )
    app.title_entry.grid(row=row, column=1, sticky=tk.EW, pady=15, padx=10)

    # 小说类型
    row = 2
    tk.Label(novel_info_frame, text="小说类型:", font=("Microsoft YaHei", 10)).grid(
        row=row, column=0, sticky=tk.W, pady=15, padx=10
    )
    app.novel_type_var = tk.StringVar(value="其他")
    novel_type_combo = ttk.Combobox(
        novel_info_frame,
        textvariable=app.novel_type_var,
        values=["玄幻", "都市", "科幻", "历史", "言情", "悬疑", "武侠", "其他"],
        state="readonly",
        width=37,
        font=("Microsoft YaHei", 10)
    )
    novel_type_combo.grid(row=row, column=1, sticky=tk.EW, pady=15, padx=10)

    # 写作风格
    row = 3
    tk.Label(novel_info_frame, text="写作风格:", font=("Microsoft YaHei", 10)).grid(
        row=row, column=0, sticky=tk.W, pady=15, padx=10
    )
    app.writing_style_text = scrolledtext.ScrolledText(
        novel_info_frame,
        font=("Microsoft YaHei", 10),
        width=40,
        height=2,
        wrap=tk.WORD
    )
    app.writing_style_text.insert("1.0", "平实自然")
    app.writing_style_text.grid(row=row, column=1, sticky=tk.EW, pady=15, padx=10)

    # 思想宗旨（多行）
    row = 4
    tk.Label(novel_info_frame, text="思想宗旨:", font=("Microsoft YaHei", 10)).grid(
        row=row, column=0, sticky=tk.W, pady=15, padx=10
    )
    app.novel_theme_text = scrolledtext.ScrolledText(
        novel_info_frame,
        font=("Microsoft YaHei", 10),
        width=40,
        height=3,
        wrap=tk.WORD
    )
    app.novel_theme_text.grid(row=row, column=1, sticky=tk.EW, pady=15, padx=10)

    # 剧情主线（多行）
    row = 5
    tk.Label(novel_info_frame, text="剧情主线:", font=("Microsoft YaHei", 10)).grid(
        row=row, column=0, sticky=tk.W, pady=15, padx=10
    )
    app.novel_outline_text = scrolledtext.ScrolledText(
        novel_info_frame,
        font=("Microsoft YaHei", 10),
        width=40,
        height=4,
        wrap=tk.WORD
    )
    app.novel_outline_text.grid(row=row, column=1, sticky=tk.EW, pady=15, padx=10)

    # 章节字数
    row = 6
    tk.Label(novel_info_frame, text="章节字数:", font=("Microsoft YaHei", 10)).grid(
        row=row, column=0, sticky=tk.W, pady=15, padx=10
    )
    
    # 章节字数输入框和说明
    word_count_frame = tk.Frame(novel_info_frame)
    word_count_frame.grid(row=row, column=1, sticky=tk.W, pady=15, padx=10)
    
    app.chapter_words_var = tk.IntVar(value=3000)
    word_count_spin = tk.Spinbox(
        word_count_frame,
        from_=500,
        to=50000,
        increment=100,
        textvariable=app.chapter_words_var,
        width=15,
        font=("Microsoft YaHei", 10)
    )
    word_count_spin.pack(side=tk.LEFT)
    
    # 添加说明文字
    word_count_hint = tk.Label(
        word_count_frame,
        text="（注：设置字数和实际生成字数可能有差异）",
        font=("Microsoft YaHei", 9),
        fg="#666666"
    )
    word_count_hint.pack(side=tk.LEFT, padx=(10, 0))

    # 操作按钮行
    row = 7
    btns_frame = tk.Frame(novel_info_frame)
    btns_frame.grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=(5, 0), padx=10)
    btns_frame.columnconfigure(0, weight=1)
    btns_frame.columnconfigure(1, weight=1)
    btns_frame.columnconfigure(2, weight=1)
    btns_frame.columnconfigure(3, weight=1)

    create_btn = tk.Button(
        btns_frame,
        text="🆕 创建小说",
        command=lambda: getattr(app, "create_new_novel", lambda: None)(),
        font=("Microsoft YaHei", 10),
        bg="#17a2b8",
        fg="white",
        cursor="hand2",
        height=1
    )
    create_btn.grid(row=0, column=0, sticky=tk.EW, padx=5)

    load_btn = tk.Button(
        btns_frame,
        text="📂 读取小说",
        command=lambda: (getattr(app, "load_novel_config", None) or getattr(app, "load_novel", lambda: None))(),
        font=("Microsoft YaHei", 10),
        bg="#6c757d",
        fg="white",
        cursor="hand2",
        height=1
    )
    load_btn.grid(row=0, column=1, sticky=tk.EW, padx=5)

    save_btn = tk.Button(
        btns_frame,
        text="💾 保存设置",
        command=lambda: getattr(app, "save_novel_config", lambda: None)(),
        font=("Microsoft YaHei", 10),
        bg="#28a745",
        fg="white",
        cursor="hand2",
        height=1
    )
    save_btn.grid(row=0, column=2, sticky=tk.EW, padx=5)

    export_btn = tk.Button(
        btns_frame,
        text="📤 导出小说",
        command=lambda: getattr(app, "export_novel_to_txt", lambda: None)(),
        font=("Microsoft YaHei", 10),
        bg="#fd7e14",
        fg="white",
        cursor="hand2",
        height=1
    )
    export_btn.grid(row=0, column=3, sticky=tk.EW, padx=5)


