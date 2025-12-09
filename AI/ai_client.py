"""
AI客户端模块
封装与AI API的交互逻辑
"""

import requests
import json
import traceback


class AIClient:
    """AI客户端类，用于与DeepSeek API交互"""
    
    def __init__(self, api_key, api_base, model, timeout=300):
        """
        初始化AI客户端
        
        参数:
            api_key: API密钥
            api_base: API基础URL
            model: 使用的模型名称
            timeout: 请求超时时间（秒），默认300秒
        """
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.timeout = timeout
    

    def generate_content(self, system_prompt, user_prompt, temperature, max_tokens):
        """
        使用AI生成内容
        
        参数:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            temperature: 温度参数（控制创意性）
            max_tokens: 最大生成长度
            
        返回:
            生成的文本内容，如果出错则返回错误信息
        """
        try:
            # 准备API请求
            # 打印将要传递给AI的关键信息（不包含API Key）
            def _preview(text, limit=800):
                try:
                    s = str(text)
                    return s if len(s) <= limit else (s[:limit] + f"...(共{len(s)}字符)")
                except Exception:
                    return "<不可预览内容>"
            
            print("[调试] 将发送给AI的内容预览 ↓")
            print(f"[调试] System提示:\n{_preview(system_prompt)}")
            print(f"[调试] User提示:\n{_preview(user_prompt)}")
            print(f"[调试] 生成参数: temperature={temperature}, max_tokens={max_tokens}")
            
            # 构建完整的 API URL，移除末尾斜杠避免双斜杠
            api_base_clean = self.api_base.rstrip('/')
            url = f"{api_base_clean}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            print(f"[调试] API请求URL: {url}")
            print(f"[调试] 使用模型: {self.model}")
            print(f"[调试] 请求数据大小: {len(json.dumps(data))} 字节")
            
            try:
                # 配置代理设置
                # 如果需要使用代理访问 Google API，请设置环境变量或在这里配置
                proxies = None
                
                # 方式1: 使用系统环境变量中的代理（如果有）
                # proxies 会自动从环境变量 HTTP_PROXY/HTTPS_PROXY 读取
                
                # 方式2: 手动指定代理（取消下面的注释并填写您的代理地址）
                # proxies = {
                #     'http': 'http://127.0.0.1:7890',
                #     'https': 'http://127.0.0.1:7890',
                # }
                
                # 方式3: 完全禁用代理（如果系统代理导致问题）
                # proxies = {
                #     'http': None,
                #     'https': None,
                # }
                
                # 发送API请求
                print("[调试] 正在发送API请求...")
                print(f"[调试] 超时时间: {self.timeout}秒")
                response = requests.post(
                    url, 
                    headers=headers, 
                    data=json.dumps(data), 
                    timeout=self.timeout,  # 使用配置的超时时间
                    proxies=proxies  # 使用代理配置
                )
                print(f"[调试] API响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        generated_text = result["choices"][0]["message"]["content"]
                        print(f"[调试] API返回成功，内容长度: {len(generated_text)} 字符")
                        return generated_text.strip()
                    else:
                        print(f"[错误] API返回格式异常: {result}")
                        return f"❌ API返回格式异常: {result}"
                else:
                    error_msg = f"❌ API请求失败 (状态码: {response.status_code})"
                    print(f"[错误] {error_msg}")
                    try:
                        error_detail = response.json()
                        print(f"[错误] 错误详情: {error_detail}")
                        
                        # 检查是否是余额不足错误
                        if response.status_code == 402:
                            if 'error' in error_detail:
                                error_info = error_detail.get('error', {})
                                if 'Insufficient Balance' in str(error_info):
                                    error_msg = "❌ API账户余额不足！\n\n请访问 https://platform.deepseek.com 充值后重试。"
                                else:
                                    error_msg += f"\n错误详情: {error_detail}"
                            else:
                                error_msg += f"\n错误详情: {error_detail}"
                        else:
                            error_msg += f"\n错误详情: {error_detail}"
                    except:
                        print(f"[错误] 响应内容: {response.text[:200]}")
                        if response.status_code == 402:
                            error_msg = "❌ API账户余额不足！\n\n请访问 https://platform.deepseek.com 充值后重试。"
                        else:
                            error_msg += f"\n响应内容: {response.text[:200]}"
                    return error_msg
                    
            except requests.exceptions.Timeout:
                print("[错误] 请求超时")
                return "❌ 请求超时，请稍后重试"
            except requests.exceptions.RequestException as e:
                print(f"[错误] 网络请求错误: {type(e).__name__}: {str(e)}")
                traceback.print_exc()
                return f"❌ 网络请求错误: {str(e)}"
            except Exception as e:
                print(f"[错误] 未知错误: {type(e).__name__}: {str(e)}")
                traceback.print_exc()
                return f"❌ 发生未知错误: {str(e)}"
        except Exception as e:
            print(f"[错误] generate_content 方法异常: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
            return f"❌ 生成方法异常: {str(e)}"
    
    def update_config(self, api_key=None, api_base=None, model=None, timeout=None):
        """
        更新API配置
        
        参数:
            api_key: 新的API密钥（可选）
            api_base: 新的API基础URL（可选）
            model: 新的模型名称（可选）
            timeout: 新的超时时间（可选）
        """
        if api_key is not None:
            self.api_key = api_key
        if api_base is not None:
            self.api_base = api_base
        if model is not None:
            self.model = model
        if timeout is not None:
            self.timeout = timeout
