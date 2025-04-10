import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.audio.model_manager import ModelManager

def test_model_manager():
    """测试模型管理功能"""
    # 创建模型管理器实例
    manager = ModelManager(model_dir="test_models")
    
    print("开始模型管理测试...")
    
    # 列出可用模型
    print("\n可用模型列表:")
    models = manager.list_models()
    for model in models:
        status = "已安装" if model["available"] else "未安装"
        print(f"- {model['name']} ({model['info']['version']}): {status}")
        print(f"  描述: {model['info']['description']}")
        
    # 下载SenceVoice模型
    print("\n开始下载SenceVoice模型...")
    model_path = manager.get_model_path("sencevoice")
    if model_path:
        print(f"模型已下载: {model_path}")
    else:
        print("模型下载失败")
        
    # 再次检查模型状态
    print("\n模型状态检查:")
    if manager.check_model("sencevoice"):
        print("SenceVoice模型已就绪")
    else:
        print("SenceVoice模型未就绪")
        
if __name__ == "__main__":
    test_model_manager() 