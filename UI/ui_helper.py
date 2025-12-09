"""
UI辅助工具类
负责处理通用的UI操作，如加载动画、占位符处理、字数统计等
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import math
import traceback

class UIHelper:
    """UI辅助工具类"""
    
    def __init__(self, app):
        """
        初始化UI辅助工具
        Args:
            app: NovelGeneratorApp实例
        """
        self.app = app
        
        # 加载动画相关状态
        self.loading_window = None
        self.loading_animation_id = None
        self.loading_frame_count = 0
        self.loading_canvas = None

    def clear_placeholder(self, event):
        """清除提示文本的占位符"""
        if not hasattr(self.app, "prompt_text"):
            return
        content = self.app.prompt_text.get("1.0", tk.END).strip()
        if "请输入你的创作想法" in content:
            self.app.prompt_text.delete("1.0", tk.END)
    
    def clear_entry_placeholder(self, entry, placeholder):
        """清除Entry的占位符"""
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg="black")
    
    def set_entry_placeholder(self, entry, placeholder):
        """设置Entry的占位符"""
        if not entry.get():
            entry.insert(0, placeholder)
            entry.config(fg="gray")
    
    def update_word_count(self, event=None):
        """更新字数统计"""
        if not hasattr(self.app, "content_text") or not hasattr(self.app, "word_count_label"):
            return
        content = self.app.content_text.get("1.0", tk.END)
        word_count = len(content.strip())
        self.app.word_count_label.config(text=f"当前字数: {word_count} 字")
    
    def update_prompt_char_count(self, event=None):
        """更新创作提示字数统计"""
        if not hasattr(self.app, "prompt_text") or not hasattr(self.app, "prompt_char_count_label"):
            return
        content = self.app.prompt_text.get("1.0", tk.END).strip()
        # 排除占位符文本
        if "请输入你的创作想法" in content:
            char_count = 0
        else:
            char_count = len(content)
        self.app.prompt_char_count_label.config(text=f"当前字数: {char_count} 字")
    
    def show_loading_animation(self):
        """显示加载动画并锁定界面"""
        try:
            # 创建加载窗口
            self.loading_window = tk.Toplevel(self.app.root)
            self.loading_window.title("生成中...")
            self.loading_window.transient(self.app.root)
            self.loading_window.grab_set()
            self.loading_window.resizable(False, False)
            
            # 设置窗口大小和位置（居中）
            window_width = 300
            window_height = 150
            screen_width = self.loading_window.winfo_screenwidth()
            screen_height = self.loading_window.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            self.loading_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # 移除窗口边框装饰（可选）
            # self.loading_window.overrideredirect(True)
            
            # 创建主框架
            main_frame = tk.Frame(self.loading_window, bg="white", padx=20, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # 创建Canvas用于绘制转圈动画
            canvas_size = 60
            self.loading_canvas = tk.Canvas(
                main_frame,
                width=canvas_size,
                height=canvas_size,
                bg="white",
                highlightthickness=0
            )
            self.loading_canvas.pack(pady=(0, 10))
            
            # 加载文字
            loading_label = tk.Label(
                main_frame,
                text="AI正在生成内容，请稍候...",
                font=("Microsoft YaHei", 11),
                bg="white",
                fg="#333333"
            )
            loading_label.pack()
            
            # 禁用主窗口的所有控件
            self._disable_all_widgets(self.app.root)
            
            # 开始动画
            self.loading_frame_count = 0
            self._animate_loading()
            
        except Exception as e:
            print(f"[错误] 显示加载动画失败: {e}")
            traceback.print_exc()
    
    def _animate_loading(self):
        """加载动画循环"""
        try:
            if self.loading_window is None or not self.loading_window.winfo_exists():
                return
            
            canvas = self.loading_canvas
            canvas.delete("all")
            
            # 绘制转圈动画（8个点旋转）
            center_x = 30
            center_y = 30
            radius = 20
            num_dots = 8
            angle_step = 360 / num_dots
            
            # 计算旋转角度
            base_angle = (self.loading_frame_count * 15) % 360
            
            for i in range(num_dots):
                angle = math.radians(base_angle + i * angle_step)
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                
                # 点的透明度（距离起始点越远越淡）
                alpha = 1.0 - (i / num_dots) * 0.7
                gray_value = int(100 + (155 * alpha))
                color = f"#{gray_value:02x}{gray_value:02x}{gray_value:02x}"
                
                canvas.create_oval(x-4, y-4, x+4, y+4, fill=color, outline="")
            
            self.loading_frame_count += 1
            
            # 继续动画
            self.loading_animation_id = self.app.root.after(50, self._animate_loading)
            
        except Exception as e:
            print(f"[错误] 动画循环失败: {e}")
    
    def _disable_all_widgets(self, parent):
        """递归禁用所有控件（但保持内容区域可查看）"""
        try:
            for widget in parent.winfo_children():
                try:
                    if isinstance(widget, tk.Button):
                        widget.config(state=tk.DISABLED)
                    elif isinstance(widget, tk.Entry):
                        widget.config(state=tk.DISABLED)
                    elif isinstance(widget, tk.Listbox):
                        widget.config(state=tk.DISABLED)
                    elif isinstance(widget, ttk.Combobox):
                        widget.config(state=tk.DISABLED)
                    elif isinstance(widget, (tk.Text, scrolledtext.ScrolledText)):
                        # 文本区域保持可查看，但禁用编辑
                        widget.config(state=tk.DISABLED)
                    elif isinstance(widget, tk.Menu):
                        continue
                    else:
                        # 递归处理子控件
                        self._disable_all_widgets(widget)
                except Exception:
                    pass
        except Exception:
            pass
    
    def _enable_all_widgets(self, parent):
        """递归启用所有控件"""
        try:
            for widget in parent.winfo_children():
                try:
                    if isinstance(widget, (tk.Button, tk.Entry, tk.Text, scrolledtext.ScrolledText, tk.Listbox, ttk.Combobox)):
                        # 恢复按钮状态（除了生成按钮，它会在update_content中恢复）
                        if hasattr(self.app, "generate_btn") and widget != self.app.generate_btn:
                            widget.config(state=tk.NORMAL)
                        elif not hasattr(self.app, "generate_btn"):
                            widget.config(state=tk.NORMAL)
                    elif isinstance(widget, tk.Menu):
                        continue
                    else:
                        # 递归处理子控件
                        self._enable_all_widgets(widget)
                except Exception:
                    pass
        except Exception:
            pass
    
    def hide_loading_animation(self):
        """隐藏加载动画并解锁界面"""
        try:
            # 停止动画
            if self.loading_animation_id:
                self.app.root.after_cancel(self.loading_animation_id)
                self.loading_animation_id = None
            
            # 关闭加载窗口
            if self.loading_window and self.loading_window.winfo_exists():
                self.loading_window.destroy()
            self.loading_window = None
            
            # 启用主窗口的所有控件
            self._enable_all_widgets(self.app.root)
            
            # 确保内容编辑器可用
            if hasattr(self.app, "content_text"):
                self.app.content_text.config(state=tk.NORMAL)
            if hasattr(self.app, "prompt_text"):
                self.app.prompt_text.config(state=tk.NORMAL)
            
        except Exception as e:
            print(f"[错误] 隐藏加载动画失败: {e}")
            traceback.print_exc()
