from database.config import get_db
from database.crud import DatabaseManager
from database.models import UserRole
import logging

logger = logging.getLogger(__name__)

class AuthManager:
    def __init__(self):
        self.current_user = None
        
    def register(self, username: str, password: str, email: str = None):
        """用户注册"""
        try:
            db = next(get_db())
            db_manager = DatabaseManager(db)
            
            # 检查用户名是否已存在
            if db_manager.get_user(username):
                return {"status": "error", "message": "用户名已存在"}
                
            # 创建新用户
            user = db_manager.create_user(username, password, email)
            return {"status": "success", "user_id": user.id}
            
        except Exception as e:
            logger.error(f"注册失败: {str(e)}")
            return {"status": "error", "message": "注册失败"}
            
    def login(self, username: str, password: str):
        """用户登录"""
        try:
            db = next(get_db())
            db_manager = DatabaseManager(db)
            
            # 获取用户
            user = db_manager.get_user(username)
            if not user:
                return {"status": "error", "message": "用户不存在"}
                
            # 验证密码
            if not db_manager.verify_password(user, password):
                return {"status": "error", "message": "密码错误"}
                
            # 更新最后登录时间
            db_manager.update_last_login(user.id)
            
            # 设置当前用户
            self.current_user = user
            
            return {
                "status": "success",
                "user_id": user.id,
                "username": user.username,
                "role": user.role.value
            }
            
        except Exception as e:
            logger.error(f"登录失败: {str(e)}")
            return {"status": "error", "message": "登录失败"}
            
    def logout(self):
        """用户登出"""
        self.current_user = None
        return {"status": "success"}
        
    def get_current_user(self):
        """获取当前用户"""
        return self.current_user
        
    def is_authenticated(self):
        """检查是否已认证"""
        return self.current_user is not None
        
    def is_admin(self):
        """检查当前用户是否为管理员"""
        if not self.current_user:
            return False
        return self.current_user.role == UserRole.ADMIN
        
    def require_auth(self, func):
        """认证装饰器"""
        def wrapper(*args, **kwargs):
            if not self.is_authenticated():
                return {"status": "error", "message": "需要登录"}
            return func(*args, **kwargs)
        return wrapper
        
    def require_admin(self, func):
        """管理员权限装饰器"""
        def wrapper(*args, **kwargs):
            if not self.is_admin():
                return {"status": "error", "message": "需要管理员权限"}
            return func(*args, **kwargs)
        return wrapper 