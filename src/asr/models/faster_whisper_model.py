"""
Faster Whisper模型实现，用于非中文语音识别
"""
import os
import logging
import numpy as np
import traceback
from faster_whisper import WhisperModel

class FasterWhisperModel:
    """Faster Whisper模型类，用于非中文语音识别"""
    
    def __init__(self, model_dir=None, model_size="base", precision="float32"):
        """初始化Faster Whisper模型
        
        Args:
            model_dir: 模型目录路径，如果为None则使用默认路径
            model_size: 模型大小，可选值：tiny, base, small, medium, large
            precision: 计算精度，可选值：float32, float16, int8
        """
        # 设置默认模型路径
        self.model_dir = model_dir or "F:\\aivoice\\tools\\modelscope\\hub\\models\\asr"
        
        # 设置模型参数
        self.model_size = model_size
        self.precision = precision
        
        # 初始化日志
        self.logger = logging.getLogger(__name__)
        
        # 检查模型路径
        self._check_model_path()
        
        # 初始化模型
        self.model = None
        self.is_initialized = False
        self.device = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"
        
    def _check_model_path(self):
        """检查模型路径是否存在"""
        if '-local' in self.model_size:
            self.model_size = self.model_size[:-6]
            self.model_path = os.path.join(self.model_dir, f"faster-whisper-{self.model_size}")
        else:
            self.model_path = self.model_size
            
        if not os.path.exists(self.model_path):
            self.logger.warning(f"Faster Whisper模型路径不存在: {self.model_path}")
            self.logger.warning("将使用默认模型路径")
            self.model_path = self.model_size
        
    def initialize(self):
        """初始化模型"""
        try:
            self.logger.info(f"加载Faster Whisper模型: {self.model_size}, {self.model_path}")
            self.model = WhisperModel(
                model_size_or_path=self.model_path,
                device=self.device,
                compute_type=self.precision
            )
            self.is_initialized = True
            self.logger.info("Faster Whisper模型初始化成功")
            return True
        except Exception as e:
            self.logger.error(f"Faster Whisper模型初始化失败: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False
            
    def recognize_file(self, audio_file, language=None):
        """识别音频文件
        
        Args:
            audio_file: 音频文件路径
            language: 语言代码，如果为None则自动检测
            
        Returns:
            str: 识别结果文本
        """
        if not self.is_initialized:
            if not self.initialize():
                return None
                
        try:
            # 使用模型生成结果
            segments, info = self.model.transcribe(
                audio=audio_file,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=700),
                language=language
            )
            
            # 合并所有片段
            text = ""
            for segment in segments:
                text += segment.text
                
            return text
            
        except Exception as e:
            self.logger.error(f"识别失败: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None
            
    def recognize_stream(self, audio_data, language=None):
        """识别音频流
        
        Args:
            audio_data: 音频数据，numpy数组格式
            language: 语言代码，如果为None则自动检测
            
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
            segments, info = self.model.transcribe(
                audio=audio_data,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=700),
                language=language
            )
            
            # 合并所有片段
            text = ""
            for segment in segments:
                text += segment.text
                
            return text
            
        except Exception as e:
            self.logger.error(f"识别失败: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None
            
    def __del__(self):
        """清理资源"""
        try:
            if hasattr(self, 'model') and self.model is not None:
                del self.model
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"清理模型资源失败: {str(e)}") 