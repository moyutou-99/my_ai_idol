from PIL import Image, ImageDraw

def create_mic_icon():
    # 创建麦克风图标
    img = Image.new('RGBA', (30, 30), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 绘制麦克风主体
    draw.ellipse([8, 4, 22, 18], fill=(100, 100, 100, 255))
    draw.rectangle([13, 18, 17, 26], fill=(100, 100, 100, 255))
    
    # 保存图标
    img.save('assets/icons/mic.png')

def create_send_icon():
    # 创建发送图标
    img = Image.new('RGBA', (30, 30), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 绘制发送箭头
    draw.polygon([(5, 15), (25, 5), (25, 25)], fill=(100, 100, 100, 255))
    
    # 保存图标
    img.save('assets/icons/send.png')

if __name__ == '__main__':
    create_mic_icon()
    create_send_icon() 