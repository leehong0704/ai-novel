"""
数据持久化服务
负责所有数据的保存和加载操作，包括章节数据、小说配置等
将持久化逻辑与业务逻辑分离，避免混淆
"""

import os
import configparser
import traceback


class PersistenceService:
    """数据持久化服务类"""
    
    def __init__(self, app):
        """
        初始化持久化服务
        Args:
            app: NovelGeneratorApp实例
        """
        self.app = app
    
    # ==================== 章节数据持久化 ====================
    
    def save_chapters(self):
        """
        将章节列表持久化到当前小说目录
        保存内容包括：
            - novel.ini 中的章节索引、标题、提示
            - chapters/ 目录下的章节文件
        """
        try:
            print(f"[调试] PersistenceService.save_chapters 开始")
            print(f"  - hasattr current_novel_dir: {hasattr(self.app, 'current_novel_dir')}")
            if hasattr(self.app, 'current_novel_dir'):
                print(f"  - current_novel_dir: {self.app.current_novel_dir}")
            
            if not hasattr(self.app, 'current_novel_dir') or not self.app.current_novel_dir:
                print(f"[调试] current_novel_dir 未设置，跳过保存")
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
    
    def load_chapters(self, novel_ini_path):
        """
        从小说配置文件加载章节列表
        Args:
            novel_ini_path: novel.ini 文件路径
        Returns:
            章节列表，格式为 [{"title": "...", "content": "...", "prompt": "..."}, ...]
        """
        try:
            config = configparser.ConfigParser()
            config.read(novel_ini_path, encoding="utf-8")
            novel_dir = os.path.dirname(novel_ini_path)
            
            chapters_path = "chapters"
            if "META" in config:
                chapters_path = config["META"].get("chapters_path", chapters_path) or "chapters"
            chapters_dir = os.path.join(novel_dir, chapters_path)
            
            # 读取章节索引
            indices = []
            if "CHAPTERS" in config:
                try:
                    indices = sorted((int(k) for k in config["CHAPTERS"].keys()), key=int)
                except Exception:
                    indices = []
            
            # 回退：若无 CHAPTERS，仅根据 CHAPTER_TITLES 数量构造索引
            if not indices and "CHAPTER_TITLES" in config:
                try:
                    indices = sorted((int(k) for k in config["CHAPTER_TITLES"].keys()), key=int)
                except Exception:
                    indices = []
            
            # 加载章节数据
            chapter_list = []
            for idx in indices:
                title = ""
                fname = f"chapter_{idx:03d}.txt"
                
                # 读取标题
                if "CHAPTER_TITLES" in config and str(idx) in config["CHAPTER_TITLES"]:
                    title = config["CHAPTER_TITLES"][str(idx)]
                
                # 读取提示
                prompt = ""
                if "CHAPTER_PROMPTS" in config and str(idx) in config["CHAPTER_PROMPTS"]:
                    prompt = config["CHAPTER_PROMPTS"][str(idx)]
                
                # 读取内容
                content = ""
                if "CHAPTERS" in config and str(idx) in config["CHAPTERS"]:
                    fname = config["CHAPTERS"][str(idx)]
                
                chapter_file = os.path.join(chapters_dir, fname)
                if os.path.exists(chapter_file):
                    try:
                        with open(chapter_file, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                        # 跳过首行标题和空行
                        if len(lines) > 2:
                            content = "".join(lines[2:]).strip()
                        elif len(lines) == 2:
                            content = ""
                        elif len(lines) == 1:
                            content = ""
                    except Exception as e:
                        print(f"[警告] 读取章节文件 {chapter_file} 失败: {e}")
                        content = ""
                
                chapter_list.append({
                    "title": title,
                    "content": content,
                    "prompt": prompt
                })
            
            print(f"[信息] 已加载 {len(chapter_list)} 个章节")
            return chapter_list
        except Exception as e:
            print(f"[错误] 加载章节失败: {e}")
            traceback.print_exc()
            return []
    
    # ==================== 小说配置持久化 ====================
    
    def save_novel_config(self, target_dir=None):
        """
        保存小说基础配置到 novel.ini
        Args:
            target_dir: 目标目录，若为None则使用 app.current_novel_dir
        Returns:
            成功返回True，失败返回False
        """
        try:
            if target_dir is None:
                target_dir = getattr(self.app, "current_novel_dir", "")
            
            if not target_dir:
                print("[错误] 未指定保存目录")
                return False
            
            os.makedirs(target_dir, exist_ok=True)
            novel_ini = os.path.join(target_dir, "novel.ini")
            
            config = configparser.ConfigParser()
            if os.path.exists(novel_ini):
                config.read(novel_ini, encoding="utf-8")
            
            if "BASIC" not in config:
                config["BASIC"] = {}
            if "META" not in config:
                config["META"] = {}
            
            # 保存基础信息
            config["BASIC"]["title"] = self.app.title_entry.get().strip() if hasattr(self.app, "title_entry") else ""
            config["BASIC"]["type"] = self.app.novel_type_var.get() if hasattr(self.app, "novel_type_var") else "其他"
            config["BASIC"]["style"] = self.app.writing_style_var.get() if hasattr(self.app, "writing_style_var") else "平实自然"
            config["BASIC"]["theme"] = (self.app.novel_theme_text.get("1.0", "end-1c").strip() if hasattr(self.app, "novel_theme_text") else (self.app.novel_theme_var.get().strip() if hasattr(self.app, "novel_theme_var") else ""))
            config["BASIC"]["chapter_words"] = str(self.app.chapter_words_var.get()) if hasattr(self.app, "chapter_words_var") else "3000"
            
            if "chapters_path" not in config["META"]:
                config["META"]["chapters_path"] = "chapters"
            
            # 写入文件
            with open(novel_ini, "w", encoding="utf-8") as f:
                config.write(f)
            
            print(f"[信息] 已保存小说配置到: {novel_ini}")
            return True
        except Exception as e:
            print(f"[错误] 保存小说配置失败: {e}")
            traceback.print_exc()
            return False
    
    def save_novel_settings(self):
        """
        保存小说设定和人物设定到 novel.ini
        Returns:
            成功返回True，失败返回False
        """
        try:
            if not hasattr(self.app, 'current_novel_dir') or not self.app.current_novel_dir:
                print("[错误] 未设置小说目录")
                return False
            
            novel_ini = os.path.join(self.app.current_novel_dir, "novel.ini")
            
            config = configparser.ConfigParser()
            if os.path.exists(novel_ini):
                config.read(novel_ini, encoding="utf-8")
            
            # 清空旧的设定
            if "NOVEL_SETTINGS" in config:
                config.remove_section("NOVEL_SETTINGS")
            if "CHARACTERS" in config:
                config.remove_section("CHARACTERS")
            if "NOVEL_SETTINGS_SELECTED" in config:
                config.remove_section("NOVEL_SETTINGS_SELECTED")
            if "CHARACTERS_SELECTED" in config:
                config.remove_section("CHARACTERS_SELECTED")
            
            # 保存小说设定
            if hasattr(self.app, "novel_setting_details") and self.app.novel_setting_details:
                config["NOVEL_SETTINGS"] = {}
                for name, content in self.app.novel_setting_details.items():
                    config["NOVEL_SETTINGS"][name] = content
            
            # 保存人物设定
            if hasattr(self.app, "character_setting_details") and self.app.character_setting_details:
                config["CHARACTERS"] = {}
                for name, content in self.app.character_setting_details.items():
                    config["CHARACTERS"][name] = content
            
            # 保存选中状态
            if hasattr(self.app, "novel_setting_checked") and self.app.novel_setting_checked:
                config["NOVEL_SETTINGS_SELECTED"] = {}
                for name, checked in self.app.novel_setting_checked.items():
                    config["NOVEL_SETTINGS_SELECTED"][name] = str(checked)
            
            if hasattr(self.app, "character_setting_checked") and self.app.character_setting_checked:
                config["CHARACTERS_SELECTED"] = {}
                for name, checked in self.app.character_setting_checked.items():
                    config["CHARACTERS_SELECTED"][name] = str(checked)
            
            # 写入文件
            with open(novel_ini, "w", encoding="utf-8") as f:
                config.write(f)
            
            print(f"[信息] 已保存小说设定到: {novel_ini}")
            return True
        except Exception as e:
            print(f"[错误] 保存小说设定失败: {e}")
            traceback.print_exc()
            return False
    
    # ==================== 应用配置持久化 ====================
    
    def save_last_novel_path(self, novel_path):
        """
        保存最后打开的小说路径到应用配置
        Args:
            novel_path: 小说配置文件路径
        Returns:
            成功返回True，失败返回False
        """
        try:
            from services.config_manager import ConfigManager
            return ConfigManager.save_config_value("APP", "last_novel", novel_path)
        except Exception as e:
            print(f"[错误] 保存最后小说路径失败: {e}")
            traceback.print_exc()
            return False
    
    def get_last_novel_path(self):
        """
        获取最后打开的小说路径
        Returns:
            小说路径字符串，若不存在则返回空字符串
        """
        try:
            from services.config_manager import ConfigManager
            config_data = ConfigManager.load_config()
            if config_data:
                # 读取配置文件获取 last_novel
                config = configparser.ConfigParser()
                preferred_path = os.path.join("config", "config.ini")
                if os.path.exists(preferred_path):
                    config.read(preferred_path, encoding='utf-8')
                    if "APP" in config and "last_novel" in config["APP"]:
                        return config["APP"]["last_novel"]
            return ""
        except Exception as e:
            print(f"[错误] 获取最后小说路径失败: {e}")
            return ""
