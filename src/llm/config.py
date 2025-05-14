import os
import yaml
from typing import Optional

def load_config():
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return {}

class LLMConfig:
    def __init__(self):
        config = load_config()
        llm_config = config.get('llm', {})
        
        # 本地模型配置
        self.local_model_path = llm_config.get('local_model_path', "Voice_models/Qwen2.5-1.5B-Instruct")
        
        # API配置
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY") or llm_config.get('deepseek_api_key')
        self.ph_api_key = os.getenv("PH_API_KEY") or llm_config.get('ph_api_key')
        
        # 模型参数
        self.max_tokens = llm_config.get('max_tokens', 512)
        self.temperature = llm_config.get('temperature', 0.7)
        self.top_p = llm_config.get('top_p', 0.9)
        
        # 显存配置
        self.memory_threshold = llm_config.get('memory_threshold', 2.5)  # GB
        self.warning_threshold = llm_config.get('warning_threshold', 3.0)  # GB
        
    @classmethod
    def from_env(cls) -> 'LLMConfig':
        """从环境变量创建配置"""
        return cls()  # 现在直接返回实例即可，因为环境变量优先级已在__init__中处理 