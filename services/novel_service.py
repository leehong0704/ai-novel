"""
小说应用业务逻辑服务
将NovelGeneratorApp中的业务逻辑方法提取到此服务类中
"""

import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import os
import configparser
import threading
import traceback
from datetime import datetime
from AI.prompt_builder import PromptBuilder
from services.config_manager import ConfigManager


class NovelService:
    """小说业务逻辑服务类"""
    
    def __init__(self, app):
        """
        初始化服务
        Args:
            app: NovelGeneratorApp实例
        """
        self.app = app
    
    # ==================== 章节管理方法 ====================
    
    def refresh_chapter_listbox(self):
        """刷新章节列表显示"""
        try:
            self.app.chapter_listbox.delete(0, tk.END)
            for idx, chapter in enumerate(self.app.chapter_list):
                title = chapter.get("title", f"未命名章节{idx+1}")
                display_text = f"第{idx+1}章 {title}"
                self.app.chapter_listbox.insert(tk.END, display_text)
        except Exception as e:
            print(f"[错误] 刷新章节列表失败: {e}")
            traceback.print_exc()
    
    def add_new_chapter_from_editor(self):
        """将当前编辑器内容作为新章节，提示输入标题"""
        prompt_content = self.app.prompt_text.get("1.0", tk.END).strip()
        content = self.app.content_text.get("1.0", tk.END).strip()
        
        if not content:
            messagebox.showwarning("提示", "生成内容为空，无法添加章节！")
            return
        
        # 弹出对话框输入章节标题
        dialog = tk.Toplevel(self.app.root)
        dialog.title("新增章节")
        dialog.geometry("400x150")
        dialog.transient(self.app.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="请输入章节标题:", font=("Microsoft YaHei", 11)).pack(pady=10)
        title_entry = tk.Entry(dialog, font=("Microsoft YaHei", 11), width=30)
        title_entry.pack(pady=5)
        title_entry.focus()
        
        def on_ok():
            title = title_entry.get().strip()
            if not title:
                messagebox.showwarning("提示", "章节标题不能为空！", parent=dialog)
                return
            self.app.chapter_list.append({"title": title, "content": content, "prompt": prompt_content})
            self._persist_chapters_to_novel()
            self.refresh_chapter_listbox()
            dialog.destroy()
            messagebox.showinfo("成功", f"已添加章节：{title}")
        
        tk.Button(dialog, text="确定", command=on_ok, width=10).pack(side=tk.LEFT, padx=20, pady=10)
        tk.Button(dialog, text="取消", command=dialog.destroy, width=10).pack(side=tk.RIGHT, padx=20, pady=10)
    
    def rename_selected_chapter(self):
        """重命名所选章节标题"""
        try:
            sel = self.app.chapter_listbox.curselection()
            if not sel:
                messagebox.showwarning("提示", "请先选择要重命名的章节！")
                return
            idx = sel[0]
            old_title = self.app.chapter_list[idx].get("title", "")
            
            dialog = tk.Toplevel(self.app.root)
            dialog.title("编辑章节标题")
            dialog.geometry("400x150")
            dialog.transient(self.app.root)
            dialog.grab_set()
            
            tk.Label(dialog, text="请输入新的章节标题:", font=("Microsoft YaHei", 11)).pack(pady=10)
            title_entry = tk.Entry(dialog, font=("Microsoft YaHei", 11), width=30)
            title_entry.insert(0, old_title)
            title_entry.pack(pady=5)
            title_entry.focus()
            title_entry.select_range(0, tk.END)
            
            def on_ok():
                new_title = title_entry.get().strip()
                if not new_title:
                    messagebox.showwarning("提示", "章节标题不能为空！", parent=dialog)
                    return
                self.app.chapter_list[idx]["title"] = new_title
                self._persist_chapters_to_novel()
                self.refresh_chapter_listbox()
                self.app.chapter_listbox.selection_set(idx)
                dialog.destroy()
            
            tk.Button(dialog, text="确定", command=on_ok, width=10).pack(side=tk.LEFT, padx=20, pady=10)
            tk.Button(dialog, text="取消", command=dialog.destroy, width=10).pack(side=tk.RIGHT, padx=20, pady=10)
        except Exception as e:
            messagebox.showerror("错误", f"重命名失败: {str(e)}")
    
    def insert_chapter_at_selection(self):
        """将当前编辑器内容插入到所选章节位置之前"""
        prompt_content = self.app.prompt_text.get("1.0", tk.END).strip()
        content = self.app.content_text.get("1.0", tk.END).strip()
        
        if not content:
            messagebox.showwarning("提示", "生成内容为空，无法插入章节！")
            return
        
        sel = self.app.chapter_listbox.curselection()
        if not sel:
            messagebox.showwarning("提示", "请先选择插入位置（将在所选章节之前插入）！")
            return
        
        insert_idx = sel[0]
        
        dialog = tk.Toplevel(self.app.root)
        dialog.title("插入章节")
        dialog.geometry("400x150")
        dialog.transient(self.app.root)
        dialog.grab_set()
        
        tk.Label(dialog, text=f"将在第{insert_idx+1}章之前插入，请输入章节标题:", font=("Microsoft YaHei", 10)).pack(pady=10)
        title_entry = tk.Entry(dialog, font=("Microsoft YaHei", 11), width=30)
        title_entry.pack(pady=5)
        title_entry.focus()
        
        def on_ok():
            title = title_entry.get().strip()
            if not title:
                messagebox.showwarning("提示", "章节标题不能为空！", parent=dialog)
                return
            self.app.chapter_list.insert(insert_idx, {"title": title, "content": content, "prompt": prompt_content})
            self._persist_chapters_to_novel()
            self.refresh_chapter_listbox()
            self.app.chapter_listbox.selection_set(insert_idx)
            dialog.destroy()
            messagebox.showinfo("成功", f"已在第{insert_idx+1}章位置插入：{title}")
        
        tk.Button(dialog, text="确定", command=on_ok, width=10).pack(side=tk.LEFT, padx=20, pady=10)
        tk.Button(dialog, text="取消", command=dialog.destroy, width=10).pack(side=tk.RIGHT, padx=20, pady=10)
    
    def load_selected_chapter(self):
        """载入所选章节到编辑器"""
        try:
            sel = self.app.chapter_listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            if 0 <= idx < len(self.app.chapter_list):
                chapter = self.app.chapter_list[idx]
                
                # 载入提示
                prompt = chapter.get("prompt", "")
                self.app.prompt_text.delete("1.0", tk.END)
                if prompt:
                    self.app.prompt_text.insert("1.0", prompt)
                
                # 载入内容
                content = chapter.get("content", "")
                self.app.content_text.delete("1.0", tk.END)
                if content:
                    self.app.content_text.insert("1.0", content)
                
                # 更新当前章节索引
                self.app.current_chapter_index = idx
                
                # 记录原始内容（用于检测变更）
                self.app.original_chapter_prompt = prompt
                self.app.original_chapter_content = content
                
                # 更新字数统计
                if hasattr(self.app, 'update_word_count'):
                    self.app.update_word_count()
                if hasattr(self.app, 'update_prompt_char_count'):
                    self.app.update_prompt_char_count()
        except Exception as e:
            print(f"[错误] 载入章节失败: {e}")
            traceback.print_exc()
    
    def save_current_chapter(self, silent=False, chapter_index=None):
        """
        将当前编辑器中的提示与内容保存到指定章节，并写入小说文件
        Args:
            silent: 如果为True，保存成功时不显示消息框（用于切换章节时自动保存）
            chapter_index: 要保存的章节索引，如果为None则使用当前选中的章节
        """
        try:
            # 如果指定了章节索引，使用指定的；否则使用当前选中的
            if chapter_index is not None:
                idx = chapter_index
            else:
                sel = self.app.chapter_listbox.curselection()
                if not sel:
                    if not silent:
                        messagebox.showwarning("提示", "请先选择要保存的章节！")
                    return False
                idx = sel[0]
            
            if 0 <= idx < len(self.app.chapter_list):
                prompt_content = self.app.prompt_text.get("1.0", tk.END).strip()
                content = self.app.content_text.get("1.0", tk.END).strip()
                
                self.app.chapter_list[idx]["prompt"] = prompt_content
                self.app.chapter_list[idx]["content"] = content
                
                # 更新原始内容
                self.app.original_chapter_prompt = prompt_content
                self.app.original_chapter_content = content
                
                # 保存到文件，检查是否成功
                if not self._persist_chapters_to_novel():
                    error_msg = "保存章节到文件失败，请检查小说目录设置"
                    print(f"[错误] {error_msg}")
                    if not silent:
                        messagebox.showerror("错误", error_msg)
                    return False
                
                if not silent:
                    messagebox.showinfo("成功", f"已保存第{idx+1}章")
                return True
            return False
        except Exception as e:
            error_msg = f"保存章节失败: {str(e)}"
            print(f"[错误] {error_msg}")
            traceback.print_exc()
            if not silent:
                messagebox.showerror("错误", error_msg)
            return False
    
    def delete_selected_chapter(self):
        """删除列表中选定的章节"""
        try:
            sel = self.app.chapter_listbox.curselection()
            if not sel:
                messagebox.showwarning("提示", "请先选择要删除的章节！")
                return
            
            idx = sel[0]
            title = self.app.chapter_list[idx].get("title", f"第{idx+1}章")
            
            if messagebox.askyesno("确认删除", f"确定要删除 {title} 吗？"):
                del self.app.chapter_list[idx]
                self._persist_chapters_to_novel()
                self.refresh_chapter_listbox()
                messagebox.showinfo("成功", "章节已删除")
        except Exception as e:
            messagebox.showerror("错误", f"删除失败: {str(e)}")
    
    def has_unsaved_changes(self):
        """检查当前章节是否有未保存的更改"""
        try:
            current_prompt = self.app.prompt_text.get("1.0", tk.END).strip()
            current_content = self.app.content_text.get("1.0", tk.END).strip()
            
            # 排除占位符文本
            if "请输入你的创作想法" in current_prompt:
                current_prompt = ""
            
            return (current_prompt != self.app.original_chapter_prompt or 
                    current_content != self.app.original_chapter_content)
        except:
            return False
    
    def on_chapter_selected(self, event=None):
        """列表选择变化时，自动同步创作提示与生成内容"""
        try:
            # 防止递归调用（当恢复选择时可能会再次触发事件）
            if hasattr(self.app, '_is_handling_chapter_selection') and self.app._is_handling_chapter_selection:
                return
            self.app._is_handling_chapter_selection = True
            
            try:
                # 获取新选择的章节索引
                sel = self.app.chapter_listbox.curselection()
                if not sel:
                    return
                
                new_index = sel[0]
                
                # 如果选择的是当前章节，不需要切换
                if new_index == self.app.current_chapter_index:
                    return
                
                # 检查是否有未保存的更改（在切换前保存当前正在编辑的章节）
                if self.app.current_chapter_index is not None and self.has_unsaved_changes():
                    result = messagebox.askyesno(
                        "保存更改",
                        "当前章节有未保存的更改，是否保存？\n\n点击'是'保存并切换\n点击'否'放弃更改并切换"
                    )
                    
                    if result:  # 是，保存当前正在编辑的章节（使用current_chapter_index而不是新选择的索引）
                        # 重要：保存时使用 current_chapter_index，因为此时列表框中已经选择了新章节
                        if not self.save_current_chapter(silent=True, chapter_index=self.app.current_chapter_index):
                            # 保存失败，询问用户是否继续切换
                            continue_result = messagebox.askyesno(
                                "保存失败",
                                "保存章节失败，是否仍要继续切换章节？\n\n点击'是'继续切换（将丢失未保存的更改）\n点击'否'停留在当前章节"
                            )
                            if not continue_result:  # 用户选择不继续
                                # 恢复之前的选择
                                self.app._is_handling_chapter_selection = False
                                if self.app.current_chapter_index is not None:
                                    self.app.chapter_listbox.selection_clear(0, tk.END)
                                    self.app.chapter_listbox.selection_set(self.app.current_chapter_index)
                                return
                    # 如果选择"否"，直接继续，不保存，丢弃修改
                
                # 载入新选择的章节（这会覆盖当前编辑器内容，从而丢弃未保存的修改）
                self.load_selected_chapter()
            finally:
                # 确保标志被清除
                self.app._is_handling_chapter_selection = False
        except Exception as e:
            print(f"[错误] 章节选择处理失败: {e}")
            traceback.print_exc()
            # 确保即使出错也清除标志
            if hasattr(self.app, '_is_handling_chapter_selection'):
                self.app._is_handling_chapter_selection = False
    
    def _persist_chapters_to_novel(self):
        """
        将章节标题、提示与内容保存到当前小说目录：
            - novel.ini
                [CHAPTERS] 索引=文件名（chapter_001.txt）
                [CHAPTER_TITLES] 索引=标题（纯标题）
                [CHAPTER_PROMPTS] 索引=创作提示
            - 章节文件：chapters/chapter_001.txt，首行写 '第X章 标题'，空行后正文
        Returns:
            bool: 保存成功返回True，失败返回False
        """
        try:
            if not hasattr(self.app, 'current_novel_dir') or not self.app.current_novel_dir:
                print(f"[错误] current_novel_dir 未设置，无法保存章节")
                return False
            
            novel_ini_path = os.path.join(self.app.current_novel_dir, "novel.ini")
            chapters_dir = os.path.join(self.app.current_novel_dir, "chapters")
            os.makedirs(chapters_dir, exist_ok=True)
            
            config = configparser.ConfigParser()
            if os.path.exists(novel_ini_path):
                config.read(novel_ini_path, encoding='utf-8')
            
            # 清空旧的章节配置
            if "CHAPTERS" in config:
                config.remove_section("CHAPTERS")
            if "CHAPTER_TITLES" in config:
                config.remove_section("CHAPTER_TITLES")
            if "CHAPTER_PROMPTS" in config:
                config.remove_section("CHAPTER_PROMPTS")
            
            config.add_section("CHAPTERS")
            config.add_section("CHAPTER_TITLES")
            config.add_section("CHAPTER_PROMPTS")
            
            # 保存每个章节
            for idx, chapter in enumerate(self.app.chapter_list):
                chapter_filename = f"chapter_{idx+1:03d}.txt"
                chapter_file_path = os.path.join(chapters_dir, chapter_filename)
                
                title = chapter.get("title", f"未命名章节{idx+1}")
                content = chapter.get("content", "")
                prompt = chapter.get("prompt", "")
                
                # 写入章节文件
                with open(chapter_file_path, "w", encoding="utf-8") as f:
                    f.write(f"第{idx+1}章 {title}\n\n")
                    f.write(content)
                
                # 更新配置
                config.set("CHAPTERS", str(idx), chapter_filename)
                config.set("CHAPTER_TITLES", str(idx), title)
                config.set("CHAPTER_PROMPTS", str(idx), prompt)
            
            # 写入配置文件
            with open(novel_ini_path, "w", encoding="utf-8") as f:
                config.write(f)
            
            print(f"[信息] 已保存 {len(self.app.chapter_list)} 个章节到 {self.app.current_novel_dir}")
            return True
        except Exception as e:
            print(f"[错误] 持久化章节失败: {e}")
            traceback.print_exc()
            return False

    def save_novel(self):
        """保存小说内容"""
        novel_title = self.app.title_entry.get().strip()
        novel_content = self.app.content_text.get("1.0", tk.END).strip()
        
        if not novel_title:
            messagebox.showwarning("提示", "请先输入小说标题！")
            return
        
        if not novel_content:
            messagebox.showwarning("提示", "没有内容可保存！")
            return
        
        # 创建output目录
        os.makedirs("output", exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output/{novel_title}_{timestamp}.txt"
        
        # 保存内容
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"《{novel_title}》\n\n")
                f.write(novel_content)
            
            messagebox.showinfo("成功", f"✅ 小说已保存到:\n{filename}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def clear_content(self):
        """清空生成内容"""
        if messagebox.askyesno("确认", "确定要清空生成内容吗？"):
            # 保存当前选中状态
            current_selection = None
            if hasattr(self.app, "chapter_listbox"):
                sel = self.app.chapter_listbox.curselection()
                current_selection = sel[0] if sel else None
            
            self.app.content_text.delete("1.0", tk.END)
            if hasattr(self.app, 'update_word_count'):
                self.app.update_word_count()
            
            # 恢复选中状态
            if current_selection is not None and hasattr(self.app, "chapter_listbox"):
                if current_selection < self.app.chapter_listbox.size():
                    self.app.chapter_listbox.selection_set(current_selection)
                    self.app.chapter_listbox.see(current_selection)
            
            messagebox.showinfo("成功", "✅ 生成内容已清空")

    def create_new_novel(self):
        """弹出创建小说对话框：选择目录并创建小说配置"""
        try:
            dialog = tk.Toplevel(self.app.root)
            dialog.title("创建小说")
            dialog.transient(self.app.root)
            dialog.grab_set()
            dialog.geometry("520x200")

            frame = tk.Frame(dialog, padx=20, pady=20)
            frame.pack(fill=tk.BOTH, expand=True)

            # 目录选择
            tk.Label(frame, text="小说配置目录：", font=("Microsoft YaHei", 10)).grid(row=0, column=0, sticky=tk.W, pady=10)
            dir_var = tk.StringVar(value="")
            dir_entry = tk.Entry(frame, textvariable=dir_var, font=("Microsoft YaHei", 10))
            dir_entry.grid(row=0, column=1, sticky=tk.EW, pady=10, padx=(0, 10))
            def browse_dir():
                path = filedialog.askdirectory(title="选择小说配置目录")
                if path:
                    dir_var.set(path)
            browse_btn = tk.Button(frame, text="浏览...", command=browse_dir, cursor="hand2")
            browse_btn.grid(row=0, column=2, sticky=tk.W)

            # 提示
            hint = tk.Label(frame, text="将创建 novel.ini 和 chapters/ 目录。标题、类型、风格来自当前设置。", fg="gray")
            hint.grid(row=1, column=0, columnspan=3, sticky=tk.W)

            frame.columnconfigure(1, weight=1)

            # 底部按钮
            btns = tk.Frame(dialog, padx=20, pady=10)
            btns.pack(fill=tk.X, side=tk.BOTTOM)
            def on_cancel():
                dialog.destroy()
            def on_confirm():
                target_dir = dir_var.get().strip()
                if not target_dir:
                    messagebox.showwarning("提示", "请选择小说配置目录！", parent=dialog)
                    return
                try:
                    os.makedirs(target_dir, exist_ok=True)
                    chapters_dir = os.path.join(target_dir, "chapters")
                    os.makedirs(chapters_dir, exist_ok=True)
                    # 写入 novel.ini
                    cfg = configparser.ConfigParser()
                    cfg["BASIC"] = {
                        "title": self.app.title_entry.get().strip() if hasattr(self.app, "title_entry") else "",
                        "type": self.app.novel_type_var.get() if hasattr(self.app, "novel_type_var") else "其他",
                        "style": self.app.writing_style_var.get() if hasattr(self.app, "writing_style_var") else "平实自然",
                        "theme": (self.app.novel_theme_text.get("1.0", tk.END).strip() if hasattr(self.app, "novel_theme_text") else (self.app.novel_theme_var.get().strip() if hasattr(self.app, "novel_theme_var") else "")),
                        "chapter_words": str(self.app.chapter_words_var.get()) if hasattr(self.app, "chapter_words_var") else "3000"
                    }
                    cfg["META"] = {
                        "created_by": "AI小说生成器",
                        "chapters_path": "chapters"
                    }
                    novel_ini = os.path.join(target_dir, "novel.ini")
                    with open(novel_ini, "w", encoding="utf-8") as f:
                        cfg.write(f)

                    # 保存最后打开的小说路径
                    save_config_value = ConfigManager.save_config_value
                    save_config_value("APP", "last_novel", novel_ini)

                    # 同步UI状态：清空正文与章节，标题保持/更新
                    self.app.current_novel_dir = target_dir
                    if hasattr(self.app, "novel_dir_var"):
                        self.app.novel_dir_var.set(target_dir)
                    self.app.content_text.delete("1.0", tk.END)
                    if hasattr(self.app, "chapter_listbox"):
                        self.app.chapter_listbox.delete(0, tk.END)
                    self.app.chapter_list.clear()
                    if hasattr(self.app, 'update_word_count'):
                        self.app.update_word_count()
                    # 创建/写入配置后，允许访问相关页面
                    self.app.update_tab_access()

                    messagebox.showinfo("成功", f"✅ 已在以下目录创建小说配置：\n{target_dir}", parent=dialog)
                    dialog.destroy()
                except Exception as e:
                    traceback.print_exc()
                    messagebox.showerror("错误", f"创建失败: {str(e)}", parent=dialog)

            cancel_btn = tk.Button(btns, text="取消", command=on_cancel, cursor="hand2")
            cancel_btn.pack(side=tk.RIGHT, padx=5)
            ok_btn = tk.Button(btns, text="确定创建", command=on_confirm, bg="#28a745", fg="white", cursor="hand2")
            ok_btn.pack(side=tk.RIGHT, padx=5)
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("错误", f"创建小说对话框失败: {str(e)}")

    def load_novel(self):
        """读取已保存的小说文本并加载到编辑器"""
        try:
            file_path = filedialog.askopenfilename(
                title="选择小说文件",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            if not file_path:
                return

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 解析标题（若首行形如《标题》）
            title = ""
            self.app.current_novel_dir = os.path.dirname(file_path)
            if hasattr(self.app, "novel_dir_var"):
                self.app.novel_dir_var.set(self.app.current_novel_dir)
            # 读取纯文本不保证存在配置，更新可访问性（可能会禁用）
            self.app.update_tab_access()
            lines = content.splitlines()
            if lines:
                first_line = lines[0].strip()
                if first_line.startswith("《") and first_line.endswith("》"):
                    title = first_line.strip("《》")
                    body = "\n".join(lines[2:]) if len(lines) > 2 and lines[1] == "" else "\n".join(lines[1:])
                else:
                    body = content
            else:
                body = ""

            # 设置标题与正文
            if hasattr(self.app, "title_entry"):
                self.app.title_entry.delete(0, tk.END)
                self.app.title_entry.insert(0, title if title else os.path.splitext(os.path.basename(file_path))[0])
            self.app.content_text.delete("1.0", tk.END)
            self.app.content_text.insert("1.0", body)
            if hasattr(self.app, 'update_word_count'):
                self.app.update_word_count()

            messagebox.showinfo("成功", f"✅ 已加载小说:\n{file_path}")
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("错误", f"读取小说失败: {str(e)}")

    def save_novel_config(self):
        """保存小说基础信息到当前小说目录的 novel.ini"""
        try:
            target_dir = getattr(self.app, "current_novel_dir", "")
            if not target_dir:
                # 未选择目录时，提示选择
                target_dir = filedialog.askdirectory(title="选择小说配置目录")
                if not target_dir:
                    return
                self.app.current_novel_dir = target_dir
                if hasattr(self.app, "novel_dir_var"):
                    self.app.novel_dir_var.set(target_dir)

            os.makedirs(target_dir, exist_ok=True)
            novel_ini = os.path.join(target_dir, "novel.ini")
            cfg = configparser.ConfigParser()
            if os.path.exists(novel_ini):
                cfg.read(novel_ini, encoding="utf-8")
            if "BASIC" not in cfg:
                cfg["BASIC"] = {}
            if "META" not in cfg:
                cfg["META"] = {}

            cfg["BASIC"]["title"] = self.app.title_entry.get().strip() if hasattr(self.app, "title_entry") else ""
            cfg["BASIC"]["type"] = self.app.novel_type_var.get() if hasattr(self.app, "novel_type_var") else "其他"
            cfg["BASIC"]["style"] = self.app.writing_style_var.get() if hasattr(self.app, "writing_style_var") else "平实自然"
            cfg["BASIC"]["theme"] = (self.app.novel_theme_text.get("1.0", tk.END).strip() if hasattr(self.app, "novel_theme_text") else (self.app.novel_theme_var.get().strip() if hasattr(self.app, "novel_theme_var") else ""))
            cfg["BASIC"]["chapter_words"] = str(self.app.chapter_words_var.get()) if hasattr(self.app, "chapter_words_var") else "3000"

            if "chapters_path" not in cfg["META"]:
                cfg["META"]["chapters_path"] = "chapters"

            with open(novel_ini, "w", encoding="utf-8") as f:
                cfg.write(f)

            messagebox.showinfo("成功", f"✅ 已保存小说配置到：\n{novel_ini}")
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")

    def export_novel_to_txt(self):
        """导出小说到TXT文件（包含标题和所有章节）"""
        try:
            # 检查是否有小说标题
            novel_title = self.app.title_entry.get().strip() if hasattr(self.app, "title_entry") else ""
            if not novel_title:
                messagebox.showwarning("提示", "请先输入小说标题！")
                return
            
            # 检查是否有章节内容
            if not self.app.chapter_list:
                messagebox.showwarning("提示", "没有章节可导出！")
                return
            
            # 让用户选择保存位置
            file_path = filedialog.asksaveasfilename(
                title="导出小说",
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                initialfile=f"{novel_title}.txt"
            )
            
            if not file_path:
                return
            
            # 生成导出内容
            with open(file_path, "w", encoding="utf-8") as f:
                # 写入标题
                f.write(f"《{novel_title}》\n\n")
                
                # 写入每个章节
                for idx, chapter in enumerate(self.app.chapter_list, start=1):
                    title = chapter.get("title", "")
                    content = chapter.get("content", "")
                    
                    # 格式化章节标题
                    chapter_header = PromptBuilder._format_chapter_display(idx, title)
                    
                    # 写入章节标题和内容
                    f.write(f"{chapter_header}\n\n")
                    if content:
                        f.write(f"{content}\n\n")
                    
                    # 章节之间添加分隔符（除了最后一章）
                    if idx < len(self.app.chapter_list):
                        f.write("\n")
            
            messagebox.showinfo("成功", f"✅ 小说已导出到：\n{file_path}")
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("错误", f"导出失败: {str(e)}")

    def load_novel_config(self, file_path=None):
        """读取 novel.ini 并填充界面，文件选择器仅限 *.ini"""
        try:
            if not file_path:
                file_path = filedialog.askopenfilename(
                    title="选择小说配置文件",
                    filetypes=[("配置文件", "*.ini")]
                )
            if not file_path:
                return

            # 保存最后打开的小说路径
            save_config_value = ConfigManager.save_config_value
            save_config_value("APP", "last_novel", file_path)

            cfg = configparser.ConfigParser()
            cfg.read(file_path, encoding="utf-8")
            basic = cfg["BASIC"] if "BASIC" in cfg else {}

            # 更新当前目录
            self.app.current_novel_dir = os.path.dirname(file_path)
            if hasattr(self.app, "novel_dir_var"):
                self.app.novel_dir_var.set(self.app.current_novel_dir)

            # 写入表单字段
            if hasattr(self.app, "title_entry"):
                self.app.title_entry.delete(0, tk.END)
                self.app.title_entry.insert(0, basic.get("title", ""))
            if hasattr(self.app, "novel_type_var"):
                self.app.novel_type_var.set(basic.get("type", "其他"))
            if hasattr(self.app, "writing_style_var"):
                self.app.writing_style_var.set(basic.get("style", "平实自然"))
            theme_value = basic.get("theme", "")
            if hasattr(self.app, "novel_theme_text"):
                self.app.novel_theme_text.delete("1.0", tk.END)
                self.app.novel_theme_text.insert("1.0", theme_value)
            elif hasattr(self.app, "novel_theme_var"):
                self.app.novel_theme_var.set(theme_value)
            
            # 加载章节字数限制
            if hasattr(self.app, "chapter_words_var"):
                words = basic.get("chapter_words", "3000")
                try:
                    self.app.chapter_words_var.set(int(words))
                except ValueError:
                    self.app.chapter_words_var.set(3000)

            # 加载“小说设定列表”和“人物设定列表”
            try:
                if hasattr(self.app, "novel_setting_listbox"):
                    self.app.novel_setting_listbox.delete(0, tk.END)
                if hasattr(self.app, "character_setting_listbox"):
                    self.app.character_setting_listbox.delete(0, tk.END)
                # 确保详情字典存在
                if not hasattr(self.app, "novel_setting_details"):
                    self.app.novel_setting_details = {}
                if not hasattr(self.app, "character_setting_details"):
                    self.app.character_setting_details = {}
                if not hasattr(self.app, "novel_setting_checked"):
                    self.app.novel_setting_checked = {}
                if not hasattr(self.app, "character_setting_checked"):
                    self.app.character_setting_checked = {}
                self.app.novel_setting_details.clear()
                self.app.character_setting_details.clear()
                self.app.novel_setting_checked.clear()
                self.app.character_setting_checked.clear()

                if "NOVEL_SETTINGS" in cfg:
                    for name, content in cfg["NOVEL_SETTINGS"].items():
                        if hasattr(self.app, "novel_setting_listbox"):
                            self.app.novel_setting_listbox.insert(tk.END, name)
                        self.app.novel_setting_details[name] = content
                if "CHARACTERS" in cfg:
                    for name, content in cfg["CHARACTERS"].items():
                        if hasattr(self.app, "character_setting_listbox"):
                            self.app.character_setting_listbox.insert(tk.END, name)
                        self.app.character_setting_details[name] = content
                # 读取已选中状态
                if "NOVEL_SETTINGS_SELECTED" in cfg:
                    for name, val in cfg["NOVEL_SETTINGS_SELECTED"].items():
                        self.app.novel_setting_checked[name] = str(val).lower() == "true"
                if "CHARACTERS_SELECTED" in cfg:
                    for name, val in cfg["CHARACTERS_SELECTED"].items():
                        self.app.character_setting_checked[name] = str(val).lower() == "true"
                # 刷新复选界面（若存在）
                if hasattr(self.app, "novel_setting_checks"):
                    self.app.novel_setting_checks.rebuild(self.app.novel_setting_details, self.app.novel_setting_checked)
                if hasattr(self.app, "character_setting_checks"):
                    self.app.character_setting_checks.rebuild(self.app.character_setting_details, self.app.character_setting_checked)
            except Exception as e:
                print(f"[调试] 加载设定列表时发生异常: {e}")

            # 读取配置后，允许访问相关页面
            self.app.update_tab_access()

            messagebox.showinfo("成功", f"✅ 已加载配置：\n{file_path}")
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("错误", f"读取配置失败: {str(e)}")
        else:
            try:
                # 加载章节列表（若存在）
                cfg = configparser.ConfigParser()
                cfg.read(file_path, encoding="utf-8")
                novel_dir = os.path.dirname(file_path)
                # 清空内存与列表UI
                self.app.chapter_list.clear()
                if hasattr(self.app, "chapter_listbox"):
                    self.app.chapter_listbox.delete(0, tk.END)
                chapters_path = "chapters"
                if "META" in cfg:
                    chapters_path = cfg["META"].get("chapters_path", chapters_path) or "chapters"
                chapters_dir = os.path.join(novel_dir, chapters_path)
                # 读取索引顺序
                indices = []
                if "CHAPTERS" in cfg:
                    try:
                        indices = sorted((int(k) for k in cfg["CHAPTERS"].keys()), key=int)
                    except Exception:
                        # 非法索引键，跳过
                        indices = []
                # 回退：若无 CHAPTERS，仅根据 CHAPTER_TITLES 数量构造索引
                if not indices and "CHAPTER_TITLES" in cfg:
                    try:
                        indices = sorted((int(k) for k in cfg["CHAPTER_TITLES"].keys()), key=int)
                    except Exception:
                        indices = []
                # 逐章加载
                for idx in indices:
                    title = ""
                    fname = f"chapter_{idx:03d}.txt"
                    if "CHAPTER_TITLES" in cfg:
                        title = cfg["CHAPTER_TITLES"].get(str(idx), "") or ""
                    if "CHAPTERS" in cfg:
                        fname = cfg["CHAPTERS"].get(str(idx), fname) or fname
                    prompt = ""
                    if "CHAPTER_PROMPTS" in cfg:
                        prompt = cfg["CHAPTER_PROMPTS"].get(str(idx), "") or ""
                    content = ""
                    try:
                        path = os.path.join(chapters_dir, fname)
                        if os.path.exists(path):
                            with open(path, "r", encoding="utf-8") as cf:
                                text = cf.read()
                            # 去掉可能的首行“第X章 标题”
                            lines = text.splitlines()
                            if lines:
                                # 若第一行以“第...章”开头，则去掉首行空行处理正文
                                first = lines[0].strip()
                                if first.startswith("第") and "章" in first:
                                    # 跳过首行和紧随其后的空行
                                    body_start = 1
                                    if len(lines) > 1 and lines[1].strip() == "":
                                        body_start = 2
                                    content = "\n".join(lines[body_start:])
                                else:
                                    content = text
                            else:
                                content = ""
                    except Exception:
                        content = ""
                    self.app.chapter_list.append({"title": PromptBuilder._strip_chapter_prefix(title), "content": content, "prompt": prompt})
                # 刷新UI
                if hasattr(self.app, "refresh_chapter_listbox"):
                    self.app.refresh_chapter_listbox()
            except Exception:
                traceback.print_exc()
