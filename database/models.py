from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from .config import Base
import datetime
import enum

class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    email = Column(String, unique=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # 关系
    settings = relationship("UserSettings", back_populates="user", uselist=False)
    voice_history = relationship("VoiceHistory", back_populates="user")

class UserSettings(Base):
    __tablename__ = 'user_settings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    wake_word = Column(String, default='你好助手')
    voice_speed = Column(Float, default=1.0)
    voice_type = Column(String, default='default')
    
    user = relationship("User", back_populates="settings")

class VoiceHistory(Base):
    __tablename__ = 'voice_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    command_text = Column(String, nullable=False)
    response_text = Column(String)
    execution_time = Column(DateTime, default=datetime.datetime.utcnow)
    success = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="voice_history") 