from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea, QSizePolicy, QMenu, QAction, QInputDialog
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QRectF
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QPen, QBrush
import logging

logger = logging.getLogger(__name__)

class ChatBubble(QLabel):
    """聊天气泡控件"""
    def __init__(self, text, is_user=True, parent=None):
        super().__init__(parent)
        self.text = text
        self.is_user = is_user
        self.padding = 10
        self.border_radius = 15
        self.initUI()

    def initUI(self):
        # 设置文本
        self.setText(self.text)
        # 允许自动换行
        self.setWordWrap(True)
        # 设置最小宽度和最大宽度
        self.setMinimumWidth(280)
        self.setMaximumWidth(280)
        # 设置大小策略
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        # 设置样式
        self.setStyleSheet("""
            QLabel {
                color: black;
                padding: 10px;
            }
        """)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 创建气泡路径
        path = QPainterPath()
        rect = QRectF(self.rect())  # 将QRect转换为QRectF
        path.addRoundedRect(rect, self.border_radius, self.border_radius)

        # 设置气泡颜色
        if self.is_user:
            painter.fillPath(path, QColor(255, 255, 255))  # 白色气泡
        else:
            painter.fillPath(path, QColor(149, 236, 105))  # 绿色气泡

        # 绘制文本
        super().paintEvent(event)

class ChatWindowWidget(QWidget):
    """聊天窗口控件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.Tool | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.initUI()

        # 聊天框属性
        self.chat_area = {
            'x': 0,
            'y': 0,
            'width': 300,
            'height': 400
        }
        self.show_chat_area = False

    def initUI(self):
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)

        # 创建滚动区域
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)

        # 创建消息容器
        self.message_container = QWidget()
        self.message_container.setStyleSheet("background: transparent;")
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setAlignment(Qt.AlignTop)
        self.message_layout.setSpacing(10)
        self.message_layout.setContentsMargins(10, 10, 10, 10)

        # 设置滚动区域的窗口部件
        self.scroll_area.setWidget(self.message_container)
        self.main_layout.addWidget(self.scroll_area)

    def add_message(self, text, is_user=True):
        """添加新消息"""
        bubble = ChatBubble(text, is_user)
        if is_user:
            self.message_layout.setAlignment(Qt.AlignLeft)
        else:
            self.message_layout.setAlignment(Qt.AlignRight)
        self.message_layout.addWidget(bubble)
        # 滚动到底部
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def paintEvent(self, event):
        """绘制事件"""
        if self.show_chat_area:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # 设置虚线笔
            pen = QPen(QColor(255, 0, 0))
            pen.setStyle(Qt.DashLine)
            pen.setWidth(2)
            painter.setPen(pen)

            # 绘制矩形
            painter.drawRect(
                self.chat_area['x'],
                self.chat_area['y'],
                self.chat_area['width'],
                self.chat_area['height']
            )

    def set_chat_area_width(self, width):
        """设置聊天区域宽度"""
        self.chat_area['width'] = width
        self.update()

    def set_chat_area_height(self, height):
        """设置聊天区域高度"""
        self.chat_area['height'] = height
        self.update()

    def toggle_chat_area_visibility(self):
        """切换聊天区域显示状态"""
        self.show_chat_area = not self.show_chat_area
        self.update()

    def mousePressEvent(self, event):
        """鼠标按下事件，实现点击穿透"""
        event.ignore()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件，实现点击穿透"""
        event.ignore()

    def mouseMoveEvent(self, event):
        """鼠标移动事件，实现点击穿透"""
        event.ignore() 