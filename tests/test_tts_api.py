import requests
import json

def test_character_list():
    """测试获取角色列表"""
    print("测试获取角色列表...")
    try:
        response = requests.get("http://127.0.0.1:8000/api/tts/characters")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"测试失败: {e}")

def test_tts():
    """测试文本转语音"""
    print("\n测试文本转语音...")
    try:
        # 准备测试数据
        data = {
            "text": "你好，这是一个测试",
            "character": "胡桃",  # 使用你实际有的角色名
            "emotion": "default",
            "text_language": "多语种混合",
            "speed": 1.0
        }
        
        # 发送请求
        response = requests.post(
            "http://127.0.0.1:8000/api/tts",
            data=data
        )
        
        print(f"状态码: {response.status_code}")
        
        # 如果是音频数据，保存到文件
        if response.status_code == 200 and response.headers.get("content-type") == "audio/wav":
            with open("test_output.wav", "wb") as f:
                f.write(response.content)
            print("音频已保存到 test_output.wav")
        else:
            print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    test_character_list()
    test_tts() 