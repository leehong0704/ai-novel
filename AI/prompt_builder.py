"""
提示词构建模块
负责构建系统提示词和用户提示词
"""
import re
import datetime

class PromptBuilder:
    """提示词构建器类"""

    @staticmethod
    def build_system_prompt(novel_type, writing_style, word_count=4000):
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
    5. 请直接输出正文内容，不要包含标题或任何说明性文字
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
    def build_user_prompt(instruction, chapter_list=None, current_index=None, settings="", chapter_title="", current_chapter_content="", chapter_plan=None):
        """
        构建用户提示词
        
        Args:
            instruction (str): 用户输入的章节内容提示/续写指导
            chapter_list (list, optional): 章节列表
            current_index (int, optional): 当前章节索引
            settings (str, optional): 相关设定（小说设定、人物设定等）
            chapter_title (str, optional): 当前章节标题
            current_chapter_content (str, optional): 当前章节已有的内容（用于续写）
            chapter_plan (dict, optional): 章节策划信息（高潮、钩子、场景）
            
        Returns:
            str: 格式化后的用户提示词
        """
        parts = []
        
        # 1. 设定信息（如果有）
        if settings:
            parts.append(f"【相关设定】\n{settings}")
        
        # 2. 前一章的创作提示
        prev_prompt = PromptBuilder.get_previous_chapter_prompt(chapter_list, current_index)
        if prev_prompt:
            parts.append(f"【前一章创作提示】\n{prev_prompt}")
        
        # 3. 章节策划（高潮、钩子、概述）
        if chapter_plan or instruction:
            plan_str = ""
            if chapter_plan and chapter_plan.get("climax"): plan_str += f"- 本章高潮：{chapter_plan['climax']}\n"
            if chapter_plan and chapter_plan.get("hook"): plan_str += f"- 本章钩子：{chapter_plan['hook']}\n"
            
            # 使用 instruction (即内容概述)
            if instruction:
                plan_str += f"- 内容概述：\n{instruction}\n"
                
            if plan_str:
                parts.append(f"【本章剧情策划】\n{plan_str.strip()}")

        # 5. 前三章摘要 (增强上下文)
        if chapter_list and current_index is not None and current_index > 0:
            sum_parts = []
            cur_start = max(0, current_index - 3)
            for i in range(cur_start, current_index):
                ch = chapter_list[i]
                ch_title = ch.get('title', f'第{i+1}章')
                # 优先使用精炼摘要，无摘要则使用原概述
                ch_sum = ch.get('summary', '').strip() or ch.get('prompt', '').strip()
                if ch_sum:
                    sum_parts.append(f"- {ch_title}剧情: {ch_sum}")
                    
                    # 仅附加本章后的关系快照（状态已累加至档案，此处移除以去重）
                    ch_rel = ch.get('char_relations', '').strip()
                    if ch_rel:
                        sum_parts.append(f"  * 角色关系变动: {ch_rel}")
            
            if sum_parts:
                parts.append("【前序章节背景（剧情、状态及关系回顾）】\n" + "\n".join(sum_parts))

        # 6. 当前章节已有内容（续写时）
        if current_chapter_content:
            parts.append(f"【当前章节已有内容】：\n{current_chapter_content}")
        
        # 7. 后一章的内容提示
        next_prompt = PromptBuilder.get_next_chapter_prompt(chapter_list, current_index)
        if next_prompt:
            parts.append(f"【后续章节剧情参考】：\n{next_prompt}")
        
        # 8. 总结指令
        reference_parts = []
        if settings: reference_parts.append("相关设定")
        if prev_prompt: reference_parts.append("前一章创作提示")
        if chapter_plan or instruction: reference_parts.append("本章剧情策划")
        
        if reference_parts:
            ref_str = "、".join(reference_parts)
            parts.append(f"请根据上述{ref_str}以及前三章的剧情回顾，创作本章节内容。要求情节跌宕起伏，逻辑自洽，注意与前文紧密承接。")
        else:
            parts.append("请创作本章节内容。注意与前三章剧情回顾保持连贯，为后续章节做好铺垫。")
        
        return "\n\n".join(parts)

    @staticmethod
    def build_outline_prompt(chapter_title, chapter_list=None, current_index=None, settings=""):
        """
        构建生成章节大纲/概述的提示词
        
        Args:
            chapter_title (str): 当前章节标题
            chapter_list (list, optional): 已有章节列表
            current_index (int, optional): 当前章节索引
            settings (str, optional): 相关设定
            
        Returns:
            str: 格式化后的提示词
        """
        parts = []
        
        if settings:
            parts.append(f"【背景设定】\n{settings}")
            
        # 提供前三章的摘要作为上下文
        if chapter_list and current_index is not None and current_index > 0:
            context_parts = ["【前序章节剧情回顾（最近3章）】"]
            start = max(0, current_index - 3)
            for i in range(start, current_index):
                ch = chapter_list[i]
                title = ch.get('title', f'第{i+1}章')
                # 优先使用本章摘要
                summary = ch.get('summary', '').strip() or ch.get('prompt', '（无概述）')
                context_parts.append(f"- {title}: {summary}")
            parts.append("\n".join(context_parts))

        parts.append(f"【当前任务】\n请为新章节构思详细的剧情大纲。要求：\n1. 情节与前文高度连贯且符合逻辑。\n2. 充满戏剧张力，能吸引读者。")
        
        parts.append("请按以下格式输出（严格按此标签分隔）：\n【章节标题】：（一个吸引人的标题）\n【内容概述】：（在这里详细写本章发生的故事）\n【章节高潮】：（本章最精彩的一幕）\n【章节钩子】：（本章结尾留下的悬念）")
        
        return "\n\n".join(parts)
    @staticmethod
    def build_modification_prompt(content, instruction, settings=""):
        """
        构建正文修改/润色的提示词
        
        Args:
            content (str): 待修改的正文内容
            instruction (str): 具体的修改要求
            settings (str, optional): 相关世界观/人物设定背景
            
        Returns:
            str: 格式化后的提示词
        """
        parts = []
        if settings:
            parts.append(f"【参考设定】\n{settings}")
            
        parts.append(f"【原正文内容】\n{content}")
        parts.append(f"【整体修改要求】\n{instruction if instruction else '按照文中内联指令进行局部微调或全文润色'}")
        
        parts.append("【处理指令】\n1. 如果正文中包含形如 【修改建议】 或 [[建议]] 的标记，请将该标记及其对应的片段按照建议进行重写。\n2. 保持原有的人设和叙事逻辑。\n3. 直接输出修改或润色后的完整正文内容。\n4. 输出中严禁保留任何原有的指令标记或说明性括号。")
        
        return "\n\n".join(parts)

    @staticmethod
    def build_chapter_summary_prompt(content):
        """
        第一步：根据正文生成本章摘要
        """
        parts = ["【创作定稿任务：本章摘要生成】"]
        parts.append(f"请根据以下本章正文内容，生成一段精准、详尽的章节摘要（约200-400字），要求覆盖章节的核心剧情、转折和重要细节，以便作为后续创作的上下文参考。")
        parts.append(f"【本章正文素材】：\n{content}")
        parts.append("直接输出摘要内容即可，无需额外说明。")
        return "\n\n".join(parts)

    @staticmethod
    def build_global_summary_update_prompt(old_global, chapter_summary):
        """
        第二步：合并旧全局摘要和新本章摘要，生成新的全局摘要
        """
        parts = ["【创作定稿任务：更新全局摘要】"]
        parts.append("你现在的任务是更新整部小说的全文提要（全局摘要）。")
        parts.append(f"【之前的全局摘要】：\n{old_global or '（暂无）'}")
        parts.append(f"【本章新增摘要内容】：\n{chapter_summary}")
        parts.append("【处理指令】\n1. 请将本章新增的摘要内容合并到原有的全局摘要中，形成一个完整的、最新的全书剧情梗概。\n2. 保持叙事连贯性，精炼语言。")
        parts.append("请直接输出更新后的完整全局摘要。")
        return "\n\n".join(parts)

    @staticmethod
    def build_char_status_update_prompt(old_status, chapter_summary, chapter_num):
        """
        第三步：增量更新人物经历日志（AI 输出简化格式：@角色名#变动内容）
        """
        parts = ["【创作定稿任务：提炼人物经历变动】"]
        parts.append("任务：根据本章剧情精华，提炼各角色的关键经历变动。")
        parts.append(f"【参考历史经历】：\n{old_status or '（暂无）'}")
        parts.append(f"【本章剧情精华】：\n{chapter_summary}")
        parts.append(f"【当前章节】：第{chapter_num}章")
        parts.append("【输出解析格式（极其重要）】\n"
                     "1. 【一章一人一条】：每名角色在本章只能有且仅有一行输出。严禁为同一角色生成多行记录。\n"
                     "2. 【全景汇总】：请用简洁的语言在一个记录块中汇总该角色在本章的所有关键点，多个事件用分号（；）隔开。\n"
                     "3. 【禁止合并人名】：严禁将多个角色名字合并在 @ 后面（如：@杨帆和李媛媛# 是错误的）。\n"
                     "4. 【格式】：@角色名#经历汇总描述\n"
                     "5. 【正确示例】：@杨帆#进入英华高中开始寄宿生活；在篮球场展现出色素质；英语摸底考不及格但有进步，接受李媛媛一对一补习。\n"
                     "6. 注意：描述中不要再包含 @ 符号，也不要包含章节号。")
        parts.append("请直接输出由 <RECORDS> 标签包裹的、每人只有一行的记录列表。")
        return "\n\n".join(parts)

    @staticmethod
    def build_char_relations_update_prompt(old_relations, chapter_summary, chapter_num):
        """
        第四步：增量更新人物关系演变
        """
        parts = ["【创作定稿任务：更新人物关系网络】"]
        parts.append("任务：维护人物间的关系动态（恩怨、情感、派系）。")
        parts.append(f"【原有关系网络】：\n{old_relations or '（暂无）'}")
        parts.append(f"【本章剧情精华】：\n{chapter_summary}")
        parts.append(f"【当前章节】：第{chapter_num}章")
        parts.append("【关键指令】\n1. 仅提取本章产生的核心关系变动（如敌友转折、重要邂逅）。\n2. **强制要求**：本章的新增记录必须【极简且短小】。\n3. 严格遵循格式：第{chapter_num}章：[简短描述]。\n4. 保持历史记录不变，仅在末尾做增量补充。")
        parts.append("请直接输出更新后的完整人物关系网络。")
        return "\n\n".join(parts)
