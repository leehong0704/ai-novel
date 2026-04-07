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
        """刷新所有页面的章节列表显示"""
        try:
            # 策划页列表框
            if hasattr(self.app, 'chapter_listbox'):
                self.app.chapter_listbox.delete(0, tk.END)
                for idx, chapter in enumerate(self.app.chapter_list):
                    display_text = f"第{idx+1}章 {chapter.get('title', '')}"
                    self.app.chapter_listbox.insert(tk.END, display_text)
            
            # 正文页列表框
            if hasattr(self.app, 'content_chapter_listbox'):
                self.app.content_chapter_listbox.delete(0, tk.END)
                for idx, chapter in enumerate(self.app.chapter_list):
                    display_text = f"第{idx+1}章 {chapter.get('title', '')}"
                    self.app.content_chapter_listbox.insert(tk.END, display_text)
                    
            # 恢复当前选择
            if self.app.current_chapter_index is not None:
                self._restore_selection(self.app.current_chapter_index)
        except Exception as e:
            print(f"[错误] 刷新章节列表失败: {e}")

    def _sync_listbox_selection(self, index, source):
        """在两个列表框之间同步选择状态"""
        if source == "plan":
            target = getattr(self.app, "content_chapter_listbox", None)
        else:
            target = getattr(self.app, "chapter_listbox", None)
            
        if target:
            target.selection_clear(0, tk.END)
            target.selection_set(index)
            target.see(index)

    def _restore_selection(self, index):
        """恢复所有列表框的选择"""
        if hasattr(self.app, 'chapter_listbox') and index < self.app.chapter_listbox.size():
            self.app.chapter_listbox.selection_clear(0, tk.END)
            self.app.chapter_listbox.selection_set(index)
            self.app.chapter_listbox.see(index)
        if hasattr(self.app, 'content_chapter_listbox') and index < self.app.content_chapter_listbox.size():
            self.app.content_chapter_listbox.selection_clear(0, tk.END)
            self.app.content_chapter_listbox.selection_set(index)
            self.app.content_chapter_listbox.see(index)
    
    def refresh_chapter_summaries(self):
        """刷新章节总结显示"""
        try:
            if not hasattr(self.app, "summaries_text"):
                return
            
            # 启用编辑以更新内容
            self.app.summaries_text.config(state=tk.NORMAL)
            self.app.summaries_text.delete("1.0", tk.END)
            
            if not self.app.chapter_list:
                self.app.summaries_text.insert("1.0", "暂无章节总结。\n\n请先在章节生成页面为各章节生成总结。")
                self.app.summaries_text.config(state=tk.DISABLED)
                return
            
            # 收集所有章节总结
            has_summary = False
            for idx, chapter in enumerate(self.app.chapter_list):
                title = chapter.get("title", f"未命名章节{idx+1}")
                summary = chapter.get("summary", "").strip()
                
                # 格式化显示
                chapter_header = f"第{idx+1}章 {title}"
                self.app.summaries_text.insert(tk.END, f"{chapter_header}\n", "header")
                self.app.summaries_text.insert(tk.END, "─" * 50 + "\n", "separator")
                
                if summary:
                    self.app.summaries_text.insert(tk.END, f"{summary}\n\n", "summary")
                    has_summary = True
                else:
                    self.app.summaries_text.insert(tk.END, "（暂无总结）\n\n", "no_summary")
            
            # 配置文本样式
            self.app.summaries_text.tag_config("header", font=("Microsoft YaHei", 11, "bold"), foreground="#1f77b4")
            self.app.summaries_text.tag_config("separator", foreground="#cccccc")
            self.app.summaries_text.tag_config("summary", font=("Microsoft YaHei", 10))
            self.app.summaries_text.tag_config("no_summary", font=("Microsoft YaHei", 10, "italic"), foreground="#999999")
            
            if not has_summary:
                self.app.summaries_text.insert("1.0", "💡 提示：尚未生成任何章节总结。\n请在章节生成页面选择章节后，点击'总结章节'按钮生成总结。\n\n")
            
            # 禁用编辑
            self.app.summaries_text.config(state=tk.DISABLED)
        except Exception as e:
            print(f"[错误] 刷新章节总结失败: {e}")
            traceback.print_exc()

    
    def add_new_chapter_from_editor(self):
        """
        新增空白章节并提示输入标题。
        
        需求：新建章节后，新建章节的内容应该为空，因此不再从当前编辑器复制内容或创作提示。
        """
        # 不再读取当前编辑器内容，新章节默认为空
        prompt_content = ""
        content = ""
        
        # 若当前章节有未保存更改，先提示保存
        try:
            if hasattr(self.app, "current_chapter_index") and self.app.current_chapter_index is not None:
                if self.has_unsaved_changes():
                    should_save = messagebox.askyesno(
                        "保存提示",
                        "当前章节有未保存的更改，新增章节前是否先保存？\n\n点击'是'保存当前章节\n点击'否'继续新增（将丢失未保存更改）"
                    )
                    if should_save:
                        if not self.save_current_chapter(silent=True, chapter_index=self.app.current_chapter_index):
                            continue_add = messagebox.askyesno(
                                "保存失败",
                                "保存当前章节失败，是否仍要继续新增章节？\n\n点击'是'继续新增（将丢失未保存更改）\n点击'否'返回编辑"
                            )
                            if not continue_add:
                                return
        except Exception:
            # 提示失败不应阻塞新增逻辑，继续后续流程
            pass
        
        # 弹出对话框输入章节标题
        dialog = tk.Toplevel(self.app.root)
        dialog.title("新增章节")
        dialog.transient(self.app.root)
        dialog.grab_set()
        self.app.ui_helper.center_window(dialog, 400, 150)
        
        tk.Label(dialog, text="请输入章节标题:", font=("Microsoft YaHei", 11)).pack(pady=10)
        title_entry = tk.Entry(dialog, font=("Microsoft YaHei", 11), width=30)
        title_entry.pack(pady=5)
        title_entry.focus()
        
        def on_ok():
            title = title_entry.get().strip() or "未命名章节"
            # 新章节内容与提示均为空，由后续编辑
            new_chapter = {
                "title": title, 
                "content": content, 
                "prompt": prompt_content,
                "climax": "", 
                "hook": "", 
                "scenes": "", 
                "num": str(len(self.app.chapter_list) + 1)
            }
            self.app.chapter_list.append(new_chapter)
            self._persist_chapters_to_novel()
            self.refresh_chapter_listbox()
            dialog.destroy()
            messagebox.showinfo("成功", f"已添加章节")
            
            # 新增后清空编辑区（提示与内容），避免沿用旧文本
            try:
                if hasattr(self.app, "prompt_text"):
                    self.app.prompt_text.delete("1.0", tk.END)
                if hasattr(self.app, "content_text"):
                    self.app.content_text.delete("1.0", tk.END)
                # 重置原始内容，用于后续未保存检测
                self.app.original_chapter_prompt = ""
                self.app.original_chapter_content = ""
                # 更新字数与字符统计
                if hasattr(self.app, "update_prompt_char_count"):
                    self.app.update_prompt_char_count()
                if hasattr(self.app, "update_word_count"):
                    self.app.update_word_count()
            except Exception:
                pass
        
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
            dialog.transient(self.app.root)
            dialog.grab_set()
            self.app.ui_helper.center_window(dialog, 400, 150)
            
            tk.Label(dialog, text="请输入新的章节标题:", font=("Microsoft YaHei", 11)).pack(pady=10)
            title_entry = tk.Entry(dialog, font=("Microsoft YaHei", 11), width=30)
            title_entry.insert(0, old_title)
            title_entry.pack(pady=5)
            title_entry.focus()
            title_entry.select_range(0, tk.END)
            
            def on_ok():
                new_title = title_entry.get().strip() or "未命名章节"
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
        dialog.transient(self.app.root)
        dialog.grab_set()
        self.app.ui_helper.center_window(dialog, 400, 150)
        
        tk.Label(dialog, text=f"将在第{insert_idx+1}章之前插入，请输入章节标题:", font=("Microsoft YaHei", 10)).pack(pady=10)
        title_entry = tk.Entry(dialog, font=("Microsoft YaHei", 11), width=30)
        title_entry.pack(pady=5)
        title_entry.focus()
        
        def on_ok():
            title = title_entry.get().strip() or "未命名章节"
            # 插入章节信息
            new_chapter = {
                "title": title, 
                "content": content, 
                "prompt": prompt_content,
                "climax": "", 
                "hook": "", 
                "scenes": "", 
                "num": str(insert_idx + 1)
            }
            self.app.chapter_list.insert(insert_idx, new_chapter)
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
                
                # 载入策划信息
                if hasattr(self.app, 'chapter_title_var'):
                    self.app.chapter_title_var.set(chapter.get("title", ""))
                
                if hasattr(self.app, 'chapter_climax_text'):
                    self.app.chapter_climax_text.delete("1.0", tk.END)
                    self.app.chapter_climax_text.insert("1.0", chapter.get("climax", ""))
                
                if hasattr(self.app, 'chapter_hook_text'):
                    self.app.chapter_hook_text.delete("1.0", tk.END)
                    self.app.chapter_hook_text.insert("1.0", chapter.get("hook", ""))
                
                # 载入摘要信息 (新增)
                if hasattr(self.app, 'global_summary_text'):
                    self.app.global_summary_text.delete("1.0", tk.END)
                    self.app.global_summary_text.insert("1.0", chapter.get("global_summary", ""))
                
                if hasattr(self.app, 'recent_summary_text'):
                    self.app.recent_summary_text.delete("1.0", tk.END)
                    self.app.recent_summary_text.insert("1.0", chapter.get("summary", ""))
                
                if hasattr(self.app, 'char_status_text'):
                    self.app.char_status_text.delete("1.0", tk.END)
                    self.app.char_status_text.insert("1.0", chapter.get("char_status", ""))

                # 更新当前章节索引
                self.app.current_chapter_index = idx
                
                # 记录原始内容（用于检测变更）
                self.app.original_chapter_prompt = prompt
                self.app.original_chapter_content = content
                self.app.original_chapter_title_val = chapter.get("title", "")
                self.app.original_chapter_climax = chapter.get("climax", "")
                self.app.original_chapter_hook = chapter.get("hook", "")
                self.app.original_global_summary = chapter.get("global_summary", "")
                self.app.original_recent_summary = chapter.get("summary", "")
                self.app.original_char_status = chapter.get("char_status", "")

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
                
                # 读取策划信息
                ch_title = self.app.chapter_title_var.get() if hasattr(self.app, 'chapter_title_var') else self.app.chapter_list[idx].get("title", "")
                ch_climax = self.app.chapter_climax_text.get("1.0", tk.END).strip() if hasattr(self.app, 'chapter_climax_text') else ""
                ch_hook = self.app.chapter_hook_text.get("1.0", tk.END).strip() if hasattr(self.app, 'chapter_hook_text') else ""
                
                # 读取摘要信息 (新增)
                ch_global_summary = self.app.global_summary_text.get("1.0", tk.END).strip() if hasattr(self.app, 'global_summary_text') else ""
                ch_recent_summary = self.app.recent_summary_text.get("1.0", tk.END).strip() if hasattr(self.app, 'recent_summary_text') else ""
                ch_char_status = self.app.char_status_text.get("1.0", tk.END).strip() if hasattr(self.app, 'char_status_text') else ""

                self.app.chapter_list[idx]["prompt"] = prompt_content
                self.app.chapter_list[idx]["content"] = content
                self.app.chapter_list[idx]["title"] = ch_title
                self.app.chapter_list[idx]["climax"] = ch_climax
                self.app.chapter_list[idx]["hook"] = ch_hook
                self.app.chapter_list[idx]["global_summary"] = ch_global_summary
                self.app.chapter_list[idx]["summary"] = ch_recent_summary
                self.app.chapter_list[idx]["char_status"] = ch_char_status
                
                # 同步列表框标题显示 (格式: 第X章 标题)
                display_text = f"第{idx+1}章 {ch_title}"
                if hasattr(self.app, "chapter_listbox"):
                    self.app.chapter_listbox.delete(idx)
                    self.app.chapter_listbox.insert(idx, display_text)
                    self.app.chapter_listbox.selection_set(idx)
                
                if hasattr(self.app, "content_chapter_listbox"):
                    self.app.content_chapter_listbox.delete(idx)
                    self.app.content_chapter_listbox.insert(idx, display_text)
                    self.app.content_chapter_listbox.selection_set(idx)

                # 更新正文页面的标题显示
                if hasattr(self.app, "content_page_title"):
                    self.app.content_page_title.config(text=f"第{idx+1}章 {ch_title}")

                # 更新原始内容
                self.app.original_chapter_prompt = prompt_content
                self.app.original_chapter_content = content
                self.app.original_chapter_title_val = ch_title
                self.app.original_chapter_climax = ch_climax
                self.app.original_chapter_hook = ch_hook
                self.app.original_global_summary = ch_global_summary
                self.app.original_recent_summary = ch_recent_summary
                self.app.original_char_status = ch_char_status
                
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
            
            # 策划信息检测
            curr_title = self.app.chapter_title_var.get() if hasattr(self.app, 'chapter_title_var') else ""
            curr_climax = self.app.chapter_climax_text.get("1.0", tk.END).strip() if hasattr(self.app, 'chapter_climax_text') else ""
            curr_hook = self.app.chapter_hook_text.get("1.0", tk.END).strip() if hasattr(self.app, 'chapter_hook_text') else ""

            # 摘要信息检测 (新增)
            curr_global_sum = self.app.global_summary_text.get("1.0", tk.END).strip() if hasattr(self.app, 'global_summary_text') else ""
            curr_recent_sum = self.app.recent_summary_text.get("1.0", tk.END).strip() if hasattr(self.app, 'recent_summary_text') else ""
            curr_char_status = self.app.char_status_text.get("1.0", tk.END).strip() if hasattr(self.app, 'char_status_text') else ""

            # 排除占位符文本
            if "请输入你的创作想法" in current_prompt:
                current_prompt = ""
            
            return (current_prompt != getattr(self.app, "original_chapter_prompt", "") or 
                    current_content != getattr(self.app, "original_chapter_content", "") or
                    curr_title != getattr(self.app, "original_chapter_title_val", "") or
                    curr_climax != getattr(self.app, "original_chapter_climax", "") or
                    curr_hook != getattr(self.app, "original_chapter_hook", "") or
                    curr_global_sum != getattr(self.app, "original_global_summary", "") or
                    curr_recent_sum != getattr(self.app, "original_recent_summary", "") or
                    curr_char_status != getattr(self.app, "original_char_status", ""))
        except:
            return False
    
    def on_chapter_selected(self, event=None, source="plan"):
        """列表选择变化时，自动同步创作提示与生成内容"""
        try:
            # 防止递归调用（当恢复选择时可能会再次触发事件）
            if hasattr(self.app, '_is_handling_chapter_selection') and self.app._is_handling_chapter_selection:
                return
            self.app._is_handling_chapter_selection = True
            
            try:
                # 获取新选择的章节索引
                if source == "plan":
                    sel = self.app.chapter_listbox.curselection()
                else:
                    sel = self.app.content_chapter_listbox.curselection()
                    
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
                    
                    if result:
                        if not self.save_current_chapter(silent=True, chapter_index=self.app.current_chapter_index):
                            # 恢复之前的选择
                            self.app._is_handling_chapter_selection = False
                            self._restore_selection(self.app.current_chapter_index)
                            return
                
                # 同步另一个列表框的选择
                self._sync_listbox_selection(new_index, source)
                
                # 更新正文页标题显示
                if hasattr(self.app, "content_page_title") and 0 <= new_index < len(self.app.chapter_list):
                    ch = self.app.chapter_list[new_index]
                    self.app.content_page_title.config(text=f"第{new_index+1}章 {ch.get('title', '')}")
                    # 确保正文页文本框可用
                    if hasattr(self.app, "content_text"):
                        self.app.content_text.config(state=tk.NORMAL)

                # 载入新选择的章节
                self.load_selected_chapter()
            finally:
                self.app._is_handling_chapter_selection = False
        except Exception as e:
            print(f"[错误] 章节选择处理失败: {e}")
            traceback.print_exc()
            # 确保即使出错也清除标志
            if hasattr(self.app, '_is_handling_chapter_selection'):
                self.app._is_handling_chapter_selection = False
    
    def _persist_chapters_to_novel(self):
        """
        将章节标题、提示、总结与内容保存到当前小说目录：
            - novel.ini
                [CHAPTERS] 索引=文件名（chapter_001.txt）
                [CHAPTER_TITLES] 索引=标题（纯标题）
                [CHAPTER_PROMPTS] 索引=创作提示
                [CHAPTER_SUMMARIES] 索引=章节总结
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
            
            config = configparser.ConfigParser(interpolation=None)
            if os.path.exists(novel_ini_path):
                config.read(novel_ini_path, encoding='utf-8')
            
            # 清空旧的章节配置
            if "CHAPTERS" in config:
                config.remove_section("CHAPTERS")
            if "CHAPTER_TITLES" in config:
                config.remove_section("CHAPTER_TITLES")
            if "CHAPTER_PROMPTS" in config:
                config.remove_section("CHAPTER_PROMPTS")
            if "CHAPTER_SUMMARIES" in config:
                config.remove_section("CHAPTER_SUMMARIES")
            if "CHAPTER_CLIMAXES" in config:
                config.remove_section("CHAPTER_CLIMAXES")
            if "CHAPTER_HOOKS" in config:
                config.remove_section("CHAPTER_HOOKS")
            if "CHAPTER_GLOBAL_SUMMARIES" in config:
                config.remove_section("CHAPTER_GLOBAL_SUMMARIES")
            if "CHAPTER_CHAR_STATUSES" in config:
                config.remove_section("CHAPTER_CHAR_STATUSES")
            
            config.add_section("CHAPTERS")
            config.add_section("CHAPTER_TITLES")
            config.add_section("CHAPTER_PROMPTS")
            config.add_section("CHAPTER_SUMMARIES")
            config.add_section("CHAPTER_CLIMAXES")
            config.add_section("CHAPTER_HOOKS")
            config.add_section("CHAPTER_GLOBAL_SUMMARIES")
            config.add_section("CHAPTER_CHAR_STATUSES")
            
            # 保存每个章节
            for idx, chapter in enumerate(self.app.chapter_list):
                chapter_filename = f"chapter_{idx+1:03d}.txt"
                chapter_file_path = os.path.join(chapters_dir, chapter_filename)
                
                title = chapter.get("title", f"未命名章节{idx+1}")
                content = chapter.get("content", "")
                prompt = chapter.get("prompt", "")
                summary = chapter.get("summary", "")
                global_sum = chapter.get("global_summary", "")
                char_stat = chapter.get("char_status", "")
                
                # 写入章节文件
                with open(chapter_file_path, "w", encoding="utf-8") as f:
                    f.write(f"第{idx+1}章 {title}\n\n")
                    f.write(content)
                
                # 更新配置 (确保所有值都是字符串)
                config.set("CHAPTERS", str(idx), str(chapter_filename))
                config.set("CHAPTER_TITLES", str(idx), str(title))
                config.set("CHAPTER_PROMPTS", str(idx), str(prompt))
                config.set("CHAPTER_SUMMARIES", str(idx), str(summary))
                config.set("CHAPTER_CLIMAXES", str(idx), str(chapter.get("climax", "")))
                config.set("CHAPTER_HOOKS", str(idx), str(chapter.get("hook", "")))
                
                # 新增字段容错
                try:
                    config.set("CHAPTER_GLOBAL_SUMMARIES", str(idx), str(chapter.get("global_summary", "")))
                    config.set("CHAPTER_CHAR_STATUSES", str(idx), str(chapter.get("char_status", "")))
                except Exception:
                    pass
            
            # 写入配置文件
            with open(novel_ini_path, "w", encoding="utf-8") as f:
                config.write(f)
            
            print(f"[信息] 已保存 {len(self.app.chapter_list)} 个章节到 {self.app.current_novel_dir}")
            return True
        except Exception as e:
            print(f"[错误] 持久化章节失败: {e}")
            traceback.print_exc()
            return False

    def export_current_chapter(self):
        """
        导出当前选中的单章为txt文件
        """
        try:
            cur_idx = self.app.current_chapter_index
            if cur_idx is None or cur_idx < 0 or cur_idx >= len(self.app.chapter_list):
                messagebox.showwarning("提示", "请先选择或加载一个有效章节。")
                return
            
            chapter = self.app.chapter_list[cur_idx]
            title = chapter.get("title", f"未命名章节{cur_idx+1}")
            # 直接从编辑器获取最新内容（可能未保存）
            content = self.app.content_text.get("1.0", tk.END).strip()
            
            if not content:
                messagebox.showwarning("提示", "当前章节编辑框内没有内容可以导出。")
                return

            default_name = f"第{cur_idx+1}章_{title}.txt"
            # 简单过滤非法字符，防止文件名冲突
            for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
                default_name = default_name.replace(char, "_")

            file_path = filedialog.asksaveasfilename(
                title="导出当前章节文本",
                defaultextension=".txt",
                initialfile=default_name,
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            
            if not file_path:
                return
            
            with open(file_path, "w", encoding="utf-8", newline='') as f:
                f.write(f"第{cur_idx+1}章 {title}\r\n")
                f.write("-" * 30 + "\r\n")
                # 显式转换内容中的换行符为 \r\n
                normalized_content = content.replace("\r\n", "\n").replace("\n", "\r\n")
                f.write(normalized_content)
            
            messagebox.showinfo("成功", f"✅ 章节“{title}”已成功导出至：\n{file_path}")
            
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("错误", f"导出单章失败: {str(e)}")

    def export_novel_text(self):
        """
        导出全书为单个txt文件
        """
        try:
            if not self.app.chapter_list:
                messagebox.showwarning("提示", "目前没有任何章节内容可以导出。")
                return

            # 建议默认文件名
            default_name = "我的精彩小说.txt"
            if hasattr(self.app, "title_entry"):
                title = self.app.title_entry.get().strip()
                if title:
                    default_name = f"{title}.txt"

            file_path = filedialog.asksaveasfilename(
                title="导出全文文本",
                defaultextension=".txt",
                initialfile=default_name,
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )

            if not file_path:
                return

            # 调用持久化服务的导出方法
            from services.persistence_service import PersistenceService
            ps = PersistenceService(self.app)
            if ps.export_to_single_text(file_path, self.app.chapter_list):
                messagebox.showinfo("成功", f"✅ 小说全文已成功导出至：\n{file_path}")
            else:
                messagebox.showerror("错误", "导出过程中发生错误，请检查磁盘空间或权限。")

        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("错误", f"导出失败: {str(e)}")

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
            self.app.ui_helper.center_window(dialog, 520, 200)

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
                        "style": (self.app.writing_style_text.get("1.0", tk.END).strip() if hasattr(self.app, "writing_style_text") else (self.app.writing_style_var.get().strip() if hasattr(self.app, "writing_style_var") else "平实自然")),
                        "theme": (self.app.novel_theme_text.get("1.0", tk.END).strip() if hasattr(self.app, "novel_theme_text") else (self.app.novel_theme_var.get().strip() if hasattr(self.app, "novel_theme_var") else "")),
                        "outline": (self.app.novel_outline_text.get("1.0", tk.END).strip() if hasattr(self.app, "novel_outline_text") else ""),
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
            cfg = configparser.ConfigParser(interpolation=None)
            if os.path.exists(novel_ini):
                cfg.read(novel_ini, encoding="utf-8")
            if "BASIC" not in cfg:
                cfg["BASIC"] = {}
            if "META" not in cfg:
                cfg["META"] = {}

            cfg["BASIC"]["title"] = self.app.title_entry.get().strip() if hasattr(self.app, "title_entry") else ""
            cfg["BASIC"]["type"] = self.app.novel_type_var.get() if hasattr(self.app, "novel_type_var") else "其他"
            cfg["BASIC"]["style"] = (self.app.writing_style_text.get("1.0", tk.END).strip() if hasattr(self.app, "writing_style_text") else (self.app.writing_style_var.get().strip() if hasattr(self.app, "writing_style_var") else "平实自然"))
            cfg["BASIC"]["theme"] = (self.app.novel_theme_text.get("1.0", tk.END).strip() if hasattr(self.app, "novel_theme_text") else (self.app.novel_theme_var.get().strip() if hasattr(self.app, "novel_theme_var") else ""))
            cfg["BASIC"]["outline"] = (self.app.novel_outline_text.get("1.0", tk.END).strip() if hasattr(self.app, "novel_outline_text") else "")
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

            cfg = configparser.ConfigParser(interpolation=None)
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
            style_value = basic.get("style", "平实自然")
            if hasattr(self.app, "writing_style_text"):
                self.app.writing_style_text.delete("1.0", tk.END)
                self.app.writing_style_text.insert("1.0", style_value)
            elif hasattr(self.app, "writing_style_var"):
                self.app.writing_style_var.set(style_value)
            theme_value = basic.get("theme", "")
            if hasattr(self.app, "novel_theme_text"):
                self.app.novel_theme_text.delete("1.0", tk.END)
                self.app.novel_theme_text.insert("1.0", theme_value)
            elif hasattr(self.app, "novel_theme_var"):
                self.app.novel_theme_var.set(theme_value)
            
            # 加载剧情主线
            outline_value = basic.get("outline", "")
            if hasattr(self.app, "novel_outline_text"):
                self.app.novel_outline_text.delete("1.0", tk.END)
                self.app.novel_outline_text.insert("1.0", outline_value)
            
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
                cfg = configparser.ConfigParser(interpolation=None)
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
                    summary = ""
                    if "CHAPTER_SUMMARIES" in cfg:
                        summary = cfg["CHAPTER_SUMMARIES"].get(str(idx), "") or ""
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
                            content = content.strip()
                    except Exception:
                        content = ""
                    
                    climax = cfg["CHAPTER_CLIMAXES"].get(str(idx), "") if "CHAPTER_CLIMAXES" in cfg else ""
                    hook = cfg["CHAPTER_HOOKS"].get(str(idx), "") if "CHAPTER_HOOKS" in cfg else ""
                    global_summary = cfg["CHAPTER_GLOBAL_SUMMARIES"].get(str(idx), "") if "CHAPTER_GLOBAL_SUMMARIES" in cfg else ""
                    char_status = cfg["CHAPTER_CHAR_STATUSES"].get(str(idx), "") if "CHAPTER_CHAR_STATUSES" in cfg else ""
                    
                    self.app.chapter_list.append({
                        "title": PromptBuilder._strip_chapter_prefix(title), 
                        "content": content, 
                        "prompt": prompt, 
                        "summary": summary,
                        "climax": climax,
                        "hook": hook,
                        "global_summary": global_summary,
                        "char_status": char_status
                    })
                # 刷新UI
                if hasattr(self.app, "refresh_chapter_listbox"):
                    self.app.refresh_chapter_listbox()
                # 刷新章节总结显示
                if hasattr(self.app, "refresh_chapter_summaries"):
                    self.app.refresh_chapter_summaries()
            except Exception:
                traceback.print_exc()
