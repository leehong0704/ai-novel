"""
提示词构建模块
负责构建系统提示词和用户提示词
"""
import re

class PromptBuilder:
    """提示词构建器类"""

    @staticmethod
    def build_system_prompt(novel_type, writing_style, word_count=2000):
        """
        构建系统提示词
        
        Args:
            novel_type (str): 小说类型
            writing_style (str): 写作风格
            word_count (int): 章节字数，默认2000
            
        Returns:
            str: 格式化后的系统提示词
        """
        system_prompt = f"""你是一位专业的小说创作助手。请根据用户的要求创作小说内容。
    
    创作要求：
    1. 小说类型：{novel_type}
    2. 写作风格：{writing_style}
    3. 严格按照【当前章节创作提示】写作小说内容
    4. 注意与前后章节的连贯性，做好承上启下
    5. 请直接输出小说标题和正文内容，不要添加任何说明性文字
    6. 每个章节字数在{word_count}字左右
    """
        return system_prompt

    @staticmethod
    def _strip_chapter_prefix(title_text):
        """移除如 '第12章' 前缀，保留纯标题"""
        try:
            text = str(title_text).strip()
            # 匹配前缀 '第 数字 章' 可带空格
            text = re.sub(r'^\s*第\s*\d+\s*章\s*', '', text)
            return text.strip()
        except Exception:
            return title_text

    @staticmethod
    def _format_chapter_display(index, stored_title):
        """渲染列表显示为 '第X章 标题'"""
        base = f"第{index}章"
        clean = PromptBuilder._strip_chapter_prefix(stored_title or "")
        return base if not clean else f"{base} {clean}"

    @staticmethod
    def get_previous_chapter_prompt(chapter_list, current_index):
        """
        获取前一章的创作提示
        
        Args:
            chapter_list (list): 章节列表
            current_index (int): 当前章节索引
            
        Returns:
            str: 前一章的创作提示，如果没有则返回空字符串
        """
        if not chapter_list or current_index is None or current_index <= 0:
            return ""
            
        try:
            prev_chapter = chapter_list[current_index - 1]
            prev_prompt = (prev_chapter.get("prompt", "") or "").strip()
            prev_title = prev_chapter.get("title", "")
            
            if prev_prompt:
                title_disp = PromptBuilder._format_chapter_display(current_index, prev_title)
                return f"{title_disp} 的创作提示：\n{prev_prompt}"
            return ""
        except Exception:
            return ""
    
    @staticmethod
    def get_next_chapter_prompt(chapter_list, current_index):
        """
        获取后一章的创作提示
        
        Args:
            chapter_list (list): 章节列表
            current_index (int): 当前章节索引
            
        Returns:
            str: 后一章的创作提示，如果没有则返回空字符串
        """
        if not chapter_list or current_index is None:
            return ""
            
        try:
            # 检查是否有下一章
            if current_index + 1 < len(chapter_list):
                next_chapter = chapter_list[current_index + 1]
                next_prompt = (next_chapter.get("prompt", "") or "").strip()
                next_title = next_chapter.get("title", "")
                
                if next_prompt:
                    title_disp = PromptBuilder._format_chapter_display(current_index + 2, next_title)
                    return f"{title_disp} 的内容提示：\n{next_prompt}"
            return ""
        except Exception:
            return ""

    @staticmethod
    def build_settings_content(novel_settings, character_settings):
        """
        构建设定内容字符串
        
        Args:
            novel_settings (dict): 小说设定字典 {name: detail}
            character_settings (dict): 人物设定字典 {name: detail}
            
        Returns:
            str: 格式化后的设定内容
        """
        lines = []
        if novel_settings:
            lines.append("【小说设定】")
            for n, v in novel_settings.items():
                lines.append(f"- {n}: {v}")
                
        if character_settings:
            lines.append("【人物设定】")
            for n, v in character_settings.items():
                lines.append(f"- {n}: {v}")
                
        return "\n".join(lines).strip()

    @staticmethod
    def build_user_prompt(instruction, chapter_list=None, current_index=None, settings="", chapter_title="", current_chapter_content=""):
        """
        构建用户提示词
        
        Args:
            instruction (str): 用户输入的章节内容提示/续写指导
            chapter_list (list, optional): 章节列表
            current_index (int, optional): 当前章节索引
            settings (str, optional): 相关设定（小说设定、人物设定等）
            chapter_title (str, optional): 当前章节标题
            current_chapter_content (str, optional): 当前章节已有的内容（用于续写）
            
        Returns:
            str: 格式化后的用户提示词
        """
        parts = []
        
        # 1. 设定信息（如果有）
        if settings:
            parts.append(f"相关设定：\n{settings}")
        
        # 2. 前一章的创作提示
        prev_prompt = PromptBuilder.get_previous_chapter_prompt(chapter_list, current_index)
        if prev_prompt:
            parts.append(f"前一章创作提示：\n{prev_prompt}")
        
        # 3. 当前章节信息
        if chapter_title:
            parts.append(f"当前章节标题：{chapter_title}")
        
        # 4. 当前章节已有内容（续写时）
        if current_chapter_content:
            parts.append(f"当前章节已有内容：\n{current_chapter_content}")
        
        # 5. 当前章节的写作指导/提示
        if instruction:
            parts.append(f"当前章节创作提示：\n{instruction}")
        
        # 6. 后一章的内容提示
        next_prompt = PromptBuilder.get_next_chapter_prompt(chapter_list, current_index)
        if next_prompt:
            parts.append(f"后续章节提示（供参考，确保内容连贯）：\n{next_prompt}")
        
        # 7. 总结指令
        reference_parts = []
        if settings:
            reference_parts.append("【相关设定】")
        if prev_prompt:
            reference_parts.append("【前一章创作提示】")
        if instruction:
            reference_parts.append("【当前章节创作提示】")
        
        if reference_parts:
            ref_str = "、".join(reference_parts)
            parts.append(f"请根据上述{ref_str}，创作本章节内容。注意与前后章节保持连贯，为后续章节做好铺垫。")
        else:
            parts.append("请创作本章节内容。注意与前后章节保持连贯，为后续章节做好铺垫。")
        
        return "\n\n".join(parts)

