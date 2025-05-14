# 导入配置文件
import yaml

# 加载配置文件
def load_config():
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            if not config:
                raise ValueError("配置文件为空")
            return config
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        raise

# 加载配置
config = load_config()

# 验证必要的配置项
def validate_config():
    required_configs = {
        'ui': ['show_login_dialog', 'icon_path'],
        'live2d': ['model_path']
    }
    
    for section, keys in required_configs.items():
        if section not in config:
            raise ValueError(f"配置文件中缺少 {section} 部分")
        for key in keys:
            if key not in config[section]:
                raise ValueError(f"配置文件中缺少 {section}.{key} 配置项")

# 验证配置
validate_config()

# 获取配置值
SHOW_LOGIN_DIALOG = config['ui']['show_login_dialog']

import sys
import os
import asyncio
import qasync
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor
# 导入前端模块
from src.live2d_window import Live2DWindow
from src.auth.auth_ui import LoginDialog, UserProfileWidget
from src.auth.auth_manager import AuthManager

# 导入后端模块
from src.backend.server import run_server

# 导入数据库模块
from database.init_db import init_db

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建线程池
executor = ThreadPoolExecutor(max_workers=1)

# 初始化认证管理器
auth_manager = AuthManager()

async def start_backend_server():
    """启动后端服务器"""
    try:
        logger.info("正在启动后端服务器...")
        # 在单独的线程中运行服务器
        loop = asyncio.get_event_loop()
        server_task = loop.run_in_executor(executor, run_server, "127.0.0.1", 8000)
        # 等待服务器启动
        await asyncio.sleep(2)  # 给服务器一些启动时间
        logger.info("后端服务器启动成功")
        return server_task
    except Exception as e:
        logger.error(f"后端服务器启动失败: {e}")
        logger.error(traceback.format_exc())
        raise

def start_tts_server():
    """启动TTS服务器"""
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
        import subprocess
        subprocess.Popen(bat_path, cwd=bat_dir, creationflags=subprocess.CREATE_NEW_CONSOLE)
        logger.info("TTS服务器启动命令已执行")
    except Exception as e:
        logger.error(f"TTS服务器启动失败: {e}")
        logger.error(traceback.format_exc())

async def cleanup():
    """清理资源"""
    try:
        logger.info("正在清理资源...")
        # 关闭线程池
        executor.shutdown(wait=True)
        logger.info("线程池已关闭")
        
        # 获取当前事件循环
        loop = asyncio.get_event_loop()
        
        # 取消所有任务
        for task in asyncio.all_tasks(loop):
            task.cancel()
            
        # 等待所有任务完成
        await asyncio.gather(*asyncio.all_tasks(loop), return_exceptions=True)
        
        logger.info("资源清理完成")
    except Exception as e:
        logger.error(f"清理资源时发生错误: {e}")
        logger.error(traceback.format_exc())

async def main():
    try:
        # 检查数据库文件是否存在
        if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'ai_assistant.db')):
            # 初始化数据库
            logger.info("数据库不存在，正在初始化...")
            init_db()
        else:
            logger.info("数据库已存在，跳过初始化")
        
        # 创建QApplication实例
        logger.info("正在创建QApplication实例...")
        app = QApplication(sys.argv)
        
        # 设置应用程序图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config['ui']['icon_path'])
        app.setWindowIcon(QIcon(icon_path))
        
        # 创建事件循环
        logger.info("正在创建事件循环...")
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        # 显示登录对话框
        if SHOW_LOGIN_DIALOG:
            login_dialog = LoginDialog()
            if login_dialog.exec_() != QDialog.Accepted:
                logger.info("用户取消登录，退出程序")
                return
        
        # 启动后端服务器
        logger.info("正在启动后端服务器...")
        server_task = await start_backend_server()
        
        # 启动TTS服务器
        logger.info("正在启动TTS服务器...")
        start_tts_server()
        
        # 创建并显示主窗口
        logger.info("正在创建主窗口...")
        window = Live2DWindow()
        
        # 添加用户信息显示
        user_profile = UserProfileWidget(auth_manager, window)
        window.add_user_profile_widget(user_profile)
        
        window.show()
        logger.info("主窗口已显示")
        
        # 加载模型
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, config['live2d']['model_path'])
        logger.info(f"正在加载模型: {model_path}")
        
        # 确保模型路径存在
        if not os.path.exists(model_path):
            logger.error(f"模型文件不存在: {model_path}")
            return
            
        try:
            logger.info("开始加载模型...")
            window.load_model(model_path)
            logger.info("模型加载成功")
            
            # 创建更新定时器，驱动模型动画
            update_timer = QTimer()
            update_timer.timeout.connect(window.model_widget.update)
            update_timer.start(16)  # 约60FPS
            logger.info("更新定时器已启动")
            
            # 测试播放表情和动作
            def test_animations():
                try:
                    logger.info("开始测试动画...")
                    # 播放表情
                    window.play_expression("爱心眼")
                    logger.info("已播放表情：爱心眼")
                    
                    # 延迟2秒后播放动作
                    QTimer.singleShot(2000, lambda: window.play_motion("Scene1"))
                    logger.info("已安排动作：Scene1")
                    
                    # 延迟4秒后播放另一个表情
                    QTimer.singleShot(4000, lambda: window.play_expression("normal"))
                    logger.info("已安排表情：normal")
                except Exception as e:
                    logger.error(f"测试动画时发生错误: {e}")
                    logger.error(traceback.format_exc())
            
            # 延迟1秒后开始测试动画序列
            QTimer.singleShot(1000, test_animations)
            logger.info("已安排测试动画序列")
            
        except Exception as e:
            logger.error(f"加载模型时发生错误: {e}")
            logger.error(traceback.format_exc())
        
        # 运行应用
        logger.info("开始运行应用主循环...")
        with loop:
            try:
                loop.run_forever()
            finally:
                # 清理资源
                await cleanup()
                # 关闭事件循环
                loop.close()
            
    except Exception as e:
        logger.error(f"主程序发生错误: {e}")
        logger.error(traceback.format_exc())
        # 确保在发生错误时也清理资源
        await cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        logger.error(traceback.format_exc())