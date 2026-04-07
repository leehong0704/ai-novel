import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import configparser
from services.config_manager import ConfigManager


def create_ai_settings_page(app, parent, default_temperature, default_max_tokens, api_base, model, api_key=""):
    """创建AI设置页面（独立模块）

    参数:
        app: 主应用实例（需要在其上挂载变量，如 temperature_var、max_tokens_var 等）
        parent: 承载该页面的父容器
        default_temperature: 默认的Temperature值
        default_max_tokens: 默认的最大tokens
        api_base: API地址用于显示
        model: 模型名称用于显示
        api_key: 当前API Key初始值
    """
    
    # 主容器 - 使用PanedWindow分割左右两部分
    main_paned = tk.PanedWindow(parent, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5)
    main_paned.pack(fill=tk.BOTH, expand=True)
    
    # ========== 左侧：API配置列表 ==========
    left_frame = tk.Frame(main_paned, padx=10, pady=10)
    main_paned.add(left_frame, width=300)
    
    # 标题
    tk.Label(left_frame, text="API 配置列表", font=("Microsoft YaHei", 12, "bold")).pack(pady=(0, 10))
    
    # API列表框架
    list_frame = tk.Frame(left_frame)
    list_frame.pack(fill=tk.BOTH, expand=True)
    
    # 创建列表框和滚动条
    scrollbar = tk.Scrollbar(list_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    api_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Microsoft YaHei", 10), height=15)
    api_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=api_listbox.yview)
    
    # 存储API配置数据
    app.api_configs = []
    app.current_api_index = 0
    
    # 按钮框架
    btn_frame = tk.Frame(left_frame)
    btn_frame.pack(fill=tk.X, pady=(10, 0))
    
    def refresh_api_list():
        """刷新API列表显示"""
        api_listbox.delete(0, tk.END)
        
        # 重新加载配置
        config = ConfigManager.load_config()
        if config:
            app.api_configs = config['available_apis']
            current_api_name = config['current_api']
            
            # 填充列表
            for i, api in enumerate(app.api_configs):
                prefix = "✓ " if api['name'] == current_api_name else "  "
                api_listbox.insert(tk.END, f"{prefix}{api['name']}")
                if api['name'] == current_api_name:
                    app.current_api_index = i
                    api_listbox.selection_set(i)
    
    def on_api_selected(event):
        """选择API时加载其配置到右侧"""
        selection = api_listbox.curselection()
        if selection:
            index = selection[0]
            app.current_api_index = index
            api = app.api_configs[index]
            
            # 更新右侧显示
            app.api_name_var.set(api['name'])
            app.original_api_name = api['name']  # 保存原始名称
            app.api_base_var.set(api['api_base'])
            app.model_var.set(api['model'])
            app.api_key_var.set(api['api_key'])
            
            # 更新temperature和max_tokens（如果有的话，否则使用默认值）
            if 'temperature' in api:
                app.temperature_var.set(float(api['temperature']))
            if 'max_tokens' in api:
                app.max_tokens_var.set(int(api['max_tokens']))
            if 'timeout' in api:
                app.timeout_var.set(int(api['timeout']))
    
    api_listbox.bind('<<ListboxSelect>>', on_api_selected)
    
    def set_current_api():
        """设置当前选中的API为活动API"""
        selection = api_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个API配置！")
            return
        
        index = selection[0]
        api = app.api_configs[index]
        
        # 保存到配置文件
        if ConfigManager.save_config_value('APP', 'current_api', api['name']):
            messagebox.showinfo("成功", f"✅ 已将 '{api['name']}' 设置为当前使用的API")
            refresh_api_list()
            
            # 更新AI客户端配置
            if hasattr(app, 'ai_client'):
                app.ai_client.update_config(
                    api_key=api['api_key'],
                    api_base=api['api_base'],
                    model=api['model'],
                    timeout=api.get('timeout', 300)
                )
        else:
            messagebox.showerror("错误", "设置失败！")
    
    def add_new_api():
        """添加新的API配置"""
        # 弹出对话框输入API名称
        api_name = simpledialog.askstring("新建API配置", "请输入API配置名称（如：DEEPSEEK, OPENAI等）:")
        if not api_name:
            return
        
        api_name = api_name.strip().upper()
        
        # 检查是否已存在
        for api in app.api_configs:
            if api['name'] == api_name:
                messagebox.showerror("错误", f"API配置 '{api_name}' 已存在！")
                return
        
        # 添加新配置（使用默认值）
        if ConfigManager.save_api_config(
            api_name,
            "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "https://api.example.com/v1",
            "model-name",
            0.7,  # 默认temperature
            4000,  # 默认max_tokens
            300   # 默认timeout
        ):
            messagebox.showinfo("成功", f"✅ 已创建API配置 '{api_name}'\n请在右侧编辑其详细信息")
            refresh_api_list()
            
            # 选中新添加的项
            for i, api in enumerate(app.api_configs):
                if api['name'] == api_name:
                    api_listbox.selection_clear(0, tk.END)
                    api_listbox.selection_set(i)
                    on_api_selected(None)
                    break
        else:
            messagebox.showerror("错误", "创建失败！")
    
    def delete_api():
        """删除选中的API配置"""
        selection = api_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要删除的API配置！")
            return
        
        index = selection[0]
        api = app.api_configs[index]
        
        # 检查是否是当前使用的API
        config = ConfigManager.load_config()
        if config and config['current_api'] == api['name']:
            messagebox.showerror("错误", f"无法删除当前正在使用的API配置 '{api['name']}'！\\n请先切换到其他API。")
            return
        
        # 确认删除
        if messagebox.askyesno("确认删除", f"确定要删除API配置 '{api['name']}' 吗？"):
            if ConfigManager.delete_api_config(api['name']):
                messagebox.showinfo("成功", f"✅ 已删除API配置 '{api['name']}'")
                refresh_api_list()
            else:
                messagebox.showerror("错误", "删除失败！")
    
    # 按钮
    tk.Button(btn_frame, text="✓ 设为当前", command=set_current_api, bg="#28a745", fg="white", cursor="hand2").pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
    tk.Button(btn_frame, text="➕ 新建", command=add_new_api, bg="#007bff", fg="white", cursor="hand2").pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
    tk.Button(btn_frame, text="🗑 删除", command=delete_api, bg="#dc3545", fg="white", cursor="hand2").pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
    
    # ========== 右侧：API配置详情 ==========
    right_frame = tk.Frame(main_paned, padx=20, pady=10)
    main_paned.add(right_frame)
    
    # 合并后的设置框架
    settings_frame = ttk.LabelFrame(right_frame, text="API 配置详情", padding=20)
    settings_frame.pack(fill=tk.BOTH, expand=True)

    row = 0  # 通用行游标

    # API 名称
    tk.Label(settings_frame, text="配置名称:", font=("Microsoft YaHei", 10)).grid(
        row=row, column=0, sticky=tk.W, pady=10, padx=10
    )
    app.api_name_var = tk.StringVar(value="")
    app.original_api_name = ""  # 存储原始名称，用于重命名时比较
    api_name_entry = tk.Entry(settings_frame, textvariable=app.api_name_var, font=("Microsoft YaHei", 10), width=30)
    api_name_entry.grid(row=row, column=1, sticky=tk.W, pady=10, padx=10)
    tk.Label(settings_frame, text="（修改后保存即可重命名）", font=("Microsoft YaHei", 8), fg="gray").grid(
        row=row, column=2, sticky=tk.W, padx=5
    )
    row += 1

    # API 地址
    tk.Label(settings_frame, text="API 地址:", font=("Microsoft YaHei", 10)).grid(
        row=row, column=0, sticky=tk.W, pady=10, padx=10
    )
    app.api_base_var = tk.StringVar(value=api_base)
    api_base_entry = tk.Entry(settings_frame, textvariable=app.api_base_var, font=("Microsoft YaHei", 10), width=50)
    api_base_entry.grid(row=row, column=1, sticky=tk.EW, pady=10, padx=10, columnspan=2)
    row += 1

    # 模型
    tk.Label(settings_frame, text="模型 (Model):", font=("Microsoft YaHei", 10)).grid(
        row=row, column=0, sticky=tk.W, pady=10, padx=10
    )
    app.model_var = tk.StringVar(value=model)
    model_entry = tk.Entry(settings_frame, textvariable=app.model_var, font=("Microsoft YaHei", 10), width=30)
    model_entry.grid(row=row, column=1, sticky=tk.W, pady=10, padx=10)
    row += 1

    # API Key
    tk.Label(settings_frame, text="API Key:", font=("Microsoft YaHei", 10)).grid(
        row=row, column=0, sticky=tk.W, pady=10, padx=10
    )
    app.api_key_var = tk.StringVar(value=api_key)
    api_key_entry = tk.Entry(settings_frame, textvariable=app.api_key_var, font=("Microsoft YaHei", 10), width=50, show="*")
    api_key_entry.grid(row=row, column=1, sticky=tk.EW, pady=10, padx=10)
    
    # 按钮框架（显示/隐藏 + 测试连接）
    key_btn_frame = tk.Frame(settings_frame)
    key_btn_frame.grid(row=row, column=2, sticky=tk.W, pady=10, padx=(0,10))
    
    def toggle_api_key():
        api_key_entry.config(show="" if api_key_entry.cget("show") == "*" else "*")
        toggle_btn.config(text="隐藏" if api_key_entry.cget("show") == "" else "显示")
    
    toggle_btn = tk.Button(key_btn_frame, text="显示", command=toggle_api_key, width=6)
    toggle_btn.pack(side=tk.LEFT, padx=2)
    
    def test_api_connection():
        """测试API连接"""
        import requests
        import json
        from tkinter import messagebox
        import threading
        
        api_name = app.api_name_var.get().strip()
        api_key = app.api_key_var.get().strip()
        api_base = app.api_base_var.get().strip()
        model = app.model_var.get().strip()
        
        if not api_name:
            messagebox.showwarning("提示", "请先选择一个API配置！")
            return
        
        if not api_key or api_key == "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
            messagebox.showwarning("提示", "请先填写有效的API Key！")
            return
        
        if not api_base:
            messagebox.showwarning("提示", "请先填写API地址！")
            return
        
        if not model:
            messagebox.showwarning("提示", "请先填写模型名称！")
            return
        
        # 禁用测试按钮
        test_btn.config(state=tk.DISABLED, text="测试中...")
        
        def test_thread():
            try:
                # 构建测试请求
                api_base_clean = api_base.rstrip('/')
                url = f"{api_base_clean}/chat/completions"
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
                
                data = {
                    "model": model,
                    "messages": [
                        {"role": "user", "content": "Hello"}
                    ],
                    "max_tokens": 255
                }
                
                # 获取超时时间配置
                timeout = app.timeout_var.get() if hasattr(app, 'timeout_var') else 30
                
                print(f"[测试] 正在测试API连接...")
                print(f"[测试] URL: {url}")
                print(f"[测试] Model: {model}")
                print(f"[测试] Timeout: {timeout}秒")
                
                # 发送测试请求
                response = requests.post(
                    url,
                    headers=headers,
                    data=json.dumps(data),
                    timeout=timeout
                )
                
                print(f"[测试] 响应状态码: {response.status_code}")
                
                # 在主线程中显示结果
                def show_result():
                    test_btn.config(state=tk.NORMAL, text="🔍 测试")
                    
                    if response.status_code == 200:
                        result = response.json()
                        if "choices" in result or "candidates" in result:
                            messagebox.showinfo(
                                "测试成功", 
                                f"✅ API连接测试成功！\n\n"
                                f"配置名称: {api_name}\n"
                                f"API地址: {api_base}\n"
                                f"模型: {model}\n"
                                f"状态: 正常"
                            )
                        else:
                            messagebox.showwarning(
                                "测试警告",
                                f"⚠️ API响应格式异常\n\n"
                                f"状态码: {response.status_code}\n"
                                f"响应: {str(result)[:200]}"
                            )
                    else:
                        error_msg = f"❌ API连接失败\n\n状态码: {response.status_code}"
                        try:
                            error_detail = response.json()
                            error_msg += f"\n错误详情: {error_detail}"
                        except:
                            error_msg += f"\n响应内容: {response.text[:200]}"
                        
                        messagebox.showerror("测试失败", error_msg)
                
                app.root.after(0, show_result)
                
            except requests.exceptions.Timeout:
                def show_timeout():
                    test_btn.config(state=tk.NORMAL, text="🔍 测试")
                    messagebox.showerror(
                        "测试失败",
                        "❌ 连接超时\n\n"
                        "请检查：\n"
                        "1. API地址是否正确\n"
                        "2. 网络连接是否正常\n"
                        "3. 是否需要配置代理"
                    )
                app.root.after(0, show_timeout)
                
            except requests.exceptions.RequestException as e:
                def show_error():
                    test_btn.config(state=tk.NORMAL, text="🔍 测试")
                    messagebox.showerror(
                        "测试失败",
                        f"❌ 网络请求错误\n\n{str(e)}"
                    )
                app.root.after(0, show_error)
                
            except Exception as e:
                def show_exception():
                    test_btn.config(state=tk.NORMAL, text="🔍 测试")
                    messagebox.showerror(
                        "测试失败",
                        f"❌ 发生错误\n\n{str(e)}"
                    )
                app.root.after(0, show_exception)
        
        # 在后台线程中执行测试
        thread = threading.Thread(target=test_thread, daemon=True)
        thread.start()
    
    test_btn = tk.Button(key_btn_frame, text="🔍 测试", command=test_api_connection, width=6, bg="#17a2b8", fg="white", cursor="hand2")
    test_btn.pack(side=tk.LEFT, padx=2)
    
    row += 1

    ttk.Separator(settings_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=(5, 15))
    row += 1

    # 创造性（Temperature）
    tk.Label(settings_frame, text="创造性 (Temperature):", font=("Microsoft YaHei", 10)).grid(
        row=row, column=0, sticky=tk.W, pady=15, padx=10
    )
    app.temperature_var = tk.DoubleVar(value=default_temperature)
    temperature_scale = tk.Scale(
        settings_frame,
        from_=0.0,
        to=1.0,
        resolution=0.1,
        orient=tk.HORIZONTAL,
        variable=app.temperature_var,
        length=400
    )
    temperature_scale.grid(row=row, column=1, sticky=tk.EW, pady=15, padx=10)
    app.temperature_label = tk.Label(
        settings_frame,
        text=f"{default_temperature:.1f}",
        font=("Microsoft YaHei", 10, "bold"),
        fg="#1f77b4"
    )
    app.temperature_label.grid(row=row, column=2, padx=10)
    temperature_scale.config(command=lambda v: app.temperature_label.config(text=f"{float(v):.1f}"))

    # 说明
    temp_info = tk.Label(
        settings_frame,
        text="值越高，生成内容越有创造性（0.0-1.0）",
        font=("Microsoft YaHei", 9),
        fg="gray"
    )
    temp_info.grid(row=row+1, column=0, columnspan=3, sticky=tk.W, padx=10, pady=(0, 10))

    # 最大长度
    row += 2
    tk.Label(settings_frame, text="最大生成长度 (Max Tokens):", font=("Microsoft YaHei", 10)).grid(
        row=row, column=0, sticky=tk.W, pady=15, padx=10
    )
    app.max_tokens_var = tk.IntVar(value=default_max_tokens)
    max_tokens_spin = tk.Spinbox(
        settings_frame,
        from_=1000,
        to=10000,
        increment=500,
        textvariable=app.max_tokens_var,
        width=20,
        font=("Microsoft YaHei", 10)
    )
    max_tokens_spin.grid(row=row, column=1, sticky=tk.W, pady=15, padx=10)

    # 说明
    tokens_info = tk.Label(
        settings_frame,
        text="控制生成内容的最大长度（1000-10000）",
        font=("Microsoft YaHei", 9),
        fg="gray"
    )
    tokens_info.grid(row=row+1, column=0, columnspan=3, sticky=tk.W, padx=10, pady=(0, 10))

    # 超时时间
    row += 2
    tk.Label(settings_frame, text="请求超时时间 (Timeout):", font=("Microsoft YaHei", 10)).grid(
        row=row, column=0, sticky=tk.W, pady=15, padx=10
    )
    app.timeout_var = tk.IntVar(value=300)
    timeout_spin = tk.Spinbox(
        settings_frame,
        from_=30,
        to=600,
        increment=30,
        textvariable=app.timeout_var,
        width=20,
        font=("Microsoft YaHei", 10)
    )
    timeout_spin.grid(row=row, column=1, sticky=tk.W, pady=15, padx=10)
    tk.Label(settings_frame, text="秒", font=("Microsoft YaHei", 10)).grid(
        row=row, column=2, sticky=tk.W, padx=5
    )

    # 说明
    timeout_info = tk.Label(
        settings_frame,
        text="API请求超时时间，建议300秒（30-600秒）",
        font=("Microsoft YaHei", 9),
        fg="gray"
    )
    timeout_info.grid(row=row+1, column=0, columnspan=3, sticky=tk.W, padx=10, pady=(0, 10))

    # 保存区
    def save_current_api_config():
        """保存当前编辑的API配置"""
        api_name = app.api_name_var.get().strip().upper()  # 转换为大写
        original_name = getattr(app, 'original_api_name', '')
        
        if not api_name:
            messagebox.showwarning("提示", "配置名称不能为空！")
            return
        
        # 检查是否使用了保留名称
        if api_name in ['DEFAULT', 'APP']:
            messagebox.showerror("错误", f"不能使用保留名称 '{api_name}'！\n请使用其他名称。")
            return
        
        try:
            # 检查是否需要重命名
            if original_name and api_name != original_name:
                # 需要重命名
                if messagebox.askyesno("确认重命名", 
                    f"确定要将API配置从 '{original_name}' 重命名为 '{api_name}' 吗？"):
                    
                    if ConfigManager.rename_api_config(original_name, api_name):
                        # 重命名成功，更新原始名称
                        app.original_api_name = api_name
                        messagebox.showinfo("成功", f"✅ 已将API配置重命名为 '{api_name}'")
                    else:
                        messagebox.showerror("错误", "重命名失败！\n请检查新名称是否已存在。")
                        return
                else:
                    # 用户取消重命名，恢复原名称
                    app.api_name_var.set(original_name)
                    return
            
            # 保存API配置（使用当前名称）
            if ConfigManager.save_api_config(
                api_name,
                app.api_key_var.get().strip(),
                app.api_base_var.get().strip(),
                app.model_var.get().strip(),
                app.temperature_var.get(),
                app.max_tokens_var.get(),
                app.timeout_var.get()
            ):
                # 不需要再保存到DEFAULT section了
                # ConfigManager.save_config_value('DEFAULT', 'temperature', str(app.temperature_var.get()))
                # ConfigManager.save_config_value('DEFAULT', 'max_tokens', str(app.max_tokens_var.get()))
                
                messagebox.showinfo("成功", f"✅ 已保存API配置 '{api_name}'\n提示：更改已即时生效。")
                refresh_api_list()
                
                # 重新选中当前API
                for i, api in enumerate(app.api_configs):
                    if api['name'] == api_name:
                        api_listbox.selection_clear(0, tk.END)
                        api_listbox.selection_set(i)
                        break
            else:
                messagebox.showerror("错误", "保存失败！")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")

    # 底部保存按钮区域（居中、靠下）
    footer_frame = tk.Frame(right_frame)
    footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
    save_btn = tk.Button(footer_frame, text="💾 保存当前配置", command=save_current_api_config, bg="#28a745", fg="white", cursor="hand2", height=2)
    save_btn.pack(pady=10)

    settings_frame.columnconfigure(1, weight=1)
    
    # 初始加载API列表
    refresh_api_list()
    
    # 如果有API配置，选中第一个
    if app.api_configs:
        api_listbox.selection_set(app.current_api_index)
        on_api_selected(None)
