"""
AI小说生成器 - 主程序
基于Windows Form的桌面应用程序
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import requests
import json
import configparser
from datetime import datetime
import threading
import traceback
import sys
import re
import math

# UI模块
from UI.ai_settings import create_ai_settings_page as external_create_ai_settings_page
from UI.novel_settings import create_novel_settings_page as external_create_novel_settings_page
from UI.novel_profile import create_novel_profile_page as external_create_novel_profile_page
from UI.chapter_generate import create_chapter_generate_page as external_create_chapter_generate_page

# 业务模块
from AI.ai_client import AIClient
from services.config_manager import ConfigManager
from services.novel_service import NovelService
from services.generation_service import GenerationService
from UI.ui_helper import UIHelper

# 读取配置文件
# 加载配置
config = ConfigManager.load_config()
if config is None:
    # 在打包为无控制台的 GUI 模式下，input 会导致 “lost sys.stdin”。
    # 使用消息框提示并直接退出。
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("配置错误", "程序无法启动，请检查配置文件！")
        root.destroy()
    except Exception:
        # 作为兜底在不可用时打印到 stderr
        print("程序无法启动，请检查配置文件！", file=sys.stderr)
    sys.exit(1)

DEEPSEEK_API_KEY = config['api_key']
DEEPSEEK_API_BASE = config['api_base']
DEEPSEEK_MODEL = config['model']
DEFAULT_TEMPERATURE = config['temperature']
DEFAULT_MAX_TOKENS = config['max_tokens']
DEFAULT_TIMEOUT = config.get('timeout', 300)
CURRENT_API = config['current_api']
AVAILABLE_APIS = config['available_apis']



class NovelGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI小说生成器")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # 数据存储
        self.novel_title = ""
        self.novel_content = ""
        self.chapter_list = []
        
        # 加载动画相关状态已移至 UIHelper

        
        # 初始化AI客户端
        self.ai_client = AIClient(
            api_key=DEEPSEEK_API_KEY,
            api_base=DEEPSEEK_API_BASE,
            model=DEEPSEEK_MODEL,
            timeout=DEFAULT_TIMEOUT
        )
        
        # 初始化业务服务
        self.novel_service = NovelService(self)
        
        default_config = {
            'api_key': DEEPSEEK_API_KEY,
            'api_base': DEEPSEEK_API_BASE,
            'model': DEEPSEEK_MODEL
        }
        self.generation_service = GenerationService(self, default_config)
        
        # 初始化UI辅助工具
        self.ui_helper = UIHelper(self)
        
        # 创建界面
        self.create_widgets()
        
        # 设置窗口关闭协议
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 尝试自动加载上次打开的小说
        try:
            cfg = configparser.ConfigParser()
            cfg_path = os.path.join("config", "config.ini")
            if os.path.exists(cfg_path):
                cfg.read(cfg_path, encoding='utf-8')
                if "APP" in cfg and "last_novel" in cfg["APP"]:
                    last_novel_path = cfg["APP"]["last_novel"]
                    if os.path.exists(last_novel_path):
                        # 延迟加载以确保界面就绪
                        self.root.after(200, lambda: self.load_novel_config(last_novel_path))
        except Exception as e:
            print(f"自动加载失败: {e}")
        
    def create_widgets(self):
        """创建界面组件"""
        # 主标题
        title_frame = tk.Frame(self.root, bg="#1f77b4", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="📚 AI小说生成器", 
            font=("Microsoft YaHei", 20, "bold"),
            bg="#1f77b4",
            fg="white"
        )
        title_label.pack(pady=15)
        
        # 创建标签页容器
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.notebook = notebook
        
        # ========== 页面1: AI设置 ==========
        ai_settings_frame = tk.Frame(notebook, padx=20, pady=20)
        notebook.add(ai_settings_frame, text="🤖 AI设置")
        external_create_ai_settings_page(
            self,
            ai_settings_frame,
            DEFAULT_TEMPERATURE,
            DEFAULT_MAX_TOKENS,
            DEEPSEEK_API_BASE,
            DEEPSEEK_MODEL,
            DEEPSEEK_API_KEY
        )
        
        # ========== 页面2: 小说设置 ==========
        novel_settings_frame = tk.Frame(notebook, padx=20, pady=20)
        notebook.add(novel_settings_frame, text="📖 小说设置")
        external_create_novel_settings_page(self, novel_settings_frame)
        
        # ========== 新页面: 小说设定 ==========
        novel_profile_frame = tk.Frame(notebook, padx=20, pady=20)
        notebook.add(novel_profile_frame, text="🧩 小说设定")
        external_create_novel_profile_page(self, novel_profile_frame)
        self.novel_profile_frame = novel_profile_frame

        # ========== 页面3: 章节生成 ==========
        chapter_generate_frame = tk.Frame(notebook, padx=20, pady=20)
        notebook.add(chapter_generate_frame, text="✍️ 章节生成")
        self.create_chapter_generate_page(chapter_generate_frame)
        self.chapter_generate_frame = chapter_generate_frame

        # 初始根据是否存在小说配置，控制可访问性
        self.update_tab_access()
    
    def create_ai_settings_page(self, parent):
        """保留方法签名以兼容，但委托到外部模块"""
        external_create_ai_settings_page(
            self,
            parent,
            DEFAULT_TEMPERATURE,
            DEFAULT_MAX_TOKENS,
            DEEPSEEK_API_BASE,
            DEEPSEEK_MODEL
        )
    
    def create_novel_settings_page(self, parent):
        """保留方法签名以兼容，但委托到外部模块"""
        external_create_novel_settings_page(self, parent)
    
    def create_chapter_generate_page(self, parent):
        """保留方法签名以兼容，但委托到外部模块"""
        external_create_chapter_generate_page(self, parent)
        
    def clear_placeholder(self, event):
        """清除提示文本的占位符"""
        self.ui_helper.clear_placeholder(event)
    
    def clear_entry_placeholder(self, entry, placeholder):
        """清除Entry的占位符"""
        self.ui_helper.clear_entry_placeholder(entry, placeholder)
    
    def set_entry_placeholder(self, entry, placeholder):
        """设置Entry的占位符"""
        self.ui_helper.set_entry_placeholder(entry, placeholder)
    
    def update_word_count(self, event=None):
        """更新字数统计"""
        self.ui_helper.update_word_count(event)
    
    def update_prompt_char_count(self, event=None):
        """更新创作提示字数统计"""
        self.ui_helper.update_prompt_char_count(event)
    
    def show_loading_animation(self):
        """显示加载动画并锁定界面"""
        self.ui_helper.show_loading_animation()
    
    # _animate_loading, _disable_all_widgets, _enable_all_widgets 已移至 UIHelper
    
    def hide_loading_animation(self):
        """隐藏加载动画并解锁界面"""
        self.ui_helper.hide_loading_animation()
    
    def generate_novel(self, prompt, novel_type, writing_style, temperature, max_tokens):
        """使用AI客户端生成小说内容"""
        return self.generation_service.generate_novel(prompt, novel_type, writing_style, temperature, max_tokens)
        
    def generate_content(self):
        """生成内容（在后台线程中执行）"""
        self.generation_service.generate_content()

    def continue_content(self):
        """续写小说（独立逻辑）"""
        self.generation_service.continue_content()

    def has_novel_config(self):
        """是否已选择并存在小说配置 novel.ini"""
        try:
            novel_dir = getattr(self, "current_novel_dir", "")
            if not novel_dir:
                return False
            return os.path.exists(os.path.join(novel_dir, "novel.ini"))
        except Exception:
            return False

    def update_tab_access(self):
        """根据是否存在小说配置，启用/禁用“小说设定”“章节生成”页"""
        if not hasattr(self, "notebook"):
            return
        has_cfg = self.has_novel_config()
        try:
            if hasattr(self, "novel_profile_frame"):
                self.notebook.tab(self.novel_profile_frame, state=("normal" if has_cfg else "disabled"))
            if hasattr(self, "chapter_generate_frame"):
                self.notebook.tab(self.chapter_generate_frame, state=("normal" if has_cfg else "disabled"))
            # 如果当前在被禁用的页面上，切回首页
            try:
                current = self.notebook.select()
                if not has_cfg and current in (
                    str(self.novel_profile_frame),
                    str(self.chapter_generate_frame),
                ):
                    # 切换到第一个标签
                    self.notebook.select(0)
            except Exception:
                pass
        except Exception as e:
            print(f"[调试] 更新标签可访问性失败: {e}")
    
    # _post_generation_cleanup, _on_generate_success, _on_continue_success 已移至 GenerationService

    
    def refresh_chapter_listbox(self):
        """刷新章节列表显示"""
        self.novel_service.refresh_chapter_listbox()
    
    # def _strip_chapter_prefix(self, title_text): -> moved to prompt_builder
    # def _format_chapter_display(self, index, stored_title): -> moved to prompt_builder
    
    def add_new_chapter_from_editor(self):
        """将当前编辑器内容作为新章节，提示输入标题"""
        self.novel_service.add_new_chapter_from_editor()
    
    def rename_selected_chapter(self):
        """重命名所选章节标题"""
        self.novel_service.rename_selected_chapter()
    
    def insert_chapter_at_selection(self):
        """将当前编辑器内容插入到所选章节位置之前"""
        self.novel_service.insert_chapter_at_selection()
    
    def load_selected_chapter(self):
        """载入所选章节到编辑器"""
        self.novel_service.load_selected_chapter()
    
    def has_unsaved_changes(self):
        """检查当前章节是否有未保存的更改"""
        return self.novel_service.has_unsaved_changes()
    
    def on_chapter_selected(self, event=None):
        """列表选择变化时，自动同步创作提示与生成内容"""
        print(f"[调试] main.py on_chapter_selected 被调用")
        self.novel_service.on_chapter_selected(event)
    
    def save_current_chapter(self):
        """将当前编辑器中的提示与内容保存到当前选中的章节，并写入小说文件"""
        self.novel_service.save_current_chapter()
    
    def on_tab_changed(self, event=None):
        """切换标签页时，自动保存当前章节内容与提示"""
        self.novel_service.save_current_chapter()
    
    def delete_selected_chapter(self):
        """删除列表中选定的章节"""
        self.novel_service.delete_selected_chapter()

    # _persist_chapters_to_novel 已移至 NovelService

    
    def save_novel(self):
        """保存小说内容"""
        self.novel_service.save_novel()
    
    def clear_content(self):
        """清空生成内容"""
        self.novel_service.clear_content()

    def create_new_novel(self):
        """弹出创建小说对话框：选择目录并创建小说配置"""
        self.novel_service.create_new_novel()

    def load_novel(self):
        """读取已保存的小说文本并加载到编辑器"""
        self.novel_service.load_novel()

    def save_novel_config(self):
        """保存小说基础信息到当前小说目录的 novel.ini"""
        self.novel_service.save_novel_config()

    def export_novel_to_txt(self):
        """导出小说到TXT文件（包含标题和所有章节）"""
        self.novel_service.export_novel_to_txt()

    def load_novel_config(self, file_path=None):
        """读取 novel.ini 并填充界面，文件选择器仅限 *.ini"""
        self.novel_service.load_novel_config(file_path)
    
    def preserve_chapter_selection(self):
        """保持章节列表的选中状态，防止在编辑文本时丢失"""
        try:
            # 如果有当前章节索引，确保列表框中保持选中状态
            if hasattr(self, 'current_chapter_index') and self.current_chapter_index is not None:
                if hasattr(self, 'chapter_listbox'):
                    sel = self.chapter_listbox.curselection()
                    # 如果选择状态丢失，恢复它
                    if not sel or sel[0] != self.current_chapter_index:
                        self.chapter_listbox.selection_clear(0, tk.END)
                        if 0 <= self.current_chapter_index < self.chapter_listbox.size():
                            self.chapter_listbox.selection_set(self.current_chapter_index)
                            self.chapter_listbox.see(self.current_chapter_index)
        except Exception as e:
            # 静默处理错误，不影响编辑
            pass
    
    def on_closing(self):
        """处理窗口关闭事件，检查是否有未保存的更改"""
        try:
            # 检查是否有未保存的更改
            if hasattr(self, 'current_chapter_index') and self.current_chapter_index is not None:
                if self.has_unsaved_changes():
                    result = messagebox.askyesno(
                        "保存更改",
                        "当前章节有未保存的更改，是否保存？\n\n点击'是'保存并退出\n点击'否'不保存直接退出"
                    )
                    
                    if result:  # 是，保存当前章节
                        # 保存当前正在编辑的章节
                        if not self.novel_service.save_current_chapter(silent=True, chapter_index=self.current_chapter_index):
                            # 保存失败，询问用户是否仍要退出
                            continue_result = messagebox.askyesno(
                                "保存失败",
                                "保存章节失败，是否仍要退出程序？\n\n点击'是'退出（将丢失未保存的更改）\n点击'否'返回程序"
                            )
                            if not continue_result:  # 用户选择不退出
                                return  # 阻止关闭
                    # 如果选择"否"，直接退出，不保存
            
            # 关闭程序
            self.root.destroy()
        except Exception as e:
            print(f"[错误] 关闭程序时发生错误: {e}")
            traceback.print_exc()
            # 即使出错也关闭程序
            self.root.destroy()


def main():
    try:
        root = tk.Tk()
        app = NovelGeneratorApp(root)
        root.mainloop()
    except Exception as e:
        print("=" * 50)
        print("程序发生错误！")
        print("=" * 50)
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        print("\n详细错误堆栈:")
        print("-" * 50)
        traceback.print_exc()
        print("=" * 50)
        input("\n按回车键退出...")
        sys.exit(1)


if __name__ == "__main__":
    # 确保错误输出到控制台
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print("=" * 50)
        print("程序启动失败！")
        print("=" * 50)
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        print("\n详细错误堆栈:")
        print("-" * 50)
        traceback.print_exc()
        print("=" * 50)
        input("\n按回车键退出...")
        sys.exit(1)
