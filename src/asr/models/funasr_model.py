"""
FunASR模型实现
"""
import os
import logging
import numpy as np
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess
from src.audio.model_manager import ModelManager

class FunASRModel:
    """FunASR模型类，包含三个子模型：
    1. 主要的语音识别模型
    2. 语音活动检测(VAD)模型
    3. 标点符号预测模型
    """
    
    def __init__(self, model_dir=None):
        """初始化FunASR模型
        
        Args:
            model_dir: 模型目录路径，如果为None则使用默认路径
        """
        # 初始化模型管理器
        self.model_manager = ModelManager(model_dir)
        
        # 获取模型配置
        model_config = self.model_manager.get_model_config("funasr")
        if not model_config:
            raise ValueError("无法获取FunASR模型配置")
            
        # 设置模型路径
        self.asr_model_path = model_config["asr_model"]
        self.vad_model_path = model_config["vad_model"]
        self.punc_model_path = model_config["punc_model"]
        
        # 初始化模型
        self.model = None
        self.is_initialized = False
        self.device = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"
        
        # 流式识别配置
        self.chunk_size = [0, 10, 5]  # [0, 10, 5] 600ms
        self.encoder_chunk_look_back = 4
        self.decoder_chunk_look_back = 1
        
        # 初始化日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def initialize(self):
        """初始化模型"""
        try:
            # 使用本地模型
            self.model = AutoModel(
                model=self.asr_model_path,
                model_revision="v2.0.4",
                vad_model=self.vad_model_path,
                vad_model_revision="v2.0.4",
                punc_model=self.punc_model_path,
                punc_model_revision="v2.0.4",
                device=self.device
            )
            self.is_initialized = True
            self.logger.info("FunASR模型初始化成功")
            return True
        except Exception as e:
            self.logger.error(f"FunASR模型初始化失败: {str(e)}")
            return False
            
    def recognize_file(self, audio_file):
        """识别音频文件
        
        Args:
            audio_file: 音频文件路径
            
        Returns:
            str: 识别结果文本
        """
        if not self.is_initialized:
            if not self.initialize():
                return None
                
        try:
            # 使用模型生成结果
            result = self.model.generate(
                input=audio_file,
                cache={},
                language="auto",
                use_itn=True,
                batch_size_s=60,
                merge_vad=True,
                merge_length_s=15
            )
            
            # 后处理
            text = rich_transcription_postprocess(result[0]["text"])
            return text
            
        except Exception as e:
            self.logger.error(f"识别失败: {str(e)}")
            return None
            
    def recognize_stream(self, audio_data, is_final=False):
        """识别音频流
        
        Args:
            audio_data: 音频数据，numpy数组格式
            is_final: 是否为最后一个音频片段
            
        Returns:
            str: 识别结果文本
        """
        if not self.is_initialized:
            if not self.initialize():
                return None
                
        try:
            # 确保音频数据是numpy数组
            if not isinstance(audio_data, np.ndarray):
                audio_data = np.array(audio_data)
                
            # 使用模型生成结果
            result = self.model.generate(
                input=audio_data,
                cache={},
                is_final=is_final,
                chunk_size=self.chunk_size,
                encoder_chunk_look_back=self.encoder_chunk_look_back,
                decoder_chunk_look_back=self.decoder_chunk_look_back,
                language="auto",
                use_itn=True,
                batch_size_s=60,
                merge_vad=True,
                merge_length_s=15
            )
            
            # 后处理
            text = rich_transcription_postprocess(result[0]["text"])
            return text
            
        except Exception as e:
            self.logger.error(f"识别失败: {str(e)}")
            return None
            
    def __del__(self):
        """清理资源"""
        if self.model is not None:
            del self.model 