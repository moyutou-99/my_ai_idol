import pyaudio
import wave
import threading
import time
import os
from datetime import datetime
import logging
import numpy as np
import queue
import webrtcvad

logger = logging.getLogger(__name__)

class AudioRecorder:
    def __init__(self, save_dir="recordings"):
        """初始化录音器
        
        Args:
            save_dir (str): 录音文件保存目录
        """
        self.save_dir = save_dir
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.recording_thread = None
        self.vad_thread = None
        self.recognition_thread = None
        
        # 获取并显示当前使用的麦克风信息
        try:
            default_input = self.audio.get_default_input_device_info()
            logger.info(f"当前使用的麦克风: {default_input['name']}")
        except Exception as e:
            logger.error(f"获取麦克风信息失败: {e}")
        
        # 创建保存目录
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        # 录音参数
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 480  # 30ms chunks for VAD (16000 * 0.03)
        self.vad = webrtcvad.Vad(3)  # 设置VAD灵敏度（0-3）
        
        # 音量计算参数
        self.volume_queue = queue.Queue()
        self.current_volume = 0
        self.silence_frames = 0
        self.max_silence_frames = 60  # 约2秒的静音判定
        
        # VAD状态
        self.is_speaking = False
        self.speech_start_time = None
        self.min_speech_duration = 0.5  # 最小语音持续时间（秒）
        
        # 语音识别相关
        self.last_recognition_result = None
        self.recognition_buffer = []
        self.recognition_lock = threading.Lock()
        
        # 音频数据队列
        self.audio_queue = queue.Queue()
        self.max_retries = 3  # 最大重试次数
        
    def _create_stream(self):
        """创建音频流"""
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            return True
        except Exception as e:
            logger.error(f"创建音频流失败: {e}")
            return False
            
    def start_recording(self):
        """开始录音"""
        if self.is_recording:
            logger.warning("已经在录音中")
            return False
            
        try:
            if not self._create_stream():
                return False
                
            self.frames = []
            self.is_recording = True
            self.recording_thread = threading.Thread(target=self._record)
            self.vad_thread = threading.Thread(target=self._process_vad)
            self.recognition_thread = threading.Thread(target=self._process_recognition)
            self.recording_thread.start()
            self.vad_thread.start()
            self.recognition_thread.start()
            
            logger.info("开始录音")
            return True
            
        except Exception as e:
            logger.error(f"开始录音失败: {e}")
            return False
            
    def stop_recording(self):
        """停止录音并保存文件"""
        if not self.is_recording:
            logger.warning("没有正在进行的录音")
            return None
            
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join()
        if self.vad_thread:
            self.vad_thread.join()
        if self.recognition_thread:
            self.recognition_thread.join()
            
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.wav"
        filepath = os.path.join(self.save_dir, filename)
        
        # 保存录音文件
        try:
            wf = wave.open(filepath, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            
            logger.info(f"录音已保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"保存录音文件失败: {e}")
            return None
            
    def _record(self):
        """录音线程"""
        retry_count = 0
        while self.is_recording:
            try:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                self.frames.append(data)
                self.audio_queue.put(data)  # 将音频数据放入队列
                
                # 计算音量
                audio_data = np.frombuffer(data, dtype=np.int16)
                volume = np.abs(audio_data).mean()
                self.volume_queue.put(volume)
                
                retry_count = 0  # 重置重试计数
                
            except Exception as e:
                logger.error(f"录音过程出错: {e}")
                retry_count += 1
                if retry_count >= self.max_retries:
                    logger.error("达到最大重试次数，停止录音")
                    break
                    
                # 尝试重新创建音频流
                time.sleep(0.1)  # 短暂等待
                if not self._create_stream():
                    break
                    
    def _process_vad(self):
        """VAD处理线程"""
        while self.is_recording:
            try:
                # 从队列获取音频数据
                data = self.audio_queue.get(timeout=1.0)
                
                # 确保数据长度正确
                if len(data) != self.chunk * 2:  # 16位采样，每个采样2字节
                    logger.warning(f"音频数据长度不正确: {len(data)} != {self.chunk * 2}")
                    continue
                
                # VAD检测
                try:
                    is_speech = self.vad.is_speech(data, self.rate)
                except Exception as e:
                    logger.error(f"VAD检测失败: {e}")
                    continue
                
                if is_speech:
                    if not self.is_speaking:
                        self.is_speaking = True
                        self.speech_start_time = time.time()
                        self.silence_frames = 0
                        # 清空识别缓冲区
                        with self.recognition_lock:
                            self.recognition_buffer = []
                else:
                    if self.is_speaking:
                        self.silence_frames += 1
                        if self.silence_frames >= self.max_silence_frames:
                            duration = time.time() - self.speech_start_time
                            if duration >= self.min_speech_duration:
                                logger.info(f"检测到语音片段，持续时间: {duration:.2f}秒")
                                # 将缓冲区数据保存为临时文件并进行识别
                                self._recognize_speech()
                            self.is_speaking = False
                            
            except queue.Empty:
                continue  # 队列为空，继续等待
            except Exception as e:
                logger.error(f"VAD处理出错: {e}")
                break
                
    def _process_recognition(self):
        """语音识别处理线程"""
        while self.is_recording:
            try:
                if self.is_speaking:
                    # 从队列获取音频数据
                    data = self.audio_queue.get(timeout=1.0)
                    with self.recognition_lock:
                        self.recognition_buffer.append(data)
                time.sleep(0.1)  # 避免过度占用CPU
            except queue.Empty:
                continue  # 队列为空，继续等待
            except Exception as e:
                logger.error(f"语音识别处理出错: {e}")
                break
                
    def _recognize_speech(self):
        """识别语音片段"""
        try:
            with self.recognition_lock:
                if not self.recognition_buffer:
                    return
                    
                # 生成临时文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_filename = f"temp_{timestamp}.wav"
                temp_filepath = os.path.join(self.save_dir, temp_filename)
                
                # 保存临时文件
                wf = wave.open(temp_filepath, 'wb')
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(self.recognition_buffer))
                wf.close()
                
                # 使用语音识别器识别
                from src.audio.speech_recognition import SpeechRecognizer
                recognizer = SpeechRecognizer()
                result = recognizer.recognize_file(temp_filepath)
                
                if result:
                    self.last_recognition_result = result
                    logger.info(f"识别结果: {result}")
                
                # 删除临时文件
                try:
                    os.remove(temp_filepath)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"语音识别失败: {e}")
                
    def get_current_volume(self):
        """获取当前音量"""
        try:
            while not self.volume_queue.empty():
                self.current_volume = self.volume_queue.get()
            return self.current_volume
        except:
            return 0
            
    def is_speech_detected(self):
        """检查是否检测到语音"""
        return self.is_speaking
        
    def __del__(self):
        """清理资源"""
        if self.stream:
            self.stream.close()
        self.audio.terminate() 