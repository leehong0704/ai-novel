"""
配置管理服务
负责加载和保存应用配置
"""

import os
import configparser
import shutil
import traceback

class ConfigManager:
    """配置管理服务类"""
    
    @staticmethod
    def load_config():
        """从 config/config.ini（优先）或根目录 config.ini 加载配置；若不存在则从 example 自动创建
        
        返回:
            包含以下键的字典:
            - api_key: 当前选中API的密钥
            - api_base: 当前选中API的基础URL
            - model: 当前选中API的模型名称
            - temperature: 当前选中API的温度参数
            - max_tokens: 当前选中API的最大token数
            - current_api: 当前选中的API配置名称
            - available_apis: 所有可用的API配置列表 [{name, api_key, api_base, model, temperature, max_tokens}, ...]
        """
        config = configparser.ConfigParser()
        os.makedirs("config", exist_ok=True)
        preferred_path = os.path.join("config", "config.ini")
        legacy_path = "config.ini"
        example_path = os.path.join("config", "config.ini.example")

        config_file = None
        if os.path.exists(preferred_path):
            config_file = preferred_path
        elif os.path.exists(legacy_path):
            config_file = legacy_path

        if config_file is None:
            # 如果 config.ini 不存在，尝试从 example 创建
            if not os.path.exists(example_path):
                # 如果 example 也不存在，先创建一个默认的 example（新格式）
                try:
                    ConfigManager._create_default_example(example_path)
                    print(f"已创建示例配置文件: {example_path}")
                except Exception as e:
                    print(f"错误: 无法创建示例配置文件: {str(e)}")
                    return None
            
            # 从 example 复制创建 config.ini
            try:
                shutil.copy2(example_path, preferred_path)
                print(f"已从示例文件自动创建配置文件: {preferred_path}")
                print("提示: 请编辑 config/config.ini 填写您的 API Key 等配置信息")
                config_file = preferred_path
            except Exception as e:
                print(f"错误: 无法从示例文件创建配置文件: {str(e)}")
                print("提示: 请手动在 config 目录下创建 config.ini（可参考 config/config.ini.example）")
                return None

        config.read(config_file, encoding='utf-8')

        try:
            # 获取默认参数
            default_temperature = config.getfloat('DEFAULT', 'temperature')
            default_max_tokens = config.getint('DEFAULT', 'max_tokens')
            default_timeout = config.getint('DEFAULT', 'timeout', fallback=300)
            
            # 获取当前使用的API配置名称
            current_api = config.get('APP', 'current_api', fallback='DEEPSEEK')
            
            # 获取所有API配置
            available_apis = []
            # 排除DEFAULT和APP这两个特殊section
            api_sections = [s for s in config.sections() if s not in ['APP']]
            
            for section in api_sections:
                try:
                    # 读取API配置，temperature、max_tokens和timeout如果没有则使用DEFAULT的值
                    api_config = {
                        'name': section,
                        'api_key': config.get(section, 'api_key'),
                        'api_base': config.get(section, 'api_base'),
                        'model': config.get(section, 'model'),
                        'temperature': config.getfloat(section, 'temperature', fallback=default_temperature),
                        'max_tokens': config.getint(section, 'max_tokens', fallback=default_max_tokens),
                        'timeout': config.getint(section, 'timeout', fallback=default_timeout)
                    }
                    available_apis.append(api_config)
                except (configparser.NoOptionError, configparser.NoSectionError):
                    # 跳过配置不完整的section
                    print(f"警告: API配置 [{section}] 不完整，已跳过")
                    continue
            
            # 如果没有找到任何API配置，返回错误
            if not available_apis:
                print("错误: 未找到任何有效的API配置")
                print("提示: 请检查配置文件是否包含至少一个完整的API配置（包含api_key, api_base, model）")
                return None
            
            # 确保current_api存在于available_apis中
            current_api_config = None
            for api in available_apis:
                if api['name'] == current_api:
                    current_api_config = api
                    break
            
            # 如果当前API不存在，使用第一个可用的API
            if current_api_config is None:
                current_api_config = available_apis[0]
                current_api = current_api_config['name']
                print(f"警告: 配置的current_api '{config.get('APP', 'current_api', fallback='DEEPSEEK')}' 不存在，已切换到 '{current_api_config['name']}'")
            
            return {
                'api_key': current_api_config['api_key'],
                'api_base': current_api_config['api_base'],
                'model': current_api_config['model'],
                'temperature': current_api_config['temperature'],
                'max_tokens': current_api_config['max_tokens'],
                'timeout': current_api_config['timeout'],
                'current_api': current_api,
                'available_apis': available_apis
            }
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            print(f"错误: 配置文件格式错误: {e}")
            print("提示: 请检查配置文件是否包含必要的配置项，可参考 config/config.ini.example")
            traceback.print_exc()
            return None
    
    @staticmethod
    def _create_default_example(example_path):
        """创建默认的示例配置文件（新格式，支持多个API）"""
        content = """[DEFAULT]
# 默认温度参数，控制生成内容的随机性（0-1之间，越高越随机）
temperature = 0.5
# 默认最大生成token数量
max_tokens = 5000
# 默认API请求超时时间（秒）
timeout = 300

[APP]
# 当前使用的AI接口名称（对应下面的某个接口配置section）
current_api = DEEPSEEK
# 上次打开的小说文件路径（程序会自动更新此项）
last_novel = 

# ========== AI接口配置 ==========
# 你可以配置多个AI接口，通过修改 [APP] 中的 current_api 来切换使用哪个接口
# 每个接口配置需要包含：api_key, api_base, model, temperature, max_tokens, timeout 六个字段

[DEEPSEEK]
# DeepSeek API 配置
api_key = 
api_base = https://api.deepseek.com/v1
model = deepseek-chat
temperature = 0.5
max_tokens = 4000
timeout = 300

[OPENAI]
# OpenAI API 配置（示例）
api_key = 
api_base = https://api.openai.com/v1
model = gpt-4
temperature = 0.7
max_tokens = 4000
timeout = 300

[GEMINI]
# Google Gemini API 配置（示例）
api_key = 
api_base = https://generativelanguage.googleapis.com/v1beta
model = gemini-2.0-flash-exp
temperature = 0.6
timeout = 300
"""
        with open(example_path, "w", encoding="utf-8") as f:
            f.write(content)

    @staticmethod
    def save_config_value(section, key, value):
        """保存配置值到 config/config.ini"""
        try:
            config = configparser.ConfigParser()
            preferred_path = os.path.join("config", "config.ini")
            
            # 读取现有配置
            if os.path.exists(preferred_path):
                config.read(preferred_path, encoding='utf-8')
            
            # 确保section存在
            if section not in config:
                config[section] = {}
            
            # 设置值
            config[section][key] = value
            
            # 写回文件
            with open(preferred_path, 'w', encoding='utf-8') as f:
                config.write(f)
            
            return True
        except Exception as e:
            print(f"错误: 保存配置失败: {e}")
            traceback.print_exc()
            return False
    
    @staticmethod
    def save_api_config(api_name, api_key, api_base, model, temperature, max_tokens, timeout=300):
        """保存或更新API配置（包含temperature、max_tokens和timeout）"""
        try:
            config = configparser.ConfigParser()
            preferred_path = os.path.join("config", "config.ini")
            
            # 读取现有配置
            if os.path.exists(preferred_path):
                config.read(preferred_path, encoding='utf-8')
            
            # 确保section存在
            if api_name not in config:
                config[api_name] = {}
            
            # 设置值
            config[api_name]['api_key'] = api_key
            config[api_name]['api_base'] = api_base
            config[api_name]['model'] = model
            config[api_name]['temperature'] = str(temperature)
            config[api_name]['max_tokens'] = str(max_tokens)
            config[api_name]['timeout'] = str(timeout)
            
            # 写回文件
            with open(preferred_path, 'w', encoding='utf-8') as f:
                config.write(f)
            
            return True
        except Exception as e:
            print(f"错误: 保存API配置失败: {e}")
            traceback.print_exc()
            return False
    
    @staticmethod
    def delete_api_config(api_name):
        """删除API配置"""
        try:
            config = configparser.ConfigParser()
            preferred_path = os.path.join("config", "config.ini")
            
            # 读取现有配置
            if os.path.exists(preferred_path):
                config.read(preferred_path, encoding='utf-8')
            
            # 删除section
            if api_name in config:
                config.remove_section(api_name)
                
                # 写回文件
                with open(preferred_path, 'w', encoding='utf-8') as f:
                    config.write(f)
                
                return True
            else:
                print(f"警告: API配置 [{api_name}] 不存在")
                return False
        except Exception as e:
            print(f"错误: 删除API配置失败: {e}")
            traceback.print_exc()
            return False
    
    @staticmethod
    def rename_api_config(old_name, new_name):
        """重命名API配置
        
        参数:
            old_name: 原配置名称
            new_name: 新配置名称
            
        返回:
            成功返回True，失败返回False
        """
        try:
            config = configparser.ConfigParser()
            preferred_path = os.path.join("config", "config.ini")
            
            # 读取现有配置
            if not os.path.exists(preferred_path):
                print("错误: 配置文件不存在")
                return False
                
            config.read(preferred_path, encoding='utf-8')
            
            # 检查旧名称是否存在
            if old_name not in config:
                print(f"错误: API配置 [{old_name}] 不存在")
                return False
            
            # 检查新名称是否已存在
            if new_name in config:
                print(f"错误: API配置 [{new_name}] 已存在")
                return False
            
            # 检查新名称是否为保留名称
            if new_name.upper() in ['DEFAULT', 'APP']:
                print(f"错误: 不能使用保留名称 '{new_name}'")
                return False
            
            # 获取旧配置的所有值
            old_config = dict(config[old_name])
            
            # 创建新配置
            config[new_name] = old_config
            
            # 删除旧配置
            config.remove_section(old_name)
            
            # 如果当前使用的是被重命名的API，更新current_api
            if 'APP' in config and config.get('APP', 'current_api', fallback='') == old_name:
                config['APP']['current_api'] = new_name
            
            # 写回文件
            with open(preferred_path, 'w', encoding='utf-8') as f:
                config.write(f)
            
            print(f"成功: API配置已从 '{old_name}' 重命名为 '{new_name}'")
            return True
            
        except Exception as e:
            print(f"错误: 重命名API配置失败: {e}")
            traceback.print_exc()
            return False
