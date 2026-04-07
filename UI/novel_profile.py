import tkinter as tk
from tkinter import ttk, simpledialog, scrolledtext, messagebox
import os
import configparser


def create_novel_profile_page(app, parent):
    """创建“小说设定”页面（独立模块）

    参数:
        app: 主应用实例（用于挂载变量）
        parent: 承载该页面的父容器
    """
    root_frame = tk.Frame(parent)
    root_frame.pack(fill=tk.BOTH, expand=True)

    # 小说设定列表（放置在右侧）
    left_frame = ttk.LabelFrame(root_frame, text="小说设定列表", padding=10)
    left_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
    left_frame.columnconfigure(0, weight=1)
    left_frame.rowconfigure(0, weight=1)

    # 复选列表通用类
    # 
    # 功能说明：
    # 该类实现了双重选择机制，用于小说设定列表和人物设定列表：
    # 
    # 1. 【单选机制】- 用于编辑/删除操作
    #    - 点击项目文字时，该项目背景变为浅蓝色 (#cce5ff)，表示被选中
    #    - 同一时间只能有一个项目被单选（高亮显示）
    #    - 再次点击已选中的项目可取消选中
    #    - 点击其他项目时，自动取消之前项目的高亮
    #    - 通过 get_selected() 获取当前单选的项目名称
    #    - 编辑和删除按钮依赖此单选状态
    # 
    # 2. 【复选框机制】- 用于AI生成时的设定传递
    #    - 每个项目前面有一个独立的复选框
    #    - 勾选的项目会在生成小说时传递给AI作为参考设定
    #    - 可以同时勾选多个项目
    #    - 通过 get_checked() 获取所有勾选的项目列表
    #    - 勾选状态会保存到 novel.ini 配置文件中
    # 
    # 3. 【两种选择互不干扰】
    #    - 单选（文字变色）和复选框是完全独立的两个状态
    #    - 可以单选某个项目进行编辑，同时勾选其他项目用于AI生成
    #    - 删除操作只删除单选的项目，不影响其他勾选的项目
    # 
    # 使用示例：
    #    - 要编辑某个设定：点击文字使其变色 → 点击"编辑"按钮
    #    - 要删除某个设定：点击文字使其变色 → 点击"删除"按钮
    #    - 要在生成时使用某些设定：勾选对应的复选框
    # 
    class ScrollCheckList:
        def __init__(self, parent_frame, on_hover_content):
            self.vars = {}  # name -> BooleanVar (复选框状态)
            self.labels = {}  # name -> Label (文字标签)
            self.frames = {}  # name -> Frame (用于设置背景色)
            self.selected_name = None  # 当前单选的项目名称（用于编辑/删除）
            self.on_hover_content = on_hover_content
            self.canvas = tk.Canvas(parent_frame, highlightthickness=0)
            self.scroll = tk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.canvas.yview)
            self.inner = tk.Frame(self.canvas)
            self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
            self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
            self.canvas.configure(yscrollcommand=self.scroll.set)
            self.canvas.grid(row=0, column=0, sticky=tk.NSEW)
            self.scroll.grid(row=0, column=1, sticky=tk.NS)
            parent_frame.columnconfigure(0, weight=1)
            parent_frame.rowconfigure(0, weight=1)
            self.tooltip = None

        def _bind_tooltip(self, name, widget):
            def on_enter(e):
                content = self.on_hover_content(name) or ""
                if not content:
                    return
                self._show_tip(content, e.x_root + 12, e.y_root + 12)
            def on_motion(e):
                if self.tooltip:
                    self.tooltip.geometry(f"+{e.x_root+12}+{e.y_root+12}")
            def on_leave(e):
                self._hide_tip()
            widget.bind("<Enter>", on_enter)
            widget.bind("<Motion>", on_motion)
            widget.bind("<Leave>", on_leave)

        def _show_tip(self, text, x, y):
            self._hide_tip()
            self.tooltip = tk.Toplevel(self.inner)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            display = text.strip()
            if len(display) > 800:
                display = display[:800] + "…"
            tk.Label(self.tooltip, text=display, justify=tk.LEFT, relief=tk.SOLID, borderwidth=1,
                     font=("Microsoft YaHei", 9), bg="#ffffe0", wraplength=380, padx=8, pady=6).pack()

        def _hide_tip(self):
            if self.tooltip:
                try:
                    self.tooltip.destroy()
                except Exception:
                    pass
                self.tooltip = None

        def _on_label_click(self, name):
            """单击标签时选中该项（用于编辑/删除）"""
            # 取消之前选中项的高亮
            if self.selected_name and self.selected_name in self.frames:
                self.frames[self.selected_name].config(bg="SystemButtonFace")
                if self.selected_name in self.labels:
                    self.labels[self.selected_name].config(bg="SystemButtonFace")
            
            # 如果点击的是已选中项，则取消选中
            if self.selected_name == name:
                self.selected_name = None
            else:
                # 选中新项并高亮
                self.selected_name = name
                if name in self.frames:
                    self.frames[name].config(bg="#cce5ff")
                if name in self.labels:
                    self.labels[name].config(bg="#cce5ff")

        def clear(self):
            for child in self.inner.winfo_children():
                child.destroy()
            self.vars.clear()
            self.labels.clear()
            self.frames.clear()
            self.selected_name = None

        def add_item(self, name, checked=False):
            row = len(self.vars)
            
            # 创建一个框架来包含复选框和标签，便于设置背景色
            item_frame = tk.Frame(self.inner)
            item_frame.grid(row=row, column=0, columnspan=2, sticky=tk.EW, padx=2, pady=2)
            item_frame.columnconfigure(1, weight=1)
            
            var = tk.BooleanVar(value=checked)
            def on_toggle(n=name, v=var):
                if self is app.novel_setting_checks:
                    app.novel_setting_checked[n] = v.get()
                    update_selection_entry("NOVEL_SETTINGS_SELECTED", n, v.get())
                else:
                    app.character_setting_checked[n] = v.get()
                    update_selection_entry("CHARACTERS_SELECTED", n, v.get())
            
            cb = tk.Checkbutton(item_frame, text="", variable=var, onvalue=True, offvalue=False, command=on_toggle)
            cb.grid(row=0, column=0, sticky=tk.W, padx=(4, 6), pady=2)
            
            lbl = tk.Label(item_frame, text=name, font=("Microsoft YaHei", 11), cursor="hand2")
            lbl.grid(row=0, column=1, sticky=tk.W, pady=2)
            
            # 绑定点击事件
            lbl.bind("<Button-1>", lambda e, n=name: self._on_label_click(n))
            
            self.vars[name] = var
            self.labels[name] = lbl
            self.frames[name] = item_frame
            self._bind_tooltip(name, lbl)

        def get_checked(self):
            """获取勾选的项目（用于AI生成）"""
            return [name for name, var in self.vars.items() if var.get()]
        
        def get_selected(self):
            """获取单选的项目（用于编辑/删除）"""
            return self.selected_name

        def rebuild(self, details_dict, checked_dict):
            self.clear()
            for name in details_dict.keys():
                self.add_item(name, checked=checked_dict.get(name, False))

        def remove_names(self, names):
            for name in names:
                if name in self.frames:
                    self.frames[name].grid_forget()
                    self.frames[name].destroy()
                    del self.frames[name]
                if name in self.labels:
                    del self.labels[name]
                if name in self.vars:
                    del self.vars[name]
            # 如果删除的是当前选中项，清空选中状态
            if self.selected_name in names:
                self.selected_name = None
            # caller can call rebuild() to normalize rows

    def create_character_dialog(dialog_title, initial_name="", initial_content=""):
        win = tk.Toplevel(parent)
        win.title(dialog_title)
        win.transient(parent)
        win.grab_set()
        app.ui_helper.center_window(win, 560, 650)

        # 简单的内容解析（支持回填）
        fields = {
            '角色设定': '', '性别': '', '年龄': '', '身份': '',
            '性格': '', '特点': '', '外貌': '', '服饰': ''
        }
        if initial_content:
            lines = initial_content.splitlines()
            for line in lines:
                if '：' in line:
                    parts = line.split('：', 1)
                    k, v = parts[0].strip(), parts[1].strip()
                    if k in fields:
                        fields[k] = v

        body = tk.Frame(win, padx=20, pady=15)
        body.pack(fill=tk.BOTH, expand=True)

        row = 0
        def add_field(label_text, value="", field_type="entry", combo_values=None):
            nonlocal row
            tk.Label(body, text=label_text, font=("Microsoft YaHei", 10)).grid(row=row, column=0, sticky=tk.W, pady=5)
            if field_type == "entry":
                var = tk.StringVar(value=value or "")
                entry = tk.Entry(body, textvariable=var, font=("Microsoft YaHei", 10))
                entry.grid(row=row, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
                row += 1
                return var
            elif field_type == "combo":
                default_val = value or (combo_values[0] if combo_values else "男")
                var = tk.StringVar(value=default_val)
                vals = combo_values if combo_values else ["男", "女", "其他"]
                combo = ttk.Combobox(body, textvariable=var, values=vals, state="readonly", font=("Microsoft YaHei", 10))
                combo.grid(row=row, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
                row += 1
                return var
            elif field_type == "text":
                txt = scrolledtext.ScrolledText(body, font=("Microsoft YaHei", 10), height=3, wrap=tk.WORD)
                txt.grid(row=row, column=1, sticky=tk.NSEW, pady=5, padx=(10, 0))
                txt.insert("1.0", value or "")
                row += 1
                return txt

        name_var = add_field("名字：", initial_name)
        role_var = add_field(
            "角色设定：", 
            fields['角色设定'], 
            field_type="combo", 
            combo_values=["主角", "男主角", "女主角", "男配角", "女配角", "工具人", "反派", "其他"]
        )
        gender_var = add_field("性别：", fields['性别'], field_type="combo")
        age_var = add_field("年龄：", fields['年龄'])
        identity_var = add_field("身份：", fields['身份'])
        personality_text = add_field("性格：", fields['性格'], field_type="text")
        trait_text = add_field("特点：", fields['特点'], field_type="text")
        appearance_text = add_field("外貌：", fields['外貌'], field_type="text")
        clothing_text = add_field("服饰：", fields['服饰'], field_type="text")

        body.columnconfigure(1, weight=1)

        result = {}
        def on_ok():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("提示", "名字不能为空！", parent=win)
                return
            
            # 组织内容字符串
            content_lines = []
            def add_line(k, v):
                cleaned_v = v.get("1.0", tk.END).strip() if isinstance(v, (tk.Text, scrolledtext.ScrolledText)) else v.get().strip()
                if cleaned_v: content_lines.append(f"{k}：{cleaned_v}")
            
            add_line("角色设定", role_var)
            add_line("性别", gender_var)
            add_line("年龄", age_var)
            add_line("身份", identity_var)
            add_line("性格", personality_text)
            add_line("特点", trait_text)
            add_line("外貌", appearance_text)
            add_line("服饰", clothing_text)
            
            result["value"] = (name, "\n".join(content_lines))
            win.destroy()

        footer = tk.Frame(win, padx=20, pady=10)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Button(footer, text="保存", command=on_ok, bg="#28a745", fg="white", cursor="hand2", width=10).pack(side=tk.RIGHT, padx=5)
        tk.Button(footer, text="取消", command=win.destroy, cursor="hand2", width=10).pack(side=tk.RIGHT, padx=5)

        win.wait_window()
        return result.get("value")

    def create_novel_setting_dialog(dialog_title, initial_name="", initial_content=""):
        win = tk.Toplevel(parent)
        win.title(dialog_title)
        win.transient(parent)
        win.grab_set()
        app.ui_helper.center_window(win, 540, 450)

        # 尝试从内容字符串中解析类别
        category = "其他"
        actual_content = initial_content
        if initial_content and "类别：" in initial_content:
            lines = initial_content.splitlines()
            if lines and lines[0].startswith("类别："):
                category = lines[0].replace("类别：", "").strip()
                if len(lines) > 1 and lines[1].startswith("内容："):
                    actual_content = "\n".join(lines[1:]).replace("内容：", "", 1).strip()
                else:
                    actual_content = "\n".join(lines[1:]).strip()

        body = tk.Frame(win, padx=20, pady=15)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(body, text="名称：", font=("Microsoft YaHei", 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar(value=initial_name)
        tk.Entry(body, textvariable=name_var, font=("Microsoft YaHei", 11)).grid(row=0, column=1, sticky=tk.EW, pady=5, padx=(10, 0))

        tk.Label(body, text="类别：", font=("Microsoft YaHei", 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        cat_var = tk.StringVar(value=category)
        ttk.Combobox(body, textvariable=cat_var, values=["环境", "物品", "规则", "名词解释", "其他"], state="readonly", font=("Microsoft YaHei", 10)).grid(row=1, column=1, sticky=tk.EW, pady=5, padx=(10, 0))

        tk.Label(body, text="内容：", font=("Microsoft YaHei", 10)).grid(row=2, column=0, sticky=tk.NW, pady=5)
        content_text = scrolledtext.ScrolledText(body, font=("Microsoft YaHei", 10), height=10, wrap=tk.WORD)
        content_text.grid(row=2, column=1, sticky=tk.NSEW, pady=5, padx=(10, 0))
        content_text.insert("1.0", actual_content)

        body.columnconfigure(1, weight=1)
        body.rowconfigure(2, weight=1)

        result = {}
        def on_ok():
            n = name_var.get().strip()
            c = content_text.get("1.0", tk.END).strip()
            cat = cat_var.get()
            if not n:
                messagebox.showwarning("提示", "名称不能为空！", parent=win)
                return
            result["value"] = (n, f"类别：{cat}\n内容：{c}")
            win.destroy()

        footer = tk.Frame(win, padx=20, pady=10)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Button(footer, text="保存", command=on_ok, bg="#28a745", fg="white", cursor="hand2", width=10).pack(side=tk.RIGHT, padx=5)
        tk.Button(footer, text="取消", command=win.destroy, cursor="hand2", width=10).pack(side=tk.RIGHT, padx=5)

        win.wait_window()
        return result.get("value")

    def create_item_with_content(dialog_title, name_label):
        win = tk.Toplevel(parent)
        win.title(dialog_title)
        win.transient(parent)
        win.grab_set()
        win.geometry("520x360")

        body = tk.Frame(win, padx=16, pady=12)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(body, text=name_label, font=("Microsoft YaHei", 10)).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        name_var = tk.StringVar()
        name_entry = tk.Entry(body, textvariable=name_var, font=("Microsoft YaHei", 10))
        name_entry.grid(row=0, column=1, sticky=tk.EW, pady=(0, 10))

        tk.Label(body, text="内容：", font=("Microsoft YaHei", 10)).grid(row=1, column=0, sticky=tk.NW)
        content_text = scrolledtext.ScrolledText(body, font=("Microsoft YaHei", 10), height=10, wrap=tk.WORD)
        content_text.grid(row=1, column=1, sticky=tk.NSEW, pady=(0, 10))

        body.columnconfigure(1, weight=1)
        body.rowconfigure(1, weight=1)

        def on_cancel():
            win.destroy()

        def on_ok():
            name = name_var.get().strip()
            content = content_text.get("1.0", tk.END).strip()
            if not name:
                tk.messagebox.showwarning("提示", "名称不能为空！", parent=win)
                return
            win.destroy()
            return name, content

        footer = tk.Frame(win, padx=16, pady=8)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Button(footer, text="取消", command=on_cancel, cursor="hand2").pack(side=tk.RIGHT, padx=6)
        result = {}
        def ok_and_store():
            r = on_ok()
            if r:
                result["value"] = r
        tk.Button(footer, text="确定", command=ok_and_store, bg="#28a745", fg="white", cursor="hand2").pack(side=tk.RIGHT, padx=6)

        win.wait_window()
        return result.get("value")

    # 确保存储字典存在
    if not hasattr(app, "novel_setting_details"):
        app.novel_setting_details = {}
    if not hasattr(app, "character_setting_details"):
        app.character_setting_details = {}
    if not hasattr(app, "novel_setting_checked"):
        app.novel_setting_checked = {}
    if not hasattr(app, "character_setting_checked"):
        app.character_setting_checked = {}

    def update_selection_entry(section: str, name: str, checked: bool):
        try:
            novel_dir = getattr(app, "current_novel_dir", "")
            if not novel_dir:
                return
            ini_path = os.path.join(novel_dir, "novel.ini")
            cfg = configparser.ConfigParser(interpolation=None)
            if os.path.exists(ini_path):
                cfg.read(ini_path, encoding="utf-8")
            if section not in cfg:
                cfg[section] = {}
            cfg[section][name] = "true" if checked else "false"
            with open(ini_path, "w", encoding="utf-8") as f:
                cfg.write(f)
        except Exception:
            pass

    def delete_selection_entry(section: str, name: str):
        try:
            novel_dir = getattr(app, "current_novel_dir", "")
            if not novel_dir:
                return
            ini_path = os.path.join(novel_dir, "novel.ini")
            cfg = configparser.ConfigParser(interpolation=None)
            if os.path.exists(ini_path):
                cfg.read(ini_path, encoding="utf-8")
            if section in cfg and name in cfg[section]:
                cfg.remove_option(section, name)
                with open(ini_path, "w", encoding="utf-8") as f:
                    cfg.write(f)
        except Exception:
            pass

    # 实例化复选列表
    left_list_container = tk.Frame(left_frame)
    left_list_container.grid(row=0, column=0, sticky=tk.NSEW)
    left_list_container.columnconfigure(0, weight=1)
    left_list_container.rowconfigure(0, weight=1)
    app.novel_setting_checks = ScrollCheckList(left_list_container, lambda n: app.novel_setting_details.get(n, ""))

    def persist_item_to_ini(section: str, name: str, content: str):
        try:
            novel_dir = getattr(app, "current_novel_dir", "")
            if not novel_dir:
                messagebox.showwarning("提示", "请先创建或读取小说配置（novel.ini）后再添加。", parent=parent)
                return False
            os.makedirs(novel_dir, exist_ok=True)
            ini_path = os.path.join(novel_dir, "novel.ini")
            cfg = configparser.ConfigParser(interpolation=None)
            if os.path.exists(ini_path):
                cfg.read(ini_path, encoding="utf-8")
            if section not in cfg:
                cfg[section] = {}
            cfg[section][name] = content
            with open(ini_path, "w", encoding="utf-8") as f:
                cfg.write(f)
            return True
        except Exception as e:
            messagebox.showerror("错误", f"写入配置失败: {str(e)}", parent=parent)
            return False

    def create_novel_setting_item():
        res = create_novel_setting_dialog("创建小说设置")
        if res:
            name, content = res
            app.novel_setting_details[name] = content
            app.novel_setting_checked[name] = False
            app.novel_setting_checks.rebuild(app.novel_setting_details, app.novel_setting_checked)
            if persist_item_to_ini("NOVEL_SETTINGS", name, content):
                messagebox.showinfo("成功", "✅ 已保存到 novel.ini 的 [NOVEL_SETTINGS]", parent=parent)

    left_btns = tk.Frame(left_frame)
    left_btns.grid(row=1, column=0, sticky=tk.E, pady=(8, 0))
    tk.Button(left_btns, text="删除", command=lambda: delete_selected_items("NOVEL_SETTINGS", "left"), cursor="hand2").pack(side=tk.RIGHT, padx=(6,0))
    tk.Button(left_btns, text="编辑", command=lambda: edit_selected_item("NOVEL_SETTINGS", "left", "编辑设置"), cursor="hand2").pack(side=tk.RIGHT, padx=(6,0))
    tk.Button(left_btns, text="＋ 创建", command=create_novel_setting_item, cursor="hand2").pack(side=tk.RIGHT)

    # 人物设定列表（放置在左侧）
    right_frame = ttk.LabelFrame(root_frame, text="人物设定列表", padding=10)
    right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
    right_frame.columnconfigure(0, weight=1)
    right_frame.rowconfigure(0, weight=1)

    right_list_container = tk.Frame(right_frame)
    right_list_container.grid(row=0, column=0, sticky=tk.NSEW)
    right_list_container.columnconfigure(0, weight=1)
    right_list_container.rowconfigure(0, weight=1)
    app.character_setting_checks = ScrollCheckList(right_list_container, lambda n: app.character_setting_details.get(n, ""))

    def create_character_setting_item():
        res = create_character_dialog("创建人物设定")
        if res:
            name, content = res
            app.character_setting_details[name] = content
            app.character_setting_checked[name] = False
            app.character_setting_checks.rebuild(app.character_setting_details, app.character_setting_checked)
            if persist_item_to_ini("CHARACTERS", name, content):
                messagebox.showinfo("成功", "✅ 已保存到 novel.ini 的 [CHARACTERS]", parent=parent)

    right_btns = tk.Frame(right_frame)
    right_btns.grid(row=1, column=0, sticky=tk.E, pady=(8, 0))
    tk.Button(right_btns, text="删除", command=lambda: delete_selected_items("CHARACTERS", "right"), cursor="hand2").pack(side=tk.RIGHT, padx=(6,0))
    tk.Button(right_btns, text="编辑", command=lambda: edit_selected_item("CHARACTERS", "right", "编辑人物"), cursor="hand2").pack(side=tk.RIGHT, padx=(6,0))
    tk.Button(right_btns, text="＋ 创建", command=create_character_setting_item, cursor="hand2").pack(side=tk.RIGHT)

    def delete_from_ini(section: str, name: str):
        try:
            novel_dir = getattr(app, "current_novel_dir", "")
            if not novel_dir:
                messagebox.showwarning("提示", "请先创建或读取小说配置（novel.ini）后再操作。", parent=parent)
                return False
            ini_path = os.path.join(novel_dir, "novel.ini")
            cfg = configparser.ConfigParser(interpolation=None)
            if os.path.exists(ini_path):
                cfg.read(ini_path, encoding="utf-8")
            if section not in cfg or name not in cfg[section]:
                return True
            cfg.remove_option(section, name)
            with open(ini_path, "w", encoding="utf-8") as f:
                cfg.write(f)
            return True
        except Exception as e:
            messagebox.showerror("错误", f"更新配置失败: {str(e)}", parent=parent)
            return False

    def delete_selected_items(section: str, side: str):
        try:
            if side == "left":
                selected_name = app.novel_setting_checks.get_selected()
                store = app.novel_setting_details
            else:
                selected_name = app.character_setting_checks.get_selected()
                store = app.character_setting_details
            
            if not selected_name:
                messagebox.showwarning("提示", "请先点击选择要删除的项目（文字会变色）。", parent=parent)
                return
            
            if not messagebox.askyesno("确认删除", f"确定删除项目：{selected_name}？", parent=parent):
                return
            
            # 删除选中的项目
            ok = delete_from_ini(section, selected_name)
            if ok and selected_name in store:
                del store[selected_name]
            
            # 同时删除选中状态记录
            if side == "left":
                if selected_name in app.novel_setting_checked:
                    del app.novel_setting_checked[selected_name]
                delete_selection_entry("NOVEL_SETTINGS_SELECTED", selected_name)
            else:
                if selected_name in app.character_setting_checked:
                    del app.character_setting_checked[selected_name]
                delete_selection_entry("CHARACTERS_SELECTED", selected_name)
            
            # 重建界面
            if side == "left":
                app.novel_setting_checks.rebuild(app.novel_setting_details, app.novel_setting_checked)
            else:
                app.character_setting_checks.rebuild(app.character_setting_details, app.character_setting_checked)
            
            if ok:
                messagebox.showinfo("成功", "✅ 已从列表与配置中删除所选项目。", parent=parent)
        except Exception as e:
            messagebox.showerror("错误", f"删除失败: {str(e)}", parent=parent)

    def edit_selected_item(section: str, side: str, title: str):
        try:
            if side == "left":
                selected_name = app.novel_setting_checks.get_selected()
                store = app.novel_setting_details
            else:
                selected_name = app.character_setting_checks.get_selected()
                store = app.character_setting_details
            
            if not selected_name:
                messagebox.showwarning("提示", "请先点击选择要编辑的项目（文字会变色）。", parent=parent)
                return
            
            old_name = selected_name
            old_content = store.get(old_name, "")
            
            # 根据所属板块选择对话框
            if section == "CHARACTERS":
                res = create_character_dialog(title, old_name, old_content)
                if not res: return
                new_name, new_content = res
            else:
                # 增强的小说设定对话框
                res = create_novel_setting_dialog(title, old_name, old_content)
                if not res: return
                new_name, new_content = res
            # 后续逻辑统一处理保存
            # 如果重命名，先删旧key
            if new_name != old_name:
                if not delete_from_ini(section, old_name):
                    return
            # 写新值
            if not persist_item_to_ini(section, new_name, new_content):
                return
            # 更新内存与列表
            if old_name in store:
                del store[old_name]
            store[new_name] = new_content
            # 搬运勾选状态
            checked = False
            if section == "NOVEL_SETTINGS":
                checked = app.novel_setting_checked.get(old_name, False)
                if old_name in app.novel_setting_checked:
                    del app.novel_setting_checked[old_name]
                app.novel_setting_checked[new_name] = checked
                app.novel_setting_checks.rebuild(app.novel_setting_details, app.novel_setting_checked)
                # 同步 ini 选中状态：删旧写新
                delete_selection_entry("NOVEL_SETTINGS_SELECTED", old_name)
                update_selection_entry("NOVEL_SETTINGS_SELECTED", new_name, checked)
            else:
                checked = app.character_setting_checked.get(old_name, False)
                if old_name in app.character_setting_checked:
                    del app.character_setting_checked[old_name]
                app.character_setting_checked[new_name] = checked
                app.character_setting_checks.rebuild(app.character_setting_details, app.character_setting_checked)
                delete_selection_entry("CHARACTERS_SELECTED", old_name)
                update_selection_entry("CHARACTERS_SELECTED", new_name, checked)
            
            messagebox.showinfo("成功", "✅ 已从新对话框完成保存。", parent=parent)
        except Exception as e:
            messagebox.showerror("错误", f"编辑失败: {str(e)}", parent=parent)

    # 悬浮提示功能已集成在 ScrollCheckList 内部的 _bind_tooltip

