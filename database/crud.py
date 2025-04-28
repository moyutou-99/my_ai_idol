from sqlalchemy.orm import Session
from . import models
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

class DatabaseManager:
    def __init__(self, db: Session):
        self.db = db
        
    def create_user(self, username: str, password: str, email: str = None, role: models.UserRole = models.UserRole.USER):
        """创建新用户"""
        hashed_password = generate_password_hash(password)
        db_user = models.User(
            username=username,
            password_hash=hashed_password,
            email=email,
            role=role
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
        
    def get_user(self, username: str):
        """获取用户信息"""
        return self.db.query(models.User).filter(models.User.username == username).first()
        
    def get_user_by_id(self, user_id: int):
        """通过ID获取用户信息"""
        return self.db.query(models.User).filter(models.User.id == user_id).first()
        
    def verify_password(self, user: models.User, password: str):
        """验证密码"""
        return check_password_hash(user.password_hash, password)
        
    def update_user(self, user_id: int, **kwargs):
        """更新用户信息"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
            
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
                
        self.db.commit()
        return user
        
    def delete_user(self, user_id: int):
        """删除用户"""
        user = self.get_user_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
            return True
        return False
        
    def update_last_login(self, user_id: int):
        """更新最后登录时间"""
        user = self.get_user_by_id(user_id)
        if user:
            user.last_login = datetime.datetime.utcnow()
            self.db.commit()
            return True
        return False
        
    def is_admin(self, user_id: int):
        """检查用户是否为管理员"""
        user = self.get_user_by_id(user_id)
        return user and user.role == models.UserRole.ADMIN
        
    def get_all_users(self):
        """获取所有用户"""
        return self.db.query(models.User).all()
        
    def update_user_settings(self, user_id: int, **settings):
        """更新用户设置"""
        user_settings = self.db.query(models.UserSettings).filter(
            models.UserSettings.user_id == user_id
        ).first()
        
        if not user_settings:
            user_settings = models.UserSettings(user_id=user_id)
            self.db.add(user_settings)
            
        for key, value in settings.items():
            if hasattr(user_settings, key):
                setattr(user_settings, key, value)
                
        self.db.commit()
        return user_settings 