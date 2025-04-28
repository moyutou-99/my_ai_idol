from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QMessageBox, QDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QFont
from .auth_manager import AuthManager
import os

class LoginDialog(QDialog):
    login_success = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_manager = AuthManager()
        # 隐藏默认帮助按钮
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               'assets', 'icons', '9.png')
        self.setWindowIcon(QIcon(icon_path))
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('登录')
        self.setFixedSize(350, 250)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                font-size: 14px;
                color: #333;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton {
                padding: 8px 16px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title_label = QLabel('用户登录')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        layout.addWidget(title_label)
        
        # 用户名输入
        username_layout = QHBoxLayout()
        username_label = QLabel('用户名:')
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('请输入用户名')
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        
        # 密码输入
        password_layout = QHBoxLayout()
        password_label = QLabel('密码:')
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText('请输入密码')
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.login_button = QPushButton('登录')
        self.login_button.setIcon(QIcon.fromTheme('system-login'))
        self.register_button = QPushButton('注册')
        self.register_button.setIcon(QIcon.fromTheme('contact-new'))
        self.help_button = QPushButton('帮助')
        self.help_button.setIcon(QIcon.fromTheme('help-about'))
        
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.register_button)
        button_layout.addWidget(self.help_button)
        
        # 添加所有布局
        layout.addLayout(username_layout)
        layout.addLayout(password_layout)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 连接信号
        self.login_button.clicked.connect(self.handle_login)
        self.register_button.clicked.connect(self.handle_register)
        self.help_button.clicked.connect(self.show_help)
        
    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, '错误', '请输入用户名和密码')
            return
            
        result = self.auth_manager.login(username, password)
        if result['status'] == 'success':
            self.login_success.emit(result)
            self.accept()
        else:
            QMessageBox.warning(self, '错误', result['message'])
            
    def handle_register(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, '错误', '请输入用户名和密码')
            return
            
        result = self.auth_manager.register(username, password)
        if result['status'] == 'success':
            QMessageBox.information(self, '成功', '注册成功，请登录')
        else:
            QMessageBox.warning(self, '错误', result['message'])
            
    def show_help(self):
        QMessageBox.information(self, '帮助', 
            '如果没有账号请先注册。\n'
            '用户名和密码没有长度和特殊字符限制。\n'
            '如有必要后续会进行对应调整。'
        )

class UserProfileWidget(QWidget):
    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 用户信息显示
        self.user_info_label = QLabel()
        self.update_user_info()
        
        # 登出按钮
        self.logout_button = QPushButton('登出')
        self.logout_button.clicked.connect(self.handle_logout)
        
        layout.addWidget(self.user_info_label)
        layout.addWidget(self.logout_button)
        
        self.setLayout(layout)
        
    def update_user_info(self):
        user = self.auth_manager.get_current_user()
        if user:
            info = f"用户名: {user.username}\n"
            info += f"角色: {user.role.value}\n"
            info += f"最后登录: {user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '从未登录'}"
            self.user_info_label.setText(info)
        else:
            self.user_info_label.setText("未登录")
            
    def handle_logout(self):
        self.auth_manager.logout()
        self.update_user_info()
        QMessageBox.information(self, '成功', '已登出') 