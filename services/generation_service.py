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
        
    def _update_ai_config(self):
        """同步UI中的最新API配置到AI客户端"""
        try:
            api_base = self.app.api_base_var.get().strip() if hasattr(self.app, "api_base_var") else self.default_config.get('api_base')
            api_key = self.app.api_key_var.get().strip() if hasattr(self.app, "api_key_var") else self.default_config.get('api_key')
            model = self.app.model_var.get().strip() if hasattr(self.app, "model_var") else self.default_config.get('model')
            
            self.app.ai_client.update_config(api_key=api_key, api_base=api_base, model=model)
        except Exception as e:
            # 回退到默认配置
            print(f"[警告] 更新AI配置失败，使用默认值: {e}")
            self.app.ai_client.update_config(
                api_key=self.default_config.get('api_key'),
                api_base=self.default_config.get('api_base'),
                model=self.default_config.get('model')
            )

    def generate_novel(self, prompt, novel_type, writing_style, temperature, max_tokens):
        """使用AI客户端生成小说内容"""
        try:
            # 更新AI客户端配置
            self._update_ai_config()
            
            # 读取章节字数限制配置
            try:
                word_count = self.app.chapter_words_var.get() if hasattr(self.app, "chapter_words_var") else 3000
            except Exception:
                word_count = 3000
            
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
            writing_style = self.app.writing_style_text.get("1.0", tk.END).strip() if hasattr(self.app, "writing_style_text") else self.app.writing_style_var.get()
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
            
            # 组织章节策划信息
            chapter_plan = None
            try:
                climax = self.app.chapter_climax_text.get("1.0", tk.END).strip() if hasattr(self.app, 'chapter_climax_text') else ""
                hook = self.app.chapter_hook_text.get("1.0", tk.END).strip() if hasattr(self.app, 'chapter_hook_text') else ""
                if climax or hook:
                    chapter_plan = {"climax": climax, "hook": hook}
            except Exception:
                chapter_plan = None

            # 构建用户提示词（包含设定信息和章节标题）
            user_prompt = PromptBuilder.build_user_prompt(
                instruction=prompt,
                chapter_list=getattr(self.app, "chapter_list", []),
                current_index=current_idx,
                settings=settings_section,
                chapter_title=chapter_title,
                chapter_plan=chapter_plan
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
            writing_style = self.app.writing_style_text.get("1.0", tk.END).strip() if hasattr(self.app, "writing_style_text") else self.app.writing_style_var.get()
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

    def summarize_chapter(self):
        """总结当前章节内容"""
        try:
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
                messagebox.showwarning("提示", "请先选择要总结的章节！")
                return
            
            # 获取当前章节内容
            content = self.app.content_text.get("1.0", tk.END).strip()
            if not content:
                messagebox.showwarning("提示", "当前章节内容为空，无法总结！")
                return
            
            # 获取章节标题
            chapter_title = ""
            try:
                if 0 <= current_idx < len(self.app.chapter_list):
                    stored_title = self.app.chapter_list[current_idx].get("title", "")
                    chapter_title = PromptBuilder._format_chapter_display(current_idx + 1, stored_title)
            except Exception:
                chapter_title = f"第{current_idx + 1}章"
            
            # 禁用总结按钮
            if hasattr(self.app, "summarize_btn"):
                self.app.summarize_btn.config(state=tk.DISABLED, text="📝 正在总结...")
                self.app.root.update()
            
            # 显示加载动画
            if hasattr(self.app, "show_loading_animation"):
                self.app.show_loading_animation()
            
            print(f"[调试] 开始总结章节: {chapter_title}")
            
            # 在后台线程中生成总结
            def summarize_thread():
                try:
                    # 获取前后章节的上下文信息
                    prev_context = ""
                    next_context = ""
                    chapter_list = getattr(self.app, "chapter_list", [])
                    
                    # 获取前一章的上下文信息（如果有）
                    if current_idx > 0 and current_idx - 1 < len(chapter_list):
                        prev_chapter = chapter_list[current_idx - 1]
                        prev_title = PromptBuilder._format_chapter_display(current_idx, prev_chapter.get("title", ""))
                        prev_prompt = prev_chapter.get("prompt", "").strip()
                        prev_content = prev_chapter.get("content", "").strip()
                        
                        if prev_prompt:
                            # 优先使用创作提示
                            prev_context = f"前一章（{prev_title}）的创作提示：\n{prev_prompt}\n\n"
                        elif prev_content:
                            # 如果没有创作提示，使用内容的前200字作为参考
                            prev_content_preview = prev_content[:200] + "..." if len(prev_content) > 200 else prev_content
                            prev_context = f"前一章（{prev_title}）的内容片段：\n{prev_content_preview}\n\n"
                    
                    # 获取后一章的上下文信息（如果有）
                    if current_idx + 1 < len(chapter_list):
                        next_chapter = chapter_list[current_idx + 1]
                        next_title = PromptBuilder._format_chapter_display(current_idx + 2, next_chapter.get("title", ""))
                        next_prompt = next_chapter.get("prompt", "").strip()
                        next_content = next_chapter.get("content", "").strip()
                        
                        if next_prompt:
                            # 优先使用创作提示
                            next_context = f"后一章（{next_title}）的创作提示：\n{next_prompt}\n\n"
                        elif next_content:
                            # 如果没有创作提示，使用内容的前200字作为参考
                            next_content_preview = next_content[:200] + "..." if len(next_content) > 200 else next_content
                            next_context = f"后一章（{next_title}）的内容片段：\n{next_content_preview}\n\n"
                    
                    # 构建总结提示词
                    system_prompt = "你是一个专业的文学编辑，擅长提炼故事要点。请结合前后章节的上下文，用简洁的语言总结当前章节内容，突出关键情节和人物发展，确保总结与前后章节连贯。"
                    
                    context_section = ""
                    if prev_context or next_context:
                        context_section = "【上下文信息】\n"
                        if prev_context:
                            context_section += prev_context
                        if next_context:
                            context_section += next_context
                        context_section += "\n"
                    
                    user_prompt = f"""请为以下章节内容生成一个简短的总结，需要结合上下文信息：

{context_section}【当前章节】

章节标题：{chapter_title}

章节内容：
{content}

要求：
1. 总结要简洁明了，突出关键情节
2. 包含主要人物和事件
3. 结合前后章节的上下文，确保故事连贯性
4. 直接输出总结内容，不要包含"总结："等前缀
"""
                    
                    # 获取API配置
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
                    
                    # 更新AI客户端配置
                    self.app.ai_client.update_config(api_key=api_key, api_base=api_base, model=model)
                    
                    max_tokens = self.app.max_tokens_var.get() if hasattr(self.app, 'max_tokens_var') else 2000
                    
                    # 调用AI生成总结
                    summary = self.app.ai_client.generate_content(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        temperature=0.7,
                        max_tokens=max_tokens
                    )
                    
                    # 统计字数（中文字符数）
                    import re
                    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', summary))
                    total_chars = len(summary)
                    non_chinese_chars = total_chars - chinese_chars
                    
                    print(f"[调试] 总结返回统计:")
                    print(f"  - 总字符数: {total_chars}")
                    print(f"  - 中文字数: {chinese_chars}")
                    print(f"  - 非中文字符数: {non_chinese_chars}")
                    print(f"[调试] 总结返回内容:")
                    print("=" * 50)
                    print(repr(summary))  # 使用repr显示原始字符串，包括转义字符
                    print("=" * 50)
                    print(summary)  # 显示实际内容
                    print("=" * 50)
                    
                    # 在主线程中更新UI
                    self.app.root.after(0, lambda: self._on_summarize_success(summary, current_idx, chapter_title))
                except Exception as e:
                    print(f"[错误] 总结章节时发生异常: {type(e).__name__}: {str(e)}")
                    traceback.print_exc()
                    error_msg = f"总结章节时发生错误: {str(e)}"
                    self.app.root.after(0, lambda: self._on_summarize_error(error_msg))
            
            thread = threading.Thread(target=summarize_thread, daemon=True)
            thread.start()
        except Exception as e:
            print(f"[错误] summarize_chapter 方法异常: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
            if hasattr(self.app, "hide_loading_animation"):
                self.app.hide_loading_animation()
            # 恢复总结按钮
            if hasattr(self.app, "summarize_btn"):
                self.app.summarize_btn.config(state=tk.NORMAL, text="📝 总结章节")
            # 恢复生成按钮
            if hasattr(self.app, "generate_btn"):
                self.app.generate_btn.config(state=tk.NORMAL, text="🚀 生成小说")
            messagebox.showerror("错误", f"发生错误: {str(e)}")
    
    def _on_summarize_success(self, summary, chapter_idx, chapter_title):
        """总结成功的回调"""
        try:
            if hasattr(self.app, "hide_loading_animation"):
                self.app.hide_loading_animation()
            
            # 恢复总结按钮
            if hasattr(self.app, "summarize_btn"):
                self.app.summarize_btn.config(state=tk.NORMAL, text="📝 总结章节")
            
            # 恢复生成按钮
            if hasattr(self.app, "generate_btn"):
                self.app.generate_btn.config(state=tk.NORMAL, text="🚀 生成小说")
            
            # 保存总结到章节数据
            if 0 <= chapter_idx < len(self.app.chapter_list):
                self.app.chapter_list[chapter_idx]["summary"] = summary.strip()
                
                # 持久化到文件
                if hasattr(self.app, "novel_service"):
                    self.app.novel_service._persist_chapters_to_novel()
                
                # 刷新章节总结显示（如果小说设置页面已打开）
                if hasattr(self.app, "refresh_chapter_summaries"):
                    self.app.refresh_chapter_summaries()
                
                messagebox.showinfo("成功", f"✅ 章节总结完成！\n\n{chapter_title}\n\n{summary.strip()}")
            else:
                messagebox.showerror("错误", "章节索引无效")
        except Exception as e:
            traceback.print_exc()
            # 确保恢复按钮状态
            if hasattr(self.app, "summarize_btn"):
                self.app.summarize_btn.config(state=tk.NORMAL, text="📝 总结章节")
            if hasattr(self.app, "generate_btn"):
                self.app.generate_btn.config(state=tk.NORMAL, text="🚀 生成小说")
            messagebox.showerror("错误", f"保存总结时发生错误: {str(e)}")
    
    def _on_summarize_error(self, error_msg):
        """总结失败的回调"""
        if hasattr(self.app, "hide_loading_animation"):
            self.app.hide_loading_animation()
        # 恢复总结按钮
        if hasattr(self.app, "summarize_btn"):
            self.app.summarize_btn.config(state=tk.NORMAL, text="📝 总结章节")
        # 恢复生成按钮
        if hasattr(self.app, "generate_btn"):
            self.app.generate_btn.config(state=tk.NORMAL, text="🚀 生成小说")
        messagebox.showerror("错误", error_msg)

    def generate_outline(self):
        """AI 生成大纲（标题、概述、高潮、钩子）"""
        try:
            # 检查是否选择了章节
            current_idx = None
            if hasattr(self.app, "chapter_listbox"):
                sel = self.app.chapter_listbox.curselection()
                if sel:
                    current_idx = sel[0]
            
            if current_idx is None:
                messagebox.showwarning("提示", "请先选择要生成大纲的章节槽位！")
                return

            # 获取设置
            settings_section = ""
            try:
                # 获取选中的设定
                novel_selected = {n: self.app.novel_setting_details.get(n,'') for n, v in self.app.novel_setting_checked.items() if v} if hasattr(self.app, "novel_setting_checked") else {}
                char_selected = {n: self.app.character_setting_details.get(n,'') for n, v in self.app.character_setting_checked.items() if v} if hasattr(self.app, "character_setting_checked") else {}
                settings_section = PromptBuilder.build_settings_content(novel_selected, char_selected)
            except Exception:
                settings_section = ""

            # 获取当前标题（如果有）作为参考
            current_title = self.app.chapter_title_var.get().strip() if hasattr(self.app, 'chapter_title_var') else ""
            
            # 构建提示词
            user_prompt = PromptBuilder.build_outline_prompt(
                chapter_title=current_title,
                chapter_list=getattr(self.app, "chapter_list", []),
                current_index=current_idx,
                settings=settings_section
            )

            # 锁定 UI
            if hasattr(self.app, "show_loading_animation"):
                self.app.show_loading_animation()
            
            # 禁用按钮提示
            print(f"[信息] 正在为第{current_idx+1}章生成构思大纲...")
            
            def outline_thread():
                try:
                    max_tokens = self.app.max_tokens_var.get() if hasattr(self.app, 'max_tokens_var') else 2000
                    
                    # 使用配置的 token 限制
                    generated_text = self.generate_novel(
                        prompt=user_prompt,
                        novel_type=self.app.novel_type_var.get(),
                        writing_style=self.app.writing_style_text.get("1.0", tk.END).strip() if hasattr(self.app, "writing_style_text") else self.app.writing_style_var.get(),
                        temperature=0.8,
                        max_tokens=max_tokens
                    )
                    
                    # 解析结果
                    self.app.root.after(0, lambda: self._on_outline_success(generated_text))
                except Exception as e:
                    self.app.root.after(0, lambda: self._on_outline_error(str(e)))
            
            thread = threading.Thread(target=outline_thread, daemon=True)
            thread.start()
            
        except Exception as e:
            messagebox.showerror("错误", f"启动大纲生成失败: {e}")

    def _on_outline_success(self, text):
        """解析并填充大纲"""
        try:
            if hasattr(self.app, "hide_loading_animation"):
                self.app.hide_loading_animation()
            
            # 正则提取
            import re
            
            def extract(tag, content):
                pattern = rf"【{tag}】：?(.*?)(?=【|$)"
                match = re.search(pattern, content, re.DOTALL)
                return match.group(1).strip() if match else ""

            ch_title = extract("章节标题", text)
            ch_summary = extract("内容概述", text)
            ch_climax = extract("章节高潮", text)
            ch_hook = extract("章节钩子", text)
            
            # 填入 UI
            if ch_title and hasattr(self.app, 'chapter_title_var'):
                self.app.chapter_title_var.set(ch_title)
            if ch_summary and hasattr(self.app, 'prompt_text'):
                self.app.prompt_text.delete("1.0", tk.END)
                self.app.prompt_text.insert("1.0", ch_summary)
            if ch_climax and hasattr(self.app, 'chapter_climax_text'):
                self.app.chapter_climax_text.delete("1.0", tk.END)
                self.app.chapter_climax_text.insert("1.0", ch_climax)
            if ch_hook and hasattr(self.app, 'chapter_hook_text'):
                self.app.chapter_hook_text.delete("1.0", tk.END)
                self.app.chapter_hook_text.insert("1.0", ch_hook)

            messagebox.showinfo("成功", "✅ 章节大纲构思完成！\n已填充至界面，请根据需要进行微调。")
        except Exception as e:
            messagebox.showerror("解析失败", f"大纲解析出错：{e}")

    def _on_outline_error(self, err):
        if hasattr(self.app, "hide_loading_animation"):
            self.app.hide_loading_animation()
        messagebox.showerror("生成失败", f"AI 生成大纲失败: {err}")

    def modify_content(self):
        """AI 修改正文（独立于大纲，直接基于正文和指令修改）"""
        try:
            # 1. 获取正文内容和修改指令
            current_content = self.app.content_text.get("1.0", tk.END).strip()
            
            # 从新的文本框中获取指令
            placeholder = "输入整体修改意见，或直接描述如何改进当前章节内容（如：增加心理描写、精简开场等）..."
            instruction = self.app.modify_instruction_entry.get("1.0", tk.END).strip()
            
            if not current_content:
                messagebox.showwarning("提示", "当前正文为空，无法修改！")
                return
            
            if not instruction or instruction == placeholder:
                messagebox.showwarning("提示", "请输入修改要求（如：增加心理描写、精简开场、更换风格等）")
                return

            # 2. 准备配置和设定
            novel_type = self.app.novel_type_var.get()
            writing_style = self.app.writing_style_text.get("1.0", tk.END).strip() if hasattr(self.app, "writing_style_text") else self.app.writing_style_var.get()
            
            # 显示加载动画并禁用按钮
            if hasattr(self.app, "show_loading_animation"):
                self.app.show_loading_animation()
            
            # 尝试通过 app 获取 modify_content_btn
            if hasattr(self.app, "modify_content_btn"):
                self.app.modify_content_btn.config(state=tk.DISABLED, text="🪄 正在修改中...")
            
            # 组织设定
            settings_section = ""
            try:
                # 重新组织设定详情以供修改参考
                novel_selected = {n: self.app.novel_setting_details.get(n,'') for n, v in self.app.novel_setting_checked.items() if v} if hasattr(self.app, "novel_setting_checked") else {}
                char_selected = {n: self.app.character_setting_details.get(n,'') for n, v in self.app.character_setting_checked.items() if v} if hasattr(self.app, "character_setting_checked") else {}
                settings_section = PromptBuilder.build_settings_content(novel_selected, char_selected)
            except Exception:
                settings_section = ""

            # 3. 构建提示词
            user_prompt = PromptBuilder.build_modification_prompt(
                content=current_content,
                instruction=instruction,
                settings=settings_section
            )

            # 4. 后台执行
            def modify_thread():
                try:
                    result = self.generate_novel(
                        prompt=user_prompt,
                        novel_type=novel_type,
                        writing_style=writing_style,
                        temperature=self.app.temperature_var.get(),
                        max_tokens=self.app.max_tokens_var.get()
                    )
                    
                    # 成功回调
                    def on_success():
                        self._post_generation_cleanup()
                        if hasattr(self.app, "modify_content_btn"):
                            self.app.modify_content_btn.config(state=tk.NORMAL, text="🪄 AI 修改正文")
                        
                        if result.startswith("❌"):
                            messagebox.showerror("错误", result)
                        else:
                            # 替换当前正文
                            self.app.content_text.delete("1.0", tk.END)
                            self.app.content_text.insert("1.0", result)
                            if hasattr(self.app, "update_word_count"):
                                self.app.update_word_count()
                            messagebox.showinfo("成功", "✅ 正文修改/润色完成！")

                    self.app.root.after(0, on_success)
                except Exception as e:
                    self.app.root.after(0, lambda: self._on_modify_error(str(e)))
            
            thread = threading.Thread(target=modify_thread, daemon=True)
            thread.start()
            
        except Exception as e:
            traceback.print_exc()
            if hasattr(self.app, "modify_content_btn"):
                self.app.modify_content_btn.config(state=tk.NORMAL, text="🪄 AI 修改正文")
            messagebox.showerror("错误", f"修改启动失败: {e}")

    def _on_modify_error(self, err):
        self._post_generation_cleanup()
        if hasattr(self.app, "modify_content_btn"):
            self.app.modify_content_btn.config(state=tk.NORMAL, text="🪄 AI 修改正文")
        messagebox.showerror("生成失败", f"AI 修改正文失败: {err}")
    
    def finalize_content(self):
        """
        定稿逻辑：两步生成法
        1. 仅凭本章正文生成 [本章摘要]
        2. 全局摘要 = 前一章全局摘要 + 本章摘要 (由 AI 整合更新)
        """
        try:
            chapter_list = self.app.chapter_list
            current_idx = self.app.current_chapter_index
            
            if current_idx is None:
                messagebox.showwarning("提示", "请先选择一个章节进行定稿")
                return

            # 1. 准备数据，确保同步最新编辑器内容
            current_content = ""
            if hasattr(self.app, "content_text"):
                current_content = self.app.content_text.get("1.0", tk.END).strip()
                if 0 <= current_idx < len(chapter_list):
                    chapter_list[current_idx]["content"] = current_content
            
            if not current_content:
                messagebox.showwarning("提示", "当前章节正文为空，无法定稿。")
                return

            # 2. 界面锁定与按钮禁用
            if hasattr(self.app, "show_loading_animation"):
                self.app.show_loading_animation()
            
            if hasattr(self.app, "finalize_btn"):
                self.app.finalize_btn.config(state=tk.DISABLED, text="⌛ 正在分析本章...")
            if hasattr(self.app, "generate_summary_btn"):
                self.app.generate_summary_btn.config(state=tk.DISABLED, text="⌛ 正在生成本章摘要...")

            # 获取前一章节的全局摘要作为基础
            old_global = ""
            if current_idx > 0:
                old_global = chapter_list[current_idx-1].get("global_summary", "").strip()
            
            # 如果前面都没有全局摘要，尝试从小说设置中获取
            if not old_global and hasattr(self.app, "novel_outline_text"):
                old_global = self.app.novel_outline_text.get("1.0", tk.END).strip()

            def finalize_thread():
                try:
                    # 更新 API 配置
                    self._update_ai_config()
                    
                    # --- 第一步：生成本章摘要 ---
                    step1_prompt = PromptBuilder.build_chapter_summary_prompt(current_content)
                    ch_summary = self.app.ai_client.generate_content(
                        system_prompt="你是一位专业的小说编辑，请精准提炼章节核心剧情。",
                        user_prompt=step1_prompt,
                        temperature=0.3,
                        max_tokens=1000
                    )
                    
                    if ch_summary.startswith("❌"):
                        self.app.root.after(0, lambda: messagebox.showerror("第一步失败", ch_summary))
                        return

                    # --- 第二步：更新全局摘要 ---
                    self.app.root.after(0, lambda: self.app.finalize_btn.config(text="⌛ 正在更新全局提要...") if hasattr(self.app, "finalize_btn") else None)
                    
                    step2_prompt = PromptBuilder.build_global_summary_update_prompt(old_global, ch_summary)
                    global_summary = self.app.ai_client.generate_content(
                        system_prompt="你是一位资深文学顾问，负责维护小说的全文主线一致性。",
                        user_prompt=step2_prompt,
                        temperature=0.3,
                        max_tokens=2000
                    )

                    def on_success():
                        self._post_generation_cleanup()
                        if hasattr(self.app, "finalize_btn"):
                            self.app.finalize_btn.config(state=tk.NORMAL, text="📝 章节定稿")
                        if hasattr(self.app, "generate_summary_btn"):
                            self.app.generate_summary_btn.config(state=tk.NORMAL, text="✨ 生成/更新定稿摘要")
                        
                        if global_summary.startswith("❌"):
                            messagebox.showerror("第二步失败", global_summary)
                            return
                        
                        # 更新显示
                        if hasattr(self.app, "global_summary_text"):
                            self.app.global_summary_text.delete("1.0", tk.END)
                            self.app.global_summary_text.insert("1.0", global_summary.strip())
                            
                        if hasattr(self.app, "recent_summary_text"):
                            self.app.recent_summary_text.delete("1.0", tk.END)
                            self.app.recent_summary_text.insert("1.0", ch_summary.strip())
                            
                        # 更新章节元数据
                        if 0 <= current_idx < len(self.app.chapter_list):
                            self.app.chapter_list[current_idx]["global_summary"] = global_summary.strip()
                            self.app.chapter_list[current_idx]["summary"] = ch_summary.strip()
                            
                            # 角色状态暂时不自动生成，由用户手动维护或后续增加独立功能
                            
                            # 同步到配置文件
                            if hasattr(self.app, "novel_service"):
                                self.app.novel_service._persist_chapters_to_novel()
                                
                            # 可选：也同步更新到“小说设置”中的剧情主线
                            if hasattr(self.app, "novel_outline_text"):
                                self.app.novel_outline_text.delete("1.0", tk.END)
                                self.app.novel_outline_text.insert("1.0", global_summary.strip())
                        
                        messagebox.showinfo("成功", "✅ 章节定稿完成！\n\n1. 已生成本章独立摘要。\n2. 已基于前文更新全局摘要。")

                    self.app.root.after(0, on_success)
                    
                except Exception as e:
                    traceback.print_exc()
                    self.app.root.after(0, lambda: messagebox.showerror("系统错误", str(e)))
                    self.app.root.after(0, self._post_generation_cleanup)

            threading.Thread(target=finalize_thread, daemon=True).start()

        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("错误", str(e))

    def _on_finalize_error(self, err):
        self._post_generation_cleanup()
        if hasattr(self.app, "finalize_btn"):
            self.app.finalize_btn.config(state=tk.NORMAL, text="📝 章节定稿")
        messagebox.showerror("失败", f"定稿生成失败: {err}")
