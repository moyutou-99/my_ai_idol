import sys
from PyQt5.QtWidgets import QOpenGLWidget, QMenu, QAction, QInputDialog, QTextEdit, QPushButton, QHBoxLayout, QWidget, QVBoxLayout, QApplication, QLabel
from PyQt5.QtCore import QTimer, Qt, QPoint, QSize, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QLinearGradient, QBrush, QGuiApplication, QCursor, QIcon, QPen, QPainterPath
from OpenGL.GL import *
import live2d.v3 as live2d
from live2d.v3 import StandardParams
from live2d.utils import log
import json
import os
import logging
import random
import math
from collections import deque
from .live2d_parameters import Live2DParameters
import requests
import re

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Live2DModelWidget(QOpenGLWidget):
    """专门用于渲染Live2D模型的OpenGL窗口"""
    # 添加移动信号
    moved = pyqtSignal(QPoint)
    # 添加关闭信号
    closed = pyqtSignal()
    # 添加缩放信号
    scaled = pyqtSignal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.Tool | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 800, 600)  # 固定高度为600
        self.setStyleSheet("background-color: rgba(255, 255, 255, 200);")  # 白色背景
        
        # 存储上一次的位置
        self.last_position = self.pos()
        
        # 缩放相关参数
        self.scale_factor = 1.0  # 当前缩放比例
        self.min_scale = 0.5     # 最小缩放比例
        self.max_scale = 2.0     # 最大缩放比例
        self.scale_step = 0.05   # 每次缩放的步长，从0.1减小到0.05
        
        # 缩放动画相关
        self.target_scale = 1.0
        self.scale_animation_timer = QTimer()
        self.scale_animation_timer.timeout.connect(self._update_scale_animation)
        self.scale_animation_timer.start(16)  # 约60FPS的更新频率
        
        # 存储模型参数
        self.parameters = None
        self.drag_position = None
        self.is_dragging = False
        self.model = None
        self.model_path = None
        self.systemScale = QGuiApplication.primaryScreen().devicePixelRatio()
        
        # 眼睛追随控制
        self.eye_follow_enabled = True  # 眼睛追随功能开关
        
        # 点击区域设置
        self.click_area = {
            'x': 0,  # 将在resizeGL中设置为居中
            'y': 0,  # 将在resizeGL中设置为居中
            'width': 200,  # 默认宽度
            'height': 500  # 默认高度
        }
        self.show_click_area = False  # 默认隐藏点击区域
        
        # 动画状态管理
        self.animation_queue = deque()  # 动画队列
        self.current_animation = None   # 当前动画
        self.animation_timer = QTimer() # 动画计时器
        self.animation_timer.timeout.connect(self._process_animation_queue)
        self.animation_timer.start(16)  # 约60FPS的更新频率
        
        # 自动动作系统
        self.auto_action_timer = QTimer()
        self.auto_action_timer.timeout.connect(self._schedule_random_action)
        self.auto_action_timer.start(30000)  # 每30秒触发一次随机动作
        
        # 动画参数
        self.animation_speed = 1.0  # 动画速度
        self.animation_duration = 1000  # 默认动画持续时间(ms)
        
        # 物理参数
        self.angle_x = 0.0
        self.angle_y = 0.0
        self.angle_z = 0.0
        self.body_angle_x = 0.0
        
        # 眼睛跟随参数
        self.eye_follow_speed = 0.15  # 眼睛跟随速度
        self.target_eye_x = 0.0
        self.target_eye_y = 0.0
        self.current_eye_x = 0.0
        self.current_eye_y = 0.0
        
        # 表情配置
        self.expressions_config = {
            "困": {
                "file": "困.exp3.json",
                "folder": ""
            },
            "爱心眼": {
                "file": "爱心眼.exp3.json",
                "folder": ""
            },
            "生气": {
                "file": "生气.exp3.json",
                "folder": ""
            },
            "哭哭": {
                "file": "哭哭.exp3.json",
                "folder": ""
            },
            "星星眼": {
                "file": "星星眼.exp3.json",
                "folder": ""
            },
            "x": {
                "file": "x.exp3.json",
                "folder": ""
            },
            "呆呆": {
                "file": "呆呆.exp3.json",
                "folder": ""
            },
            "圆眼": {
                "file": "圆眼.exp3.json",
                "folder": ""
            },
            "猫猫嘴": {
                "file": "猫猫嘴.exp3.json",
                "folder": ""
            }
        }
        
        # 聊天窗口相关
        self.chat_window = None
        self.chat_window_stay_on_top = True
        self.character_name = "久久"  # 默认角色名称
        self.message_queue = []  # 添加消息队列
        
        # 对话气泡相关
        self.speech_bubble = None  # 初始化为None
        self.current_speech = None
        self.speech_timer = QTimer()
        self.speech_timer.timeout.connect(self._clear_speech)
        self.speech_timer.setSingleShot(True)
        
        # 初始化模型状态
        self.current_model = "local"  # 默认使用本地模型
        self.model_manager = ModelManager()
        
    def initializeGL(self):
        """初始化OpenGL"""
        try:
            # 将当前窗口作为OpenGL上下文
            self.makeCurrent()
            
            # 初始化Live2D
            live2d.init()
            live2d.setLogEnable(True)
            
            # 初始化Glew
            live2d.glewInit()
            
            logger.info("Live2D初始化成功")
            
            # 创建模型
            self.model = live2d.LAppModel()
            logger.info("Live2D模型创建成功")
            
            # 如果有待加载的模型，现在加载它
            if self.model_path:
                self._load_model_internal(self.model_path)
            
        except Exception as e:
            logger.error(f"OpenGL初始化失败: {e}")
            raise
            
    def paintGL(self):
        """绘制OpenGL场景"""
        try:
            # 清空缓冲区
            live2d.clearBuffer()
            
            # 更新模型状态
            if self.model:
                # 更新物理参数
                self._update_physics()
                
                # 更新眼睛位置
                if not self.is_dragging and self.eye_follow_enabled:
                    local_x = QCursor.pos().x() - self.x()
                    local_y = QCursor.pos().y() - self.y()
                    try:
                        self.model.Drag(local_x, local_y)
                    except SystemError:
                        pass
                
                # 更新模型参数
                self.model.Update()
                
                # 执行绘制
                self.model.Draw()
                
                # 绘制点击区域
                if self.show_click_area:
                    self._draw_click_area()
            
        except Exception as e:
            logger.error(f"绘制失败: {e}")
            
    def resizeGL(self, w, h):
        """处理窗口大小改变"""
        try:
            if self.model:
                self.model.Resize(w, h)
                
            # 更新点击区域位置，使其居中
            self._update_click_area()
            
        except Exception as e:
            logger.error(f"调整大小失败: {e}")
            
    def _update_physics(self):
        """更新物理参数"""
        if self.model:
            # 设置头部角度
            self.model.SetParameterValue(StandardParams.ParamAngleX, self.angle_x, 1.0)
            self.model.SetParameterValue(StandardParams.ParamAngleY, self.angle_y, 1.0)
            self.model.SetParameterValue(StandardParams.ParamAngleZ, self.angle_z, 1.0)
            
            # 设置身体角度
            self.model.SetParameterValue(StandardParams.ParamBodyAngleX, self.body_angle_x, 1.0)
            
            # 设置眼睛参数
            self.model.SetParameterValue(StandardParams.ParamEyeBallX, self.current_eye_x, 1.0)
            self.model.SetParameterValue(StandardParams.ParamEyeBallY, self.current_eye_y, 1.0)
            
            # 如果当前有表情，保持表情状态
            if hasattr(self, 'current_expression') and self.current_expression:
                try:
                    expr_config = self.expressions_config[self.current_expression]
                    expr_file = os.path.join(os.path.dirname(self.model_path), expr_config['file'])
                    
                    if os.path.exists(expr_file):
                        with open(expr_file, 'r', encoding='utf-8') as f:
                            expr_data = json.load(f)
                            
                        if expr_data.get('Type') == 'Live2D Expression':
                            for param in expr_data.get('Parameters', []):
                                param_id = param.get('Id')
                                value = float(param.get('Value', 0.0))
                                
                                if param_id:
                                    try:
                                        self.model.SetParameterValue(param_id, value, 1.0)
                                    except:
                                        pass
                except Exception as e:
                    logger.error(f"保持表情状态失败: {e}")
            
    def _load_model_internal(self, model_path):
        """内部加载模型的方法"""
        try:
            # 检查文件是否存在
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"模型文件不存在: {model_path}")
            
            # 加载模型JSON
            self.model.LoadModelJson(model_path)
            logger.info("模型JSON加载成功")
            
            # 设置模型大小
            self.model.Resize(self.width(), self.height())
            logger.info("模型大小设置成功")
            
            # 加载参数
            self.parameters = Live2DParameters(os.path.dirname(model_path))
            logger.info("模型参数加载成功")
            
            # 启用自动眨眼和呼吸
            self.model.SetAutoBlinkEnable(True)
            self.model.SetAutoBreathEnable(True)
            logger.info("自动眨眼和呼吸已启用")
            
            # 设置默认表情
            self.play_expression("normal")
            logger.info("默认表情设置成功")
            
            # 创建对话气泡
            if self.speech_bubble is None:
                self.speech_bubble = SpeechBubble()
                self.speech_bubble.show()
                self.speech_bubble.update_position(self.pos(), self.size())
            
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            raise
            
    def load_model(self, model_path):
        """加载Live2D模型"""
        logger.info(f"开始加载模型: {model_path}")
        self.model_path = model_path
        
        # 如果OpenGL已经初始化，直接加载模型
        if self.model:
            self._load_model_internal(model_path)
            
    def _process_animation_queue(self):
        """处理动画队列"""
        if not self.animation_queue:
            return
            
        if not self.current_animation:
            # 如果没有正在播放的动画，从队列中取出下一个
            self.current_animation = self.animation_queue.popleft()
            self._play_animation(self.current_animation)
            
    def _play_animation(self, animation):
        """播放单个动画"""
        try:
            if animation['type'] == 'motion':
                # 设置动作开始和结束回调
                def on_start(group, no):
                    logger.info(f"动作开始: {group}_{no}")
                    
                def on_finish():
                    logger.info("动作结束")
                    self._on_animation_complete()
                    
                # 获取鼠标位置（居中）
                x = self.width() // 2
                y = self.height() // 2
                
                # 播放动作
                self.model.Touch(x, y, on_start, on_finish)
                self.model.StartMotion(animation['file'])
                
            elif animation['type'] == 'expression':
                # 设置表情
                self.play_expression(animation['file'])
                # 设置表情持续时间
                QTimer.singleShot(int(animation.get('duration', self.animation_duration)), 
                                self._on_animation_complete)
                                          
        except Exception as e:
            logger.error(f"播放动画失败: {e}")
            
    def _on_animation_complete(self):
        """动画完成回调"""
        self.current_animation = None
        self._process_animation_queue()
        
    def _schedule_random_action(self):
        """安排随机动作"""
        if not self.parameters:
            return
            
        # 随机选择动作类型
        action_type = random.choice(['motion', 'expression'])
        
        if action_type == 'motion':
            motions = self.parameters.get_motions()
            if motions:
                motion = random.choice(motions)
                self.queue_animation({
                    'type': 'motion',
                    'file': motion['file'],
                    'duration': random.randint(2000, 5000)
                })
        else:
            expressions = self.parameters.get_expressions()
            if expressions:
                expression = random.choice(expressions)
                self.queue_animation({
                    'type': 'expression',
                    'file': expression['file'],
                    'duration': random.randint(1000, 3000)
                })
                
    def queue_animation(self, animation):
        """将动画添加到队列"""
        self.animation_queue.append(animation)
        if not self.current_animation:
            self._process_animation_queue()
            
    def play_expression(self, expression_name):
        """播放表情"""
        try:
            if expression_name in self.expressions_config:
                expr_config = self.expressions_config[expression_name]
                expr_file = os.path.join(os.path.dirname(self.model_path), expr_config['file'])
                
                if os.path.exists(expr_file):
                    # 读取表情文件
                    with open(expr_file, 'r', encoding='utf-8') as f:
                        expr_data = json.load(f)
                        
                    # 检查是否是有效的表情文件
                    if expr_data.get('Type') == 'Live2D Expression':
                        # 重置所有表情相关参数
                        for param_id in ['ParamEyeLOpen', 'ParamEyeROpen', 'ParamBrowLY', 'ParamBrowRY', 
                                      'ParamBrowLX', 'ParamBrowRX', 'ParamMouthForm', 'ParamMouthOpenY',
                                      'Param46', 'Param47', 'Param48', 'Param49', 'Param50', 'Param51',
                                      'Param52', 'Param53', 'Param54', 'Param55', 'Param56', 'Param57',
                                      'Param58']:
                            try:
                                self.model.SetParameterValue(param_id, 0.0, 1.0)
                            except:
                                pass
                        
                        # 设置每个参数
                        for param in expr_data.get('Parameters', []):
                            param_id = param.get('Id')
                            value = float(param.get('Value', 0.0))
                            
                            if param_id:
                                try:
                                    # 使用1.0的权重，确保表情立即生效
                                    self.model.SetParameterValue(param_id, value, 1.0)
                                    logger.info(f"设置参数 {param_id} = {value}")
                                except Exception as e:
                                    logger.error(f"设置参数 {param_id} 失败: {e}")
                                    
                        logger.info(f"切换表情: {expression_name}")
                        # 强制更新显示
                        self.update()
                        
                        # 保存当前表情状态
                        self.current_expression = expression_name
                    else:
                        logger.error(f"无效的表情文件格式: {expr_file}")
                else:
                    logger.error(f"表情文件不存在: {expr_file}")
            else:
                logger.error(f"未找到表情配置: {expression_name}")
        except Exception as e:
            logger.error(f"播放表情失败: {e}")
            
    def play_motion(self, motion_name):
        """播放动作"""
        try:
            if self.parameters:
                motion = self.parameters.get_motion(motion_name)
                if motion:
                    self.queue_animation({
                        'type': 'motion',
                        'file': motion['file'],
                        'duration': self.animation_duration
                    })
        except Exception as e:
            logger.error(f"播放动作失败: {e}")
            
    def set_animation_speed(self, speed):
        """设置动画速度"""
        self.animation_speed = max(0.1, min(2.0, speed))
        if self.model:
            self.model.SetSpeed(self.animation_speed)
            
    def clear_animation_queue(self):
        """清空动画队列"""
        self.animation_queue.clear()
        self.current_animation = None
        
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            # 检查点击是否在点击区域内
            if self._is_inside_click_area(event.pos()):
                # 兼容不同版本的PyQt
                try:
                    self.drag_position = event.globalPosition().toPoint()
                except AttributeError:
                    self.drag_position = event.globalPos()
                self.is_dragging = True
        elif event.button() == Qt.RightButton:
            # 检查点击是否在点击区域内
            if self._is_inside_click_area(event.pos()):
                # 兼容不同版本的PyQt
                try:
                    global_pos = event.globalPosition().toPoint()
                except AttributeError:
                    global_pos = event.globalPos()
                self.show_context_menu(global_pos)
            
    def _is_inside_click_area(self, pos):
        """检查点击位置是否在点击区域内"""
        return (self.click_area['x'] <= pos.x() <= self.click_area['x'] + self.click_area['width'] and
                self.click_area['y'] <= pos.y() <= self.click_area['y'] + self.click_area['height'])
                
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.is_dragging and event.buttons() == Qt.LeftButton:
            # 只有在点击区域内才能拖动
            if self._is_inside_click_area(event.pos()):
                try:
                    new_pos = event.globalPosition().toPoint()
                except AttributeError:
                    new_pos = event.globalPos()
                self.move(self.pos() + new_pos - self.drag_position)
                self.drag_position = new_pos
                # 发出移动信号
                self.moved.emit(self.pos())
                event.accept()
        else:
            # 更新眼睛位置
            if self.eye_follow_enabled:
                local_x = event.pos().x()
                local_y = event.pos().y()
                try:
                    self.model.Drag(local_x, local_y)
                except SystemError:
                    pass
                self.update()
            
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            
    def show_context_menu(self, pos):
        """显示右键菜单"""
        menu = QMenu()
        
        # 添加眼睛追随开关选项
        eye_follow_action = QAction("眼睛追随", self)
        eye_follow_action.setCheckable(True)
        eye_follow_action.setChecked(self.eye_follow_enabled)
        eye_follow_action.triggered.connect(self.toggle_eye_follow)
        menu.addAction(eye_follow_action)
        
        menu.addSeparator()
        
        # 添加模型切换选项
        model_menu = QMenu("模型切换", self)
        model_menu.setStyleSheet("""
            QMenu {
                background-color: rgba(255, 255, 255, 230);
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QMenu::item {
                background-color: transparent;
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: rgba(240, 240, 240, 200);
            }
            QMenu::separator {
                height: 1px;
                background-color: #ccc;
                margin: 5px 0px;
            }
        """)
        menu.addMenu(model_menu)
        
        # 添加模型选项
        local_model_action = QAction("本地模型", self)
        local_model_action.setCheckable(True)
        local_model_action.setChecked(self.current_model == "local")
        local_model_action.triggered.connect(lambda: self.switch_model("local"))
        model_menu.addAction(local_model_action)
        
        deepseek_model_action = QAction("D老师", self)
        deepseek_model_action.setCheckable(True)
        deepseek_model_action.setChecked(self.current_model == "deepseek")
        deepseek_model_action.triggered.connect(lambda: self.switch_model("deepseek"))
        model_menu.addAction(deepseek_model_action)
        
        ph_model_action = QAction("幻日-施工中，暂不可用", self)
        ph_model_action.setCheckable(True)
        ph_model_action.setChecked(self.current_model == "ph")
        ph_model_action.triggered.connect(lambda: self.switch_model("ph"))
        model_menu.addAction(ph_model_action)
        
        menu.addSeparator()
        
        # 添加聊天窗口控制选项
        chat_menu = QMenu("聊天窗口", self)
        chat_menu.setStyleSheet(model_menu.styleSheet())
        menu.addMenu(chat_menu)
        
        # 打开/关闭聊天窗口
        toggle_chat_action = QAction("打开/关闭聊天窗口", self)
        toggle_chat_action.triggered.connect(self.toggle_chat_window)
        chat_menu.addAction(toggle_chat_action)
        
        # 置顶/取消置顶聊天窗口
        stay_on_top_action = QAction("置顶聊天窗口", self)
        stay_on_top_action.setCheckable(True)
        stay_on_top_action.setChecked(self.chat_window_stay_on_top)
        stay_on_top_action.triggered.connect(self.toggle_chat_window_stay_on_top)
        chat_menu.addAction(stay_on_top_action)
        
        # 添加字体大小设置子菜单
        font_size_menu = QMenu("字体大小", self)
        font_size_menu.setStyleSheet(chat_menu.styleSheet())
        chat_menu.addMenu(font_size_menu)
        
        # 添加字体大小选项
        font_sizes = [12, 14, 16, 18, 20]
        for size in font_sizes:
            font_size_action = QAction(f"{size}px", self)
            font_size_action.setCheckable(True)
            if self.chat_window and self.chat_window.font_size == size:
                font_size_action.setChecked(True)
            font_size_action.triggered.connect(lambda checked, s=size: self.set_chat_font_size(s))
            font_size_menu.addAction(font_size_action)
        
        menu.addSeparator()
        
        # 添加点击区域控制选项
        click_area_menu = QMenu("点击区域", self)
        click_area_menu.setStyleSheet(chat_menu.styleSheet())
        menu.addMenu(click_area_menu)
        
        # 显示/隐藏点击区域
        show_area_action = QAction("显示/隐藏区域", self)
        show_area_action.setCheckable(True)
        show_area_action.setChecked(self.show_click_area)
        show_area_action.triggered.connect(self.toggle_click_area_visibility)
        click_area_menu.addAction(show_area_action)
        
        # 调整宽度
        width_action = QAction("调整宽度", self)
        width_action.triggered.connect(self.input_click_area_width)
        click_area_menu.addAction(width_action)
        
        # 调整高度
        height_action = QAction("调整高度", self)
        height_action.triggered.connect(self.input_click_area_height)
        click_area_menu.addAction(height_action)
        
        menu.addSeparator()
        
        # 添加表情控制选项
        expression_menu = QMenu("表情控制", self)
        expression_menu.setStyleSheet(chat_menu.styleSheet())
        menu.addMenu(expression_menu)
        
        # 添加每个表情选项
        for expr_name, expr_config in self.expressions_config.items():
            expr_action = QAction(expr_name, self)
            expr_action.triggered.connect(lambda checked, name=expr_name: self.play_expression(name))
            expression_menu.addAction(expr_action)
        
        # 添加其他选项
        menu.addSeparator()
        close_action = QAction("关闭", self)
        close_action.triggered.connect(self.close_model)
        menu.addAction(close_action)
        
        # 设置主菜单样式
        menu.setStyleSheet(chat_menu.styleSheet())
        
        # 显示菜单
        menu.exec(pos)
        
    def toggle_eye_follow(self):
        """切换眼睛追随功能"""
        self.eye_follow_enabled = not self.eye_follow_enabled
        logger.info(f"眼睛追随功能: {'开启' if self.eye_follow_enabled else '关闭'}")
        
    def toggle_click_area_visibility(self):
        """切换点击区域显示状态"""
        self.show_click_area = not self.show_click_area
        self.update()
        
    def input_click_area_width(self):
        """输入点击区域宽度"""
        width, ok = QInputDialog.getInt(
            self, 
            "调整宽度",
            "请输入宽度(像素):",
            self.click_area['width'],
            50,  # 最小值
            self.width(),  # 最大值
            1  # 步长
        )
        if ok:
            self.set_click_area_width(width)
            
    def input_click_area_height(self):
        """输入点击区域高度"""
        height, ok = QInputDialog.getInt(
            self, 
            "调整高度",
            "请输入高度(像素):",
            self.click_area['height'],
            50,  # 最小值
            self.height(),  # 最大值
            1  # 步长
        )
        if ok:
            self.set_click_area_height(height)
            
    def set_click_area_width(self, width):
        """设置点击区域宽度并居中"""
        self.click_area['width'] = width
        # 更新位置使其居中
        self.click_area['x'] = (self.width() - width) // 2
        self.update()
        
    def set_click_area_height(self, height):
        """设置点击区域高度并居中"""
        self.click_area['height'] = height
        # 更新位置使其居中
        self.click_area['y'] = (self.height() - height) // 2
        self.update()
        
    def set_expression(self, expression_file):
        """设置表情"""
        try:
            if self.model:
                # 检查文件是否存在
                if not os.path.exists(expression_file):
                    logger.error(f"表情文件不存在: {expression_file}")
                    return
                    
                # 读取表情文件
                with open(expression_file, 'r', encoding='utf-8') as f:
                    expr_data = json.load(f)
                    
                # 检查是否是有效的表情文件
                if expr_data.get('Type') == 'Live2D Expression':
                    # 重置所有表情参数
                    for param in self.parameters.get_parameters():
                        if param.startswith('Param'):
                            self.model.SetParameterValue(param, 0.0, 1.0)
                    
                    # 设置每个参数
                    for param in expr_data.get('Parameters', []):
                        param_id = param.get('Id')
                        value = float(param.get('Value', 0.0))  # 确保值是浮点数
                        blend = param.get('Blend', 'Add')
                        
                        if param_id:
                            try:
                                # 根据混合模式设置参数
                                if blend == 'Add':
                                    # 获取当前值并添加
                                    current_value = float(self.model.GetParameterValue(param_id))
                                    self.model.SetParameterValue(param_id, current_value + value, 1.0)
                                else:
                                    # 直接设置值
                                    self.model.SetParameterValue(param_id, value, 1.0)
                                
                                logger.info(f"设置参数 {param_id} = {value} (混合模式: {blend})")
                            except Exception as e:
                                logger.error(f"设置参数 {param_id} 失败: {e}")
                            
                    # 强制更新显示
                    self.update()
                else:
                    logger.error(f"无效的表情文件格式: {expression_file}")
                    
        except Exception as e:
            logger.error(f"设置表情失败: {e}")
            
    def _draw_click_area(self):
        """绘制点击区域"""
        try:
            # 保存当前OpenGL状态
            glPushAttrib(GL_ALL_ATTRIB_BITS)
            
            # 设置2D投影
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            glOrtho(0, self.width(), self.height(), 0, -1, 1)
            
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            glLoadIdentity()
            
            # 禁用深度测试和光照
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_LIGHTING)
            
            # 启用线条抗锯齿
            glEnable(GL_LINE_SMOOTH)
            glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
            
            # 设置线条宽度
            glLineWidth(2.0)
            
            # 设置虚线样式
            glEnable(GL_LINE_STIPPLE)
            glLineStipple(1, 0x00FF)
            
            # 设置线条颜色（红色）
            glColor3f(1.0, 0.0, 0.0)
            
            # 绘制矩形
            glBegin(GL_LINE_LOOP)
            glVertex2f(self.click_area['x'], self.click_area['y'])
            glVertex2f(self.click_area['x'] + self.click_area['width'], self.click_area['y'])
            glVertex2f(self.click_area['x'] + self.click_area['width'], self.click_area['y'] + self.click_area['height'])
            glVertex2f(self.click_area['x'], self.click_area['y'] + self.click_area['height'])
            glEnd()
            
            # 恢复OpenGL状态
            glPopMatrix()
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)
            glPopAttrib()
            
        except Exception as e:
            logger.error(f"绘制点击区域失败: {e}")

    def moveEvent(self, event):
        """处理窗口移动事件"""
        # 获取新位置
        new_pos = self.pos()
        
        # 如果位置发生变化，发出移动信号
        if new_pos != self.last_position:
            self.moved.emit(new_pos)
            self.last_position = new_pos
            
            # 更新气泡位置
            if self.speech_bubble:
                self.speech_bubble.update_position(new_pos, self.size())
            
        super().moveEvent(event)
        
    def close_model(self):
        """关闭模型和输入框"""
        # 关闭聊天窗口
        if self.chat_window:
            self.chat_window.close()  # 这里使用close而不是hide，因为模型窗口要完全关闭
            self.chat_window = None
            
        # 关闭对话气泡
        if self.speech_bubble:
            self.speech_bubble.close()
            self.speech_bubble = None
            
        # 关闭模型窗口
        self.close()
        # 发出关闭信号，通知主窗口关闭输入框
        self.closed.emit()
        # 关闭整个应用程序
        QApplication.instance().quit()
        # 强制退出程序
        sys.exit(0)

    def wheelEvent(self, event):
        """处理鼠标滚轮事件，实现缩放功能"""
        # 获取鼠标在窗口内的位置
        mouse_pos = event.pos()
        
        # 检查鼠标是否在点击区域内
        if self._is_inside_click_area(mouse_pos):
            # 计算新的缩放比例
            delta = event.angleDelta().y()
            
            # 使用固定的缩放步长，避免动态变化导致的抖动
            if delta > 0:
                # 放大
                self.target_scale = min(self.target_scale + 0.05, self.max_scale)
            else:
                # 缩小
                self.target_scale = max(self.target_scale - 0.05, self.min_scale)
            
            # 接受事件
            event.accept()
            return
            
        # 如果不在点击区域内，不处理滚轮事件
        super().wheelEvent(event)
        
    def _update_scale_animation(self):
        """更新缩放动画"""
        if self.scale_factor != self.target_scale:
            # 使用更稳定的插值算法，减少抖动
            diff = self.target_scale - self.scale_factor
            
            # 如果差异很小，直接设置为目标值
            if abs(diff) < 0.01:
                self.scale_factor = self.target_scale
            else:
                # 使用固定的缓动系数，避免动态变化导致的抖动
                easing_factor = 0.15
                self.scale_factor += diff * easing_factor
            
            # 调整窗口大小
            base_width = 800
            base_height = 600
            new_width = int(base_width * self.scale_factor)
            new_height = int(base_height * self.scale_factor)
            
            # 保持窗口中心点不变
            center_x = self.x() + self.width() // 2
            center_y = self.y() + self.height() // 2
            new_x = center_x - new_width // 2
            new_y = center_y - new_height // 2
            
            # 设置新的窗口大小和位置
            self.setGeometry(new_x, new_y, new_width, new_height)
            
            # 更新点击区域
            self._update_click_area()
            
            # 更新模型
            self.update()
        
    def _update_click_area(self):
        """更新点击区域位置和大小"""
        # 根据当前窗口大小调整点击区域
        self.click_area['width'] = int(200 * self.scale_factor)
        self.click_area['height'] = int(500 * self.scale_factor)
        
        # 居中显示
        self.click_area['x'] = (self.width() - self.click_area['width']) // 2
        self.click_area['y'] = (self.height() - self.click_area['height']) // 2
        
    def toggle_chat_window(self):
        """切换聊天窗口的显示状态"""
        if self.chat_window is None:
            # 创建新的聊天窗口
            self.chat_window = ChatWindow()
            # 显示所有历史消息
            for sender, message in self.message_queue:
                self.chat_window.add_message(sender, message)
            self.chat_window.show()
        else:
            if self.chat_window.isVisible():
                # 如果窗口可见，则隐藏它
                self.chat_window.hide()
            else:
                # 如果窗口不可见，则显示它
                self.chat_window.show()
            
    def toggle_chat_window_stay_on_top(self):
        """切换聊天窗口的置顶状态"""
        self.chat_window_stay_on_top = not self.chat_window_stay_on_top
        if self.chat_window:
            self.chat_window.toggle_stay_on_top(self.chat_window_stay_on_top)
            
    def add_chat_message(self, sender, message):
        """添加消息到聊天窗口"""
        # 将消息添加到队列
        self.message_queue.append((sender, message))
        
        # 如果聊天窗口存在，显示消息
        if self.chat_window:
            self.chat_window.add_message(sender, message)
            
    def set_chat_font_size(self, size):
        """设置聊天窗口字体大小"""
        if self.chat_window:
            self.chat_window.set_font_size(size)

    def _clear_speech(self):
        """清除对话气泡内容"""
        self.current_speech = None
        self.speech_bubble.set_text("...")
        
    def show_speech(self, text, duration=5000):
        """显示对话气泡"""
        self.current_speech = text
        self.speech_bubble.set_text(text)
        self.speech_bubble.update_position(self.pos(), self.size())
        self.speech_timer.start(duration)

    def switch_model(self, model_name):
        """切换模型"""
        if model_name == self.current_model:
            return
            
        self.current_model = model_name
        self.model_manager.switch_model(model_name)
        
        # 更新状态栏显示
        if hasattr(self, 'status_bar'):
            self.status_bar.showMessage(f"已切换到{model_name}模型", 3000)

class ModelManager:
    def __init__(self):
        # 初始化模型状态
        self.current_model = "local"
        self.supported_models = {
            "local": "本地模型",
            "deepseek": "D老师",
            "ph": "幻日"
        }
        
    def switch_model(self, model_name):
        """切换模型"""
        try:
            if model_name not in self.supported_models:
                logger.error(f"不支持的模型类型: {model_name}")
                return False
                
            if model_name == self.current_model:
                logger.info(f"已经是{self.supported_models[model_name]}模型，无需切换")
                return True
                
            # 发送HTTP请求到后端API进行模型切换
            try:
                if model_name == "deepseek":
                    response = requests.post("http://localhost:8000/api/deepseek/load")
                elif model_name == "ph":
                    response = requests.post("http://localhost:8000/api/ph/load")
                else:
                    response = requests.post("http://localhost:8000/api/local/load")
                    
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        self.current_model = model_name
                        logger.info(f"成功切换到{self.supported_models[model_name]}模型")
                        return True
                    else:
                        error_msg = result.get("message", "未知错误")
                        logger.error(f"模型切换失败: {error_msg}")
                        return False
                else:
                    logger.error(f"模型切换请求失败，状态码: {response.status_code}")
                    return False
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"模型切换请求失败: {e}")
                return False
                
        except Exception as e:
            logger.error(f"模型切换过程中发生错误: {e}")
            return False
            
    def get_current_model_info(self):
        """获取当前模型信息"""
        return {
            "name": self.current_model,
            "display_name": self.supported_models.get(self.current_model, "未知模型")
        }

class Live2DWindow(QWidget):
    """主窗口，包含Live2D模型和输入框"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live2D Desktop Pet")
        self.setGeometry(100, 100, 800, 640)  # 初始窗口大小从650改为640
        self.setWindowFlags(Qt.Window | Qt.Tool | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 创建Live2D模型窗口
        self.model_widget = Live2DModelWidget()
        self.model_widget.setGeometry(100, 100, 800, 600)  # 固定高度为600
        
        # 连接模型窗口的关闭信号
        self.model_widget.closed.connect(self.close_input_container)
        
        # 创建输入框和按钮容器作为独立窗口
        self.input_container = QWidget(None)  # 不设置父窗口
        self.input_container.setWindowFlags(Qt.Window | Qt.Tool | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.input_container.setAttribute(Qt.WA_TranslucentBackground)
        
        # 初始化输入框位置，使其位于模型底部
        model_pos = self.model_widget.pos()
        model_width = self.model_widget.width()
        model_height = self.model_widget.height()
        
        # 计算模型底部中心位置
        model_bottom_center_x = model_pos.x() + model_width // 2
        
        # 计算输入框的位置，使其水平居中于模型底部
        input_x = model_bottom_center_x - 490 // 2
        
        # 计算输入框的垂直位置，使其位于模型底部
        input_y = model_pos.y() + model_height - 60  # 距离底部60像素
        
        # 设置输入框容器的位置和大小
        self.input_container.setGeometry(
            input_x,
            input_y,
            490, 40  # 确保有足够的高度
        )
        
        # 创建垂直布局
        self.main_layout = QVBoxLayout(self.input_container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 创建水平布局用于输入框和按钮
        self.input_layout = QHBoxLayout()
        self.input_layout.setContentsMargins(0, 0, 0, 0)
        self.input_layout.setSpacing(5)
        
        # 创建输入框
        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("输入消息...")
        self.input_box.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 200);  /* 白色背景 */
                border: 1px solid #ccc;
                border-radius: 15px;
                padding: 5px 10px;
                font-size: 14px;
                min-height: 28px;
            }
            QTextEdit:focus {
                border: 1px solid #0078d7;  /* 蓝色边框 */
                background-color: rgba(255, 255, 255, 200);  /* 聚焦时更亮的白色 */
            }
        """)
        self.input_box.setFixedHeight(28)  # 从20增加到30，设置为1.5倍文字高度
        self.input_box.setMinimumHeight(28)  # 从20增加到30
        self.input_box.setMaximumHeight(100)  # 设置最大高度
        self.input_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # 添加垂直滚动条
        self.input_box.setAcceptRichText(False)  # 只接受纯文本
        self.input_box.textChanged.connect(self.adjust_input_height)
        self.input_box.setFocusPolicy(Qt.StrongFocus)  # 设置焦点策略
        self.input_box.setMouseTracking(True)  # 启用鼠标追踪
        self.input_box.setReadOnly(False)  # 确保输入框可编辑
        self.input_box.setTabChangesFocus(False)  # 禁用Tab键切换焦点
        self.input_box.setFocus()  # 初始设置焦点
        self.input_box.installEventFilter(self)  # 安装事件过滤器
        
        # 创建按钮容器
        self.button_container = QWidget()
        self.button_container.setFixedWidth(70)
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(5)
        
        # 创建语音按钮
        self.voice_button = QPushButton()
        self.voice_button.setIcon(QIcon("assets/icons/mic.png"))
        self.voice_button.setFixedSize(30, 30)
        self.voice_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 200);  /* 白色背景 */
                border: 1px solid #ccc;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 200);  /* 悬停时更亮的白色 */
            }
        """)
        
        # 创建发送按钮
        self.send_button = QPushButton()
        self.send_button.setIcon(QIcon("assets/icons/send.png"))
        self.send_button.setFixedSize(30, 30)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 200);  /* 白色背景 */
                border: 1px solid #ccc;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 200);  /* 悬停时更亮的白色 */
            }
        """)
        
        # 添加按钮到按钮布局
        self.button_layout.addWidget(self.voice_button)
        self.button_layout.addWidget(self.send_button)
        
        # 添加输入框和按钮容器到水平布局
        self.input_layout.addWidget(self.input_box)
        self.input_layout.addWidget(self.button_container)
        
        # 添加水平布局到主布局
        self.main_layout.addLayout(self.input_layout)
        
        # 连接按钮信号
        self.voice_button.clicked.connect(self.start_voice_input)
        self.send_button.clicked.connect(self.send_message)
        
        # 连接模型窗口的移动信号
        self.model_widget.moved.connect(self.on_model_moved)
        
        # 添加录音状态变量
        self.is_recording = False
        
        # 显示窗口
        self.show()
        self.input_container.show()  # 显示输入框容器
        
    def on_model_scaled(self, scale_factor):
        """当模型窗口缩放时更新输入框位置"""
        # 获取模型窗口的新位置和大小
        model_pos = self.model_widget.pos()
        model_width = self.model_widget.width()
        model_height = self.model_widget.height()
        
        # 计算输入框的新位置，使其始终保持在模型脚底下
        # 计算模型底部中心位置
        model_bottom_center_x = model_pos.x() + model_width // 2
        
        # 计算输入框的新位置，使其水平居中于模型底部
        new_input_x = model_bottom_center_x - 490 // 2
        
        # 计算输入框的垂直位置，使其位于模型底部
        # 根据缩放比例动态调整距离
        # 当scale_factor为1.0时，距离为60像素
        # 当scale_factor为2.0时，距离为120像素
        # 当scale_factor为0.5时，距离为30像素
        base_distance = 60  # 基础距离
        distance = int(base_distance * (1 + (scale_factor - 1) * 0.5))  # 根据缩放比例调整距离
        new_input_y = model_pos.y() + model_height - distance
        
        # 设置新的输入框位置
        self.input_container.move(new_input_x, new_input_y)
        
        # 确保输入框容器和输入框在最顶层
        self.input_container.raise_()
        self.input_box.raise_()
        
    def close_input_container(self):
        """关闭输入框容器"""
        self.input_container.close()
        
    def on_model_moved(self, new_pos):
        """当模型窗口移动时更新输入框位置"""
        # 获取模型窗口的新位置和大小
        model_width = self.model_widget.width()
        model_height = self.model_widget.height()
        
        # 获取当前缩放比例
        scale_factor = self.model_widget.scale_factor
        
        # 计算模型底部中心位置
        model_bottom_center_x = new_pos.x() + model_width // 2
        
        # 计算输入框的新位置，使其水平居中于模型底部
        new_input_x = model_bottom_center_x - 490 // 2
        
        # 计算输入框的垂直位置，使其位于模型底部
        # 根据缩放比例动态调整距离
        base_distance = 60  # 基础距离
        distance = int(base_distance * (1 + (scale_factor - 1) * 0.5))  # 根据缩放比例调整距离
        new_input_y = new_pos.y() + model_height - distance
        
        # 设置新的输入框位置
        self.input_container.move(new_input_x, new_input_y)
        
        # 确保输入框容器和输入框在最顶层
        self.input_container.raise_()
        self.input_box.raise_()
        
    def load_model(self, model_path):
        """加载Live2D模型"""
        self.model_widget.load_model(model_path)
        self.model_widget.show()
        
    def play_expression(self, expression_name):
        """播放表情"""
        self.model_widget.play_expression(expression_name)
        
    def play_motion(self, motion_name):
        """播放动作"""
        self.model_widget.play_motion(motion_name)
        
    def start_voice_input(self):
        """开始或停止语音输入"""
        if not self.is_recording:
            # 开始录音
            try:
                # 发送开始录音请求
                response = requests.post("http://127.0.0.1:8000/api/start_recording")
                if response.status_code == 200:
                    data = response.json()
                    if data["status"] == "success":
                        # 更新按钮状态
                        self.voice_button.setEnabled(True)  # 保持按钮可用，以便可以再次点击停止
                        self.voice_button.setStyleSheet("""
                            QPushButton {
                                background-color: rgba(255, 0, 0, 200);  /* 红色背景表示正在录音 */
                                border: 1px solid #ccc;
                                border-radius: 15px;
                            }
                        """)
                        
                        # 设置录音状态
                        self.is_recording = True
                        
                        # 开始轮询识别结果
                        self.recognition_timer = QTimer(self)
                        self.recognition_timer.timeout.connect(self._check_recognition_result)
                        self.recognition_timer.start(1000)  # 每秒检查一次
                        
                        logger.info("开始录音")
                    else:
                        self.backend_signals.error_occurred.emit(data["message"])
            except Exception as e:
                logger.error(f"启动录音失败: {e}")
                self.backend_signals.error_occurred.emit(str(e))
        else:
            # 停止录音
            self._stop_recording()
            
    def _check_recognition_result(self):
        """检查语音识别结果"""
        try:
            response = requests.get("http://127.0.0.1:8000/api/recognition_result")
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "success" and data["text"]:
                    # 将识别结果填入输入框
                    current_text = self.input_box.toPlainText()
                    if current_text:
                        self.input_box.setText(current_text + " " + data["text"])
                    else:
                        self.input_box.setText(data["text"])
                    
                    # 不再自动停止录音，让用户手动停止
                    # self._stop_recording()
                    
        except Exception as e:
            logger.error(f"获取识别结果失败: {e}")
            
    def _stop_recording(self):
        """停止录音"""
        try:
            # 发送停止录音请求
            response = requests.post("http://127.0.0.1:8000/api/stop_recording")
            if response.status_code == 200:
                # 恢复按钮状态
                self.voice_button.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(255, 255, 255, 200);
                        border: 1px solid #ccc;
                        border-radius: 15px;
                    }
                    QPushButton:hover {
                        background-color: rgba(255, 255, 255, 200);
                    }
                """)
                
                # 更新录音状态
                self.is_recording = False
                
                # 停止轮询
                if hasattr(self, 'recognition_timer'):
                    self.recognition_timer.stop()
                    
                logger.info("停止录音")
        except Exception as e:
            logger.error(f"停止录音失败: {e}")
        
    def send_message(self):
        """发送消息"""
        message = self.input_box.toPlainText().strip()
        if message:
            # 将消息发送到聊天窗口
            self.model_widget.add_chat_message("我", message)
            
            # 发送消息到后端LLM模块
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/api/chat",
                    data={"message": message}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data["status"] == "success":
                        # 添加LLM的回复到聊天窗口
                        self.model_widget.add_chat_message(self.model_widget.character_name, data["message"])
                        # 在气泡中显示回复
                        self.model_widget.show_speech(data["message"])
                    else:
                        error_msg = f"错误：{data['message']}"
                        self.model_widget.add_chat_message("系统", error_msg)
                        self.model_widget.show_speech(error_msg)
                else:
                    error_msg = "与服务器通信失败"
                    self.model_widget.add_chat_message("系统", error_msg)
                    self.model_widget.show_speech(error_msg)
            except Exception as e:
                error_msg = f"发送消息失败：{str(e)}"
                self.model_widget.add_chat_message("系统", error_msg)
                self.model_widget.show_speech(error_msg)
            
            # 清空输入框
            self.input_box.clear()
            
    def adjust_input_height(self):
        """根据输入框内容调整高度"""
        # 获取文本内容
        text = self.input_box.toPlainText()
        # 计算文本长度
        text_length = len(text)
        
        # 如果文本长度超过30个字符，增加输入框高度
        if text_length > 30:
            # 计算需要增加的高度（每30个字符增加一行）
            additional_lines = (text_length - 1) // 30
            new_height = 40 + (additional_lines * 20)  # 每行增加20像素高度
            
            # 限制最大高度
            max_height = 120
            new_height = min(new_height, max_height)
            
            # 调整输入框容器高度
            self.input_container.setFixedHeight(new_height)
            
            # 调整输入框高度
            self.input_box.setFixedHeight(new_height - 10)  # 留出一些边距
            
            # 调整窗口大小，但保持模型区域不变
            current_width = self.width()
            current_model_height = 600  # 模型区域高度
            new_window_height = current_model_height + new_height  # 模型区域高度加上输入框高度
            self.resize(current_width, new_window_height)
            
            # 更新输入框位置，使其始终保持在模型底部
            model_pos = self.model_widget.pos()
            model_width = self.model_widget.width()
            model_height = self.model_widget.height()
            
            # 计算模型底部中心位置
            model_bottom_center_x = model_pos.x() + model_width // 2
            
            # 计算输入框的新位置，使其水平居中于模型底部
            new_input_x = model_bottom_center_x - 490 // 2
            
            # 计算输入框的垂直位置，使其位于模型底部
            new_input_y = model_pos.y() + model_height - 60  # 距离底部60像素
            
            # 设置新的输入框位置
            self.input_container.move(new_input_x, new_input_y)
            
            # 确保输入框容器和输入框在最顶层
            self.input_container.raise_()
            self.input_box.raise_()
        else:
            # 恢复默认高度，但确保不小于30像素
            self.input_container.setFixedHeight(40)  # 从30增加到40
            
            # 恢复输入框高度，但确保不小于30像素
            self.input_box.setFixedHeight(30)  # 从20增加到30
            
            # 恢复窗口大小
            current_width = self.width()
            current_model_height = 600  # 模型区域高度
            self.resize(current_width, current_model_height + 40)  # 模型区域高度加上默认输入框高度
            
            # 更新输入框位置，使其始终保持在模型底部
            model_pos = self.model_widget.pos()
            model_width = self.model_widget.width()
            model_height = self.model_widget.height()
            
            # 计算模型底部中心位置
            model_bottom_center_x = model_pos.x() + model_width // 2
            
            # 计算输入框的新位置，使其水平居中于模型底部
            new_input_x = model_bottom_center_x - 490 // 2
            
            # 计算输入框的垂直位置，使其位于模型底部
            new_input_y = model_pos.y() + model_height - 60  # 距离底部60像素
            
            # 设置新的输入框位置
            self.input_container.move(new_input_x, new_input_y)
            
            # 确保输入框容器和输入框在最顶层
            self.input_container.raise_()
            self.input_box.raise_()
            
    def showEvent(self, event):
        """窗口显示事件"""
        super().showEvent(event)
        
        # 确保输入框容器和输入框在最顶层
        self.input_container.raise_()
        self.input_box.raise_()
        
        # 确保输入框获得焦点
        self.input_box.setFocus()
        
        # 打印调试信息
        # print("窗口显示事件触发")
        # print(f"输入框容器位置: ({self.input_container.x()}, {self.input_container.y()})")
        # print(f"输入框位置: ({self.input_box.x()}, {self.input_box.y()})")
        
    def resizeEvent(self, event):
        """处理窗口大小改变事件"""
        super().resizeEvent(event)
        
        # 只调整模型窗口大小，不改变位置
        self.model_widget.resize(self.width(), 600)
        
        # 调整输入框容器大小，保持宽度为490像素
        current_height = self.input_container.height()
        self.input_container.resize(490, current_height)
        
        # 不更新输入框位置，保持当前位置不变
        # 只更新水平居中的相对位置值，供后续使用
        self.relative_input_x = (self.width() - 490) // 2
        
        # 确保输入框容器和输入框在最顶层
        self.input_container.raise_()
        self.input_box.raise_()
        
    def moveEvent(self, event):
        """处理窗口移动事件"""
        # 当主窗口移动时，同步移动模型窗口和输入框容器
        self.model_widget.move(self.x(), self.y())
        
        # 获取模型窗口的新位置和大小
        model_width = self.model_widget.width()
        model_height = self.model_widget.height()
        
        # 获取当前缩放比例
        scale_factor = self.model_widget.scale_factor
        
        # 计算模型底部中心位置
        model_bottom_center_x = self.x() + model_width // 2
        
        # 计算输入框的新位置，使其水平居中于模型底部
        new_input_x = model_bottom_center_x - 490 // 2
        
        # 计算输入框的垂直位置，使其位于模型底部
        # 根据缩放比例动态调整距离
        base_distance = 60  # 基础距离
        distance = int(base_distance * (1 + (scale_factor - 1) * 0.5))  # 根据缩放比例调整距离
        new_input_y = self.y() + model_height - distance
        
        # 设置新的输入框位置
        self.input_container.move(new_input_x, new_input_y)
        
        # 确保输入框容器和输入框在最顶层
        self.input_container.raise_()
        self.input_box.raise_()
        
        super().moveEvent(event)
        
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        # 关闭模型窗口和输入框容器
        self.model_widget.close()
        self.input_container.close()
        super().closeEvent(event)

    def eventFilter(self, obj, event):
        """事件过滤器，用于处理输入框的事件"""
        if obj == self.input_box:
            if event.type() == event.MouseButtonPress:
                # 确保输入框在最上层
                self.input_box.raise_()
                self.input_box.setFocus()
                # 输出调试信息
                # print("点击成功：输入框被点击")
                # 不阻止事件继续传播
                return False
            elif event.type() == event.FocusIn:
                # 当输入框获得焦点时，确保它可见
                self.input_box.raise_()
                # 输出调试信息
                # print("焦点获取：输入框获得焦点")
                return False
        return super().eventFilter(obj, event)

class ChatWindow(QWidget):
    """聊天窗口类"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # 移除左上角标题
        self.setWindowTitle(" ")
        self.setGeometry(100, 100, 400, 500)  # 初始窗口大小
        # 设置窗口标志，只保留关闭按钮
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint)
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons", "7.png")
        self.setWindowIcon(QIcon(icon_path))
        self.setStyleSheet("""
            QWidget {
                background-color: #cab0f6;  /* 淡紫色背景 */
            }
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
        """)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(5)
        
        # 创建标题栏
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(40)
        self.title_bar.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)
        
        # 创建标题布局
        self.title_layout = QHBoxLayout(self.title_bar)
        self.title_layout.setContentsMargins(5, 0, 5, 0)
        
        # 创建标题标签
        self.title_label = QLabel("聊天框")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #a686dc;
            }
        """)
        
        # 添加标题标签到标题布局
        self.title_layout.addWidget(self.title_label)
        
        # 创建聊天区域
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)
        
        # 添加组件到主布局
        self.main_layout.addWidget(self.title_bar)
        self.main_layout.addWidget(self.chat_area)
        
        # 设置窗口可调整大小
        self.setMinimumSize(300, 400)
        
        # 初始化字体大小
        self.font_size = 14
        
    def add_message(self, sender, message):
        """添加消息到聊天区域"""
        # 格式化消息，设置角色名称颜色为 #514485
        formatted_message = f'<b><span style="color: #514485; font-size: {self.font_size}px;">{sender}：</span></b><span style="font-size: {self.font_size}px;">{message}</span><br>'
        
        # 添加消息
        self.chat_area.append(formatted_message)
        
        # 滚动到底部
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )
        
    def toggle_stay_on_top(self, stay_on_top):
        """切换窗口置顶状态"""
        if stay_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()
        
    def set_font_size(self, size):
        """设置字体大小"""
        self.font_size = size
        # 更新现有消息的字体大小
        current_html = self.chat_area.toHtml()
        updated_html = re.sub(r'font-size: \d+px;', f'font-size: {size}px;', current_html)
        self.chat_area.setHtml(updated_html)

    def closeEvent(self, event):
        """重写关闭事件，使其只隐藏窗口而不是关闭"""
        event.ignore()  # 忽略关闭事件
        self.hide()  # 隐藏窗口

class SpeechBubble(QWidget):
    """对话气泡类"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.Tool | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 添加文字动画相关属性
        self.current_text = ""
        self.target_text = ""
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_text_animation)
        self.characters_per_update = 3  # 每次更新显示的字符数
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(0)
        
        # 创建文本标签
        self.text_label = QLabel()
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 18px;
                padding: 5px;
            }
        """)
        
        # 添加文本标签到布局
        self.main_layout.addWidget(self.text_label)
        
        # 设置默认大小
        self.setFixedSize(100, 50)
        
        # 设置默认文本
        self.set_text("...")
        
    def set_text(self, text):
        """设置气泡文本"""
        self.target_text = text
        self.current_text = ""
        self.animation_timer.start(50)  # 每50毫秒更新一次
        
    def _update_text_animation(self):
        """更新文字动画"""
        if len(self.current_text) < len(self.target_text):
            # 每次显示3-5个字符
            chars_to_add = min(self.characters_per_update, len(self.target_text) - len(self.current_text))
            # 确保target_text是字符串类型
            if isinstance(self.target_text, str):
                self.current_text += self.target_text[len(self.current_text):len(self.current_text) + chars_to_add]
                self.text_label.setText(self.current_text)
                
                # 根据文本长度调整气泡大小
                self._adjust_bubble_size()
            else:
                # 如果target_text不是字符串，转换为字符串
                self.target_text = str(self.target_text)
                self.current_text += self.target_text[len(self.current_text):len(self.current_text) + chars_to_add]
                self.text_label.setText(self.current_text)
                self._adjust_bubble_size()
        else:
            self.animation_timer.stop()
            
    def _adjust_bubble_size(self):
        """根据文本长度调整气泡大小"""
        if self.current_text == "...":
            # 默认小气泡大小
            new_width = 100
            new_height = 50
            
            # 获取当前气泡的中心点
            current_center_x = self.x() + self.width() // 2
            current_center_y = self.y() + self.height() // 2
            
            # 设置新的大小
            self.setFixedSize(new_width, new_height)
            
            # 计算新的位置，使中心点保持不变
            new_x = current_center_x - new_width // 2
            new_y = current_center_y - new_height // 2
            
            # 移动气泡到新位置
            self.move(new_x, new_y)
            
            # 重新计算并更新位置
            if hasattr(self, 'parent') and self.parent():
                model_pos = self.parent().pos()
                model_size = self.parent().size()
                self.update_position(model_pos, model_size)
        else:
            # 计算文本需要的宽度和高度
            font_metrics = self.text_label.fontMetrics()
            text_width = font_metrics.horizontalAdvance(self.current_text)
            
            # 设置气泡大小，留出边距
            width = min(max(text_width + 40, 100), 300)  # 最小100，最大300
            height = 100  # 固定高度为100像素（3行 × 18像素 + 16像素边距）
            
            # 获取当前气泡的中心点
            current_center_x = self.x() + self.width() // 2
            current_center_y = self.y() + self.height() // 2
            
            # 设置新的大小
            self.setFixedSize(width, height)
            
            # 计算新的位置，使中心点保持不变
            new_x = current_center_x - width // 2
            new_y = current_center_y - height // 2
            
            # 移动气泡到新位置
            self.move(new_x, new_y)
            
            # 重新计算并更新位置
            if hasattr(self, 'parent') and self.parent():
                model_pos = self.parent().pos()
                model_size = self.parent().size()
                self.update_position(model_pos, model_size)
                
    def update_position(self, model_pos, model_size):
        """更新气泡位置"""
        # 计算气泡位置，使其位于模型头顶，并向下偏移5像素
        bubble_x = model_pos.x() + model_size.width() // 2 - self.width() // 2
        bubble_y = model_pos.y() - self.height() - 5  # 向下偏移5像素
        
        # 设置气泡位置
        self.move(bubble_x, bubble_y)

    def paintEvent(self, event):
        """绘制气泡形状"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 设置气泡颜色为 #cab0f6
        painter.setBrush(QBrush(QColor(202, 176, 246, 230)))
        # 设置黑色实线边框，宽度为0.3
        painter.setPen(QPen(QColor(0, 0, 0), 0.3))
        
        # 绘制圆角矩形
        rect = self.rect().adjusted(5, 5, -5, -5)
        painter.drawRoundedRect(rect, 10, 10)
        
        # 绘制小三角形
        path = QPainterPath()
        path.moveTo(rect.width() // 2 - 10, rect.height())
        path.lineTo(rect.width() // 2, rect.height() + 10)
        path.lineTo(rect.width() // 2 + 10, rect.height())
        path.closeSubpath()
        painter.drawPath(path) 