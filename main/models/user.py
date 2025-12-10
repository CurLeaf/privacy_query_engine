"""
User 用户模型
"""
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship


if TYPE_CHECKING:
    from .order import Order


class UserBase(SQLModel):
    """用户基础模型 - 共享字段"""
    name: str = Field(max_length=100, description="用户姓名")
    email: str = Field(max_length=255, unique=True, index=True, description="邮箱地址")
    age: Optional[int] = Field(default=None, ge=0, le=150, description="年龄")
    phone: Optional[str] = Field(default=None, max_length=20, description="手机号码")


class User(UserBase, table=True):
    """用户表模型"""
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 关联订单
    orders: List["Order"] = Relationship(back_populates="user")


class UserCreate(UserBase):
    """创建用户的请求模型"""
    pass


class UserRead(UserBase):
    """读取用户的响应模型"""
    id: int


class UserUpdate(SQLModel):
    """更新用户的请求模型 - 所有字段可选"""
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None

