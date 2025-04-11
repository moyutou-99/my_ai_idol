import os
import logging
import json
import requests
from pathlib import Path
import hashlib
import shutil

class ModelManager:
    """模型管理器类"""
    
    def __init__(self, model_dir=None):
        """初始化模型管理器
        
        Args:
            model_dir: 模型目录路径，如果为None则使用默认目录
        """
        self.model_dir = model_dir or os.path.join(os.path.dirname(__file__), "..", "..", "Voice_models")
        self.models = {
            "funasr": {
                "name": "FunASR",
                "local_path": os.path.join(self.model_dir, "asr", "models", "models"),
                "model_type": "funasr",
                "config": {
                    "asr_model": os.path.join(self.model_dir, "asr", "models", "models", "speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"),
                    "vad_model": os.path.join(self.model_dir, "asr", "models", "models", "speech_fsmn_vad_zh-cn-16k-common-pytorch"),
                    "punc_model": os.path.join(self.model_dir, "asr", "models", "models", "punc_ct-transformer_zh-cn-common-vocab272727-pytorch"),
                    "language": "auto",
                    "use_itn": True,
                    "batch_size_s": 60,
                    "merge_vad": True,
                    "merge_length_s": 15
                }
            },
            "faster_whisper": {
                "name": "Faster Whisper",
                "local_path": "F:\\aivoice\\tools\\modelscope\\hub\\models\\asr",
                "model_type": "faster_whisper",
                "config": {
                    "model_size": "base",
                    "precision": "float32",
                    "language": "auto"
                }
            }
        }
        
        # 初始化日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def get_model_path(self, model_name):
        """获取模型路径
        
        Args:
            model_name: 模型名称
            
        Returns:
            str: 模型路径
        """
        if model_name not in self.models:
            self.logger.error(f"未找到模型: {model_name}")
            return None
            
        model_info = self.models[model_name]
        model_path = model_info["local_path"]
        
        if not os.path.exists(model_path):
            self.logger.error(f"模型路径不存在: {model_path}")
            return None
            
        return model_path
        
    def get_model_config(self, model_name):
        """获取模型配置
        
        Args:
            model_name: 模型名称
            
        Returns:
            dict: 模型配置
        """
        if model_name not in self.models:
            self.logger.error(f"未找到模型: {model_name}")
            return None
            
        return self.models[model_name]["config"]
        
    def download_model(self, model_name):
        """下载模型
        
        Args:
            model_name (str): 模型名称
            
        Returns:
            bool: 下载是否成功
        """
        if model_name not in self.models:
            self.logger.error(f"未知的模型: {model_name}")
            return False
            
        model_info = self.models[model_name]
        model_path = os.path.join(self.model_dir, f"{model_name}_{model_info['version']}.pt")
        
        # 尝试所有下载源
        for url in model_info['urls']:
            try:
                # 下载模型
                self.logger.info(f"尝试从 {url} 下载模型: {model_name}")
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()
                
                # 保存模型
                with open(model_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            
                # 验证MD5
                if model_info['md5']:
                    with open(model_path, 'rb') as f:
                        md5 = hashlib.md5(f.read()).hexdigest()
                    if md5 != model_info['md5']:
                        self.logger.error(f"模型MD5校验失败: {model_name}")
                        os.remove(model_path)
                        continue
                        
                self.logger.info(f"模型下载完成: {model_name}")
                return True
                
            except Exception as e:
                self.logger.error(f"从 {url} 下载失败: {e}")
                if os.path.exists(model_path):
                    os.remove(model_path)
                continue
                
        self.logger.error(f"所有下载源都失败: {model_name}")
        return False
            
    def check_model(self, model_name):
        """检查模型状态
        
        Args:
            model_name (str): 模型名称
            
        Returns:
            bool: 模型是否可用
        """
        if model_name not in self.models:
            return False
            
        model_path = self.get_model_path(model_name)
        return model_path is not None and os.path.exists(model_path)
        
    def list_models(self):
        """列出所有可用模型
        
        Returns:
            list: 模型信息列表
        """
        return [
            {
                "name": name,
                "info": info,
                "available": self.check_model(name)
            }
            for name, info in self.models.items()
        ] 