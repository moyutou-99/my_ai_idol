import os
from typing import Optional

class LLMConfig:
    def __init__(self):
        # 本地模型配置
        self.local_model_path = "Voice_models/Qwen2.5-1.5B-Instruct"
        
        # API配置
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "sk-af272593e5f14b049b9ac6b3bfe75b43")
        self.ph_api_key = os.getenv("PH_API_KEY", "sk-jBWhM4xVWTRGl74NriZjFMSrxsouEEPqtFCSA0eenG0rWdEV")
        
        # 模型参数
        self.max_tokens = 512
        self.temperature = 0.7
        self.top_p = 0.9
        
        # 显存配置
        self.memory_threshold = 2.5  # GB
        self.warning_threshold = 3.0  # GB
        
    @classmethod
    def from_env(cls) -> 'LLMConfig':
        """从环境变量创建配置"""
        config = cls()
        config.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "sk-af272593e5f14b049b9ac6b3bfe75b43")
        config.ph_api_key = os.getenv("PH_API_KEY", "sk-jBWhM4xVWTRGl74NriZjFMSrxsouEEPqtFCSA0eenG0rWdEV")
        return config 