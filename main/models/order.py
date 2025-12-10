"""
Order 订单模型
"""
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from sqlmodel import SQLModel, Field, Relationship


if TYPE_CHECKING:
    from .user import User


class OrderBase(SQLModel):
    """订单基础模型 - 共享字段"""
    user_id: int = Field(foreign_key="users.id", description="用户ID")
    amount: Decimal = Field(default=0, max_digits=10, decimal_places=2, description="订单金额")
    status: str = Field(default="pending", max_length=50, description="订单状态")


class Order(OrderBase, table=True):
    """订单表模型"""
    __tablename__ = "orders"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 关联用户
    user: Optional["User"] = Relationship(back_populates="orders")


class OrderCreate(OrderBase):
    """创建订单的请求模型"""
    pass


class OrderRead(OrderBase):
    """读取订单的响应模型"""
    id: int


class OrderUpdate(SQLModel):
    """更新订单的请求模型 - 所有字段可选"""
    user_id: Optional[int] = None
    amount: Optional[Decimal] = None
    status: Optional[str] = None


