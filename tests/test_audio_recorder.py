import sys
import os
import time
from pathlib import Path
import threading

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.audio.audio_recorder import AudioRecorder

def display_volume(recorder):
    """显示音量"""
    while recorder.is_recording:
        volume = recorder.get_current_volume()
        # 将音量转换为0-50的显示范围
        display_length = int(min(50, volume / 100))
        volume_bar = "=" * display_length + " " * (50 - display_length)
        print(f"\r音量: [{volume_bar}] {volume:.0f}", end="", flush=True)
        time.sleep(0.1)
    print()  # 换行

def display_vad_status(recorder):
    """显示VAD状态"""
    while recorder.is_recording:
        status = "检测到语音" if recorder.is_speech_detected() else "等待语音..."
        print(f"\rVAD状态: {status}", end="", flush=True)
        time.sleep(0.1)
    print()  # 换行

def test_recording():
    """测试录音功能"""
    # 创建录音器实例
    recorder = AudioRecorder(save_dir="test_recordings")
    
    print("开始录音测试...")
    print("1. 按回车开始录音")
    print("2. 再次按回车停止录音")
    
    input("准备开始录音...")
    
    # 开始录音
    if recorder.start_recording():
        print("正在录音...")
        
        # 创建并启动显示线程
        volume_thread = threading.Thread(target=display_volume, args=(recorder,))
        vad_thread = threading.Thread(target=display_vad_status, args=(recorder,))
        volume_thread.start()
        vad_thread.start()
        
        input("按回车停止录音...")
        
        # 停止录音
        filepath = recorder.stop_recording()
        if filepath:
            print(f"录音已保存: {filepath}")
        else:
            print("录音保存失败")
    else:
        print("开始录音失败")
        
if __name__ == "__main__":
    test_recording() 