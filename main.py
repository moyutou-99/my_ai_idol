import sys
import os
import threading
import subprocess
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import logging

# 导入前端模块
from src.live2d_window import Live2DWindow

# 导入后端模块
from src.backend.server import run_server

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_backend_server():
    """在单独的线程中启动后端服务器"""
    try:
        logger.info("正在启动后端服务器...")
        run_server(host="127.0.0.1", port=8000)
    except Exception as e:
        logger.error(f"后端服务器启动失败: {e}")

def start_tts_server():
    """在单独的线程中启动TTS服务器"""
    try:
        logger.info("正在启动TTS服务器...")
        # 获取当前文件所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建批处理文件的完整路径
        bat_path = os.path.join(current_dir, "Voice_models", "GPT-SoVITS-Inference", "0 一键启动脚本", "3 启动后端程序.bat")
        
        if not os.path.exists(bat_path):
            logger.error(f"找不到TTS后端批处理文件: {bat_path}")
            return
            
        # 切换到批处理文件所在目录
        bat_dir = os.path.dirname(bat_path)
        # 启动批处理文件
        subprocess.Popen(bat_path, cwd=bat_dir, creationflags=subprocess.CREATE_NEW_CONSOLE)
        logger.info("TTS服务器启动命令已执行")
    except Exception as e:
        logger.error(f"TTS服务器启动失败: {e}")
        logger.error(f"详细错误信息: {str(e)}")

def main():
    # 创建QApplication实例
    app = QApplication(sys.argv)
    
    # 启动后端服务器线程
    backend_thread = threading.Thread(target=start_backend_server, daemon=True)
    backend_thread.start()
    
    # 启动TTS服务器线程
    tts_thread = threading.Thread(target=start_tts_server, daemon=True)
    tts_thread.start()
    
    # 创建并显示主窗口
    window = Live2DWindow()
    window.show()  # 先显示窗口
    
    # 加载模型
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, "live2d", "live2d_model", "林久久2.0q版", "林久久2.0q版.model3.json")
    logger.info(f"正在加载模型: {model_path}")
    
    # 确保模型路径存在
    if not os.path.exists(model_path):
        logger.error(f"模型文件不存在: {model_path}")
        return
        
    try:
        window.load_model(model_path)
        logger.info("模型加载成功")
        
        # 创建更新定时器，驱动模型动画
        update_timer = QTimer()
        update_timer.timeout.connect(window.model_widget.update)  # 触发模型窗口重绘
        update_timer.start(16)  # 约60FPS
        
        # 测试播放表情和动作
        def test_animations():
            # 播放表情
            window.play_expression("爱心眼")
            
            # 延迟2秒后播放动作
            QTimer.singleShot(2000, lambda: window.play_motion("Scene1"))
            
            # 延迟4秒后播放另一个表情
            QTimer.singleShot(4000, lambda: window.play_expression("normal"))
            
        # 延迟1秒后开始测试动画序列
        QTimer.singleShot(1000, test_animations)
        
    except Exception as e:
        logger.error(f"加载模型时发生错误: {e}")
    
    # 运行应用
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()