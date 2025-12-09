"""
小说内容生成服务
负责调用AI客户端生成内容，处理线程和UI更新
"""

import tkinter as tk
from tkinter import messagebox
import threading
import traceback
from AI.prompt_builder import PromptBuilder

class GenerationService:
    """内容生成服务类"""
    
    def __init__(self, app, default_config):
        """
        初始化服务
        Args:
            app: NovelGeneratorApp实例
            default_config: 默认配置字典
        """
        self.app = app
        self.default_config = default_config
        
    def generate_novel(self, prompt, novel_type, writing_style, temperature, max_tokens):
        """使用AI客户端生成小说内容"""
        try:
            # 读取当前UI中的API配置（若无则使用初始配置）
            try:
                api_base = self.app.api_base_var.get().strip() if hasattr(self.app, "api_base_var") else self.default_config.get('api_base')
            except Exception:
                api_base = self.default_config.get('api_base')
            try:
                api_key = self.app.api_key_var.get().strip() if hasattr(self.app, "api_key_var") else self.default_config.get('api_key')
            except Exception:
                api_key = self.default_config.get('api_key')
            try:
                model = self.app.model_var.get().strip() if hasattr(self.app, "model_var") else self.default_config.get('model')
            except Exception:
                model = self.default_config.get('model')
            
            # 读取章节字数限制配置
            try:
                word_count = self.app.chapter_words_var.get() if hasattr(self.app, "chapter_words_var") else 3000
            except Exception:
                word_count = 3000
            
            # 更新AI客户端配置
            self.app.ai_client.update_config(api_key=api_key, api_base=api_base, model=model)
            
            # 构建系统提示词（包含字数限制）
            system_prompt = PromptBuilder.build_system_prompt(novel_type, writing_style, word_count)
            
            # 用户提示词直接使用传入的prompt（已包含所有内容）
            user_prompt = prompt
            
            # 调用AI客户端生成内容
            return self.app.ai_client.generate_content(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except Exception as e:
            print(f"[错误] generate_novel 调用异常: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
            return f"❌ 生成方法异常: {str(e)}"

    def generate_content(self):
        """生成内容（在后台线程中执行）"""
        try:
            prompt = self.app.prompt_text.get("1.0", tk.END).strip()
            
            if not prompt or "请输入你的创作想法" in prompt:
                messagebox.showwarning("提示", "请输入创作提示！")
                return
            
            # 禁用生成按钮
            self.app.generate_btn.config(state=tk.DISABLED, text="🤖 AI正在创作中...")
            self.app.root.update()
            
            # 获取参数
            novel_type = self.app.novel_type_var.get()
            writing_style = self.app.writing_style_var.get()
            temperature = self.app.temperature_var.get()
            max_tokens = self.app.max_tokens_var.get()
            # 检查是否选择了章节
            current_idx = None
            try:
                if hasattr(self.app, "chapter_listbox"):
                    sel = self.app.chapter_listbox.curselection()
                    if sel:
                        current_idx = sel[0]
            except Exception:
                current_idx = None
            
            # 如果未选择章节，提示用户
            if current_idx is None:
                messagebox.showwarning("提示", "请先选择章节！\n\n请在左侧章节管理列表中选择要生成内容的章节。")
                # 恢复生成按钮
                self.app.generate_btn.config(state=tk.NORMAL, text="🚀 生成小说")
                return
            
            # 显示加载动画并锁定界面
            if hasattr(self.app, "show_loading_animation"):
                self.app.show_loading_animation()
            
            # 组织已勾选的“小说设定/人物设定”
            settings_section = ""
            try:
                # 获取选中的设定
                novel_selected = {}
                if hasattr(self.app, "novel_setting_checked") and hasattr(self.app, "novel_setting_details"):
                    novel_selected = {n: self.app.novel_setting_details.get(n,'') for n, v in self.app.novel_setting_checked.items() if v}
                
                char_selected = {}
                if hasattr(self.app, "character_setting_checked") and hasattr(self.app, "character_setting_details"):
                    char_selected = {n: self.app.character_setting_details.get(n,'') for n, v in self.app.character_setting_checked.items() if v}
                
                settings_section = PromptBuilder.build_settings_content(novel_selected, char_selected)
            except Exception:
                settings_section = ""
            
            # 获取当前章节标题
            chapter_title = ""
            try:
                if current_idx is not None and 0 <= current_idx < len(self.app.chapter_list):
                    # 从章节列表中获取标题
                    stored_title = self.app.chapter_list[current_idx].get("title", "")
                    # 格式化为 "第X章 标题"
                    chapter_title = PromptBuilder._format_chapter_display(current_idx + 1, stored_title)
            except Exception:
                chapter_title = ""
            
            # 构建用户提示词（包含设定信息和章节标题）
            user_prompt = PromptBuilder.build_user_prompt(
                instruction=prompt,
                chapter_list=getattr(self.app, "chapter_list", []),
                current_index=current_idx,
                settings=settings_section,
                chapter_title=chapter_title
            )

            # 记录本次创作提示，供章节条目保存
            self.app._last_prompt = user_prompt
            
            # 获取字数限制（用于调试输出）
            try:
                word_count = self.app.chapter_words_var.get() if hasattr(self.app, "chapter_words_var") else 3000
            except Exception:
                word_count = 3000
            
            print(f"[调试] 开始生成内容...")
            print(f"[调试] 小说类型: {novel_type}, 风格: {writing_style}")
            print(f"[调试] 字数限制: {word_count} 字")
            print(f"[调试] 温度: {temperature}, 最大token: {max_tokens}")
            
            # 在后台线程中生成
            def generate_thread():
                try:
                    generated_text = self.generate_novel(
                        prompt=user_prompt,
                        novel_type=novel_type,
                        writing_style=writing_style,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    print(f"[调试] 生成完成，内容长度: {len(generated_text)} 字符")
                    
                    # 在主线程中更新UI
                    self.app.root.after(0, lambda: self._on_generate_success(generated_text, chapter_title))
                except Exception as e:
                    print(f"[错误] 生成内容时发生异常: {type(e).__name__}: {str(e)}")
                    traceback.print_exc()
                    error_msg = f"生成内容时发生错误: {str(e)}"
                    self.app.root.after(0, lambda: self._on_generate_success(f"❌ {error_msg}", ""))
            
            thread = threading.Thread(target=generate_thread, daemon=True)
            thread.start()
        except Exception as e:
            print(f"[错误] generate_content 方法异常: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
            # 确保出错时也隐藏加载动画
            if hasattr(self.app, "hide_loading_animation"):
                self.app.hide_loading_animation()
            # 恢复生成按钮
            self.app.generate_btn.config(state=tk.NORMAL, text="🚀 生成小说")
            messagebox.showerror("错误", f"发生错误: {str(e)}")

    def continue_content(self):
        """续写小说（独立逻辑）"""
        try:
            prompt = self.app.prompt_text.get("1.0", tk.END).strip()
            
            # 禁用生成按钮
            self.app.modify_btn.config(state=tk.DISABLED, text="🖊️ 正在续写...")
            self.app.root.update()
            
            # 获取参数
            novel_type = self.app.novel_type_var.get()
            writing_style = self.app.writing_style_var.get()
            temperature = self.app.temperature_var.get()
            max_tokens = self.app.max_tokens_var.get()
            
            # 检查是否选择了章节
            current_idx = None
            try:
                if hasattr(self.app, "chapter_listbox"):
                    sel = self.app.chapter_listbox.curselection()
                    if sel:
                        current_idx = sel[0]
            except Exception:
                current_idx = None
            
            if current_idx is None:
                messagebox.showwarning("提示", "请先选择章节！")
                self.app.modify_btn.config(state=tk.NORMAL, text="🖊️ 续写小说")
                return
            
            # 显示加载动画
            if hasattr(self.app, "show_loading_animation"):
                self.app.show_loading_animation()
            
            # 构建设定
            settings_section = ""
            try:
                novel_selected = {}
                if hasattr(self.app, "novel_setting_checked") and hasattr(self.app, "novel_setting_details"):
                    novel_selected = {n: self.app.novel_setting_details.get(n,'') for n, v in self.app.novel_setting_checked.items() if v}
                char_selected = {}
                if hasattr(self.app, "character_setting_checked") and hasattr(self.app, "character_setting_details"):
                    char_selected = {n: self.app.character_setting_details.get(n,'') for n, v in self.app.character_setting_checked.items() if v}
                settings_section = PromptBuilder.build_settings_content(novel_selected, char_selected)
            except Exception:
                settings_section = ""
            
            # 获取章节标题
            chapter_title = ""
            try:
                if current_idx is not None and 0 <= current_idx < len(self.app.chapter_list):
                    stored_title = self.app.chapter_list[current_idx].get("title", "")
                    chapter_title = PromptBuilder._format_chapter_display(current_idx + 1, stored_title)
            except Exception:
                chapter_title = ""
            
            # 获取当前编辑器内容
            current_content = self.app.content_text.get("1.0", tk.END).strip()
            
            # 构建用户提示词
            user_prompt = PromptBuilder.build_user_prompt(
                instruction=prompt,
                chapter_list=getattr(self.app, "chapter_list", []),
                current_index=current_idx,
                settings=settings_section,
                chapter_title=chapter_title,
                current_chapter_content=current_content
            )

            # 记录提示
            self.app._last_prompt = user_prompt
            
            print(f"[调试] 开始续写内容...")
            
            # 在后台线程中生成
            def generate_thread():
                try:
                    generated_text = self.generate_novel(
                        prompt=user_prompt,
                        novel_type=novel_type,
                        writing_style=writing_style,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    print(f"[调试] 续写完成，内容长度: {len(generated_text)} 字符")
                    
                    # 在主线程中更新UI
                    self.app.root.after(0, lambda: self._on_continue_success(generated_text, chapter_title))
                except Exception as e:
                    print(f"[错误] 续写内容时发生异常: {type(e).__name__}: {str(e)}")
                    traceback.print_exc()
                    error_msg = f"续写内容时发生错误: {str(e)}"
                    self.app.root.after(0, lambda: self._on_continue_success(f"❌ {error_msg}", ""))
            
            thread = threading.Thread(target=generate_thread, daemon=True)
            thread.start()
        except Exception as e:
            print(f"[错误] continue_content 方法异常: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
            if hasattr(self.app, "hide_loading_animation"):
                self.app.hide_loading_animation()
            self.app.modify_btn.config(state=tk.NORMAL, text="🖊️ 续写小说")
            messagebox.showerror("错误", f"发生错误: {str(e)}")

    def _post_generation_cleanup(self):
        """生成/续写后的通用清理工作"""
        try:
            if hasattr(self.app, "hide_loading_animation"):
                self.app.hide_loading_animation()
            self.app.generate_btn.config(state=tk.NORMAL, text="🚀 生成小说")
            self.app.modify_btn.config(state=tk.NORMAL, text="🖊️ 续写小说")
        except Exception:
            pass

    def _on_generate_success(self, generated_text, chapter_title):
        """生成成功的回调（覆盖模式）"""
        try:
            self._post_generation_cleanup()
            
            if generated_text.startswith("❌"):
                messagebox.showerror("错误", generated_text)
            else:
                # 覆盖内容
                self.app.content_text.delete("1.0", tk.END)
                self.app.content_text.insert("1.0", generated_text)
                
                if hasattr(self.app, "update_word_count"):
                    self.app.update_word_count()
                messagebox.showinfo("成功", "✅ 内容生成成功！")
        except Exception as e:
            traceback.print_exc()
            self._post_generation_cleanup()
            messagebox.showerror("错误", f"更新内容时发生错误: {str(e)}")

    def _on_continue_success(self, generated_text, chapter_title):
        """续写成功的回调（追加模式）"""
        try:
            self._post_generation_cleanup()
            
            if generated_text.startswith("❌"):
                messagebox.showerror("错误", generated_text)
            else:
                # 追加内容
                if self.app.content_text.get("1.0", tk.END).strip():
                    self.app.content_text.insert(tk.END, "\n\n" + generated_text)
                else:
                    self.app.content_text.insert("1.0", generated_text)
                
                if hasattr(self.app, "update_word_count"):
                    self.app.update_word_count()
                messagebox.showinfo("成功", "✅ 内容续写成功！")
        except Exception as e:
            traceback.print_exc()
            self._post_generation_cleanup()
            messagebox.showerror("错误", f"更新内容时发生错误: {str(e)}")
