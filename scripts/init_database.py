"""
数据库初始化脚本 (SQLModel ORM 版本)
创建 privacy 数据库和测试表

使用方法:
    1. 可通过命令行参数管理数据库:
        python scripts/init_database.py           初始化数据库和测试数据
        python scripts/init_database.py --drop    删除数据库
        python scripts/init_database.py --reset   重置表并重新插入数据
        python scripts/init_database.py --help    显示帮助信息

    2. 支持环境变量配置数据库连接:
        设置以下环境变量（可选，若未设置则使用脚本内默认配置）:
            export PG_HOST=localhost
            export PG_PORT=5432
            export PG_DATABASE=privacy
            export PG_USER=postgres
            export PG_PASSWORD=your_password

        也可直接修改脚本中的 DB_CONFIG 变量中的参数
"""
import sys
import os
from decimal import Decimal

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main.executor.database import DatabaseConnection
from main.models import User, Order

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "123456",  # 修改为你的 PostgreSQL 密码，或通过环境变量设置
}

DATABASE_NAME = "privacy"


def create_database():
    """创建 privacy 数据库"""
    print(f"正在连接 PostgreSQL 服务器...")
    
    # 连接到默认的 postgres 数据库
    conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # 检查数据库是否存在
    cursor.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (DATABASE_NAME,)
    )
    exists = cursor.fetchone()
    
    if exists:
        print(f"数据库 '{DATABASE_NAME}' 已存在")
    else:
        cursor.execute(f'DROP DATABASE IF EXISTS "{DATABASE_NAME}"')  # 清空数据库: 先删后建
        cursor.execute(f'CREATE DATABASE "{DATABASE_NAME}"')
        print(f"✓ 数据库 '{DATABASE_NAME}' 创建成功")
    
    cursor.close()
    conn.close()


def create_tables_orm():
    """使用 SQLModel ORM 创建表"""
    print(f"\n正在使用 ORM 创建表...")
    
    db = DatabaseConnection(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DATABASE_NAME,
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )
    
    # 创建所有 SQLModel 定义的表
    db.create_tables()
    print("✓ 表创建成功 (users, orders)")
    
    db.close()


def insert_mock_data_orm():
    """使用 ORM 插入模拟数据"""
    print(f"\n正在使用 ORM 插入模拟数据...")
    
    db = DatabaseConnection(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DATABASE_NAME,
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )
    
    # 先清空数据 (使用原始 SQL)
    db.execute("TRUNCATE orders, users RESTART IDENTITY CASCADE")
    
    # 创建用户数据
    users_data = [
        User(name="张三", email="zhangsan@example.com", age=28, phone="13812345678"),
        User(name="李四", email="lisi@example.com", age=35, phone="13987654321"),
        User(name="王五", email="wangwu@example.com", age=42, phone="13611112222"),
        User(name="John Doe", email="john@example.com", age=30, phone="13522223333"),
        User(name="Jane Smith", email="jane@example.com", age=25, phone="13633334444"),
    ]
    
    # 使用 session 添加用户
    with db.get_session() as session:
        for user in users_data:
            session.add(user)
        session.commit()
        
        # 刷新获取 ID
        for user in users_data:
            session.refresh(user)
    
    print(f"✓ 插入 {len(users_data)} 条 users 数据")
    
    # 创建订单数据
    orders_data = [
        Order(user_id=1, amount=Decimal("100.00"), status="completed"),
        Order(user_id=2, amount=Decimal("250.50"), status="pending"),
        Order(user_id=1, amount=Decimal("75.00"), status="completed"),
    ]
    
    with db.get_session() as session:
        for order in orders_data:
            session.add(order)
    
    print(f"✓ 插入 {len(orders_data)} 条 orders 数据")
    
    db.close()


def verify_data_orm():
    """使用 ORM 验证数据"""
    print(f"\n正在验证数据...")
    
    db = DatabaseConnection(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DATABASE_NAME,
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )
    
    # 使用 ORM 方法统计
    users_count = db.count(User)
    orders_count = db.count(Order)
    
    print(f"✓ users 表: {users_count} 条记录")
    print(f"✓ orders 表: {orders_count} 条记录")
    
    # 显示用户列表
    print(f"\n📋 用户列表:")
    users = db.get_all(User)
    for user in users:
        print(f"   {user.id}. {user.name} ({user.email})")
    
    # 显示订单列表
    print(f"\n📋 订单列表:")
    orders = db.get_all(Order)
    for order in orders:
        print(f"   {order.id}. 用户ID:{order.user_id}, 金额:{order.amount}, 状态:{order.status}")
    
    db.close()


def drop_database():
    """删除数据库（谨慎使用）"""
    print(f"\n正在删除数据库 '{DATABASE_NAME}'...")
    
    conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # 断开所有连接
    cursor.execute(f"""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '{DATABASE_NAME}'
        AND pid <> pg_backend_pid()
    """)
    
    cursor.execute(f'DROP DATABASE IF EXISTS "{DATABASE_NAME}"')
    print(f"✓ 数据库 '{DATABASE_NAME}' 已删除")
    
    cursor.close()
    conn.close()


def reset_tables():
    """重置表（删除并重建）"""
    print(f"\n正在重置表...")
    
    db = DatabaseConnection(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DATABASE_NAME,
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )
    
    db.drop_tables()
    print("✓ 表已删除")
    
    db.create_tables()
    print("✓ 表已重建")
    
    db.close()


def main():
    """主函数"""
    print("=" * 50)
    print("Privacy Query Engine - 数据库初始化脚本 (ORM)")
    print("=" * 50)

    if len(sys.argv) > 1:
        if sys.argv[1] == "--drop":
            drop_database()
            return
        elif sys.argv[1] == "--reset":
            reset_tables()
            insert_mock_data_orm()
            verify_data_orm()
            return
        elif sys.argv[1] == "--help":
            print("""
用法:
    python scripts/init_database.py           初始化数据库和数据
    python scripts/init_database.py --drop    删除数据库
    python scripts/init_database.py --reset   重置表并重新插入数据
    python scripts/init_database.py --help    显示帮助信息

支持环境变量配置（例如 Linux/Mac）:
    export PG_HOST=localhost
    export PG_PORT=5432
    export PG_DATABASE=privacy
    export PG_USER=postgres
    export PG_PASSWORD=your_password

如未设置环境变量，将使用脚本内 DB_CONFIG 的默认配置。
            """)
            return

    try:
        # 初始化之前需要清空数据库
        drop_database()
        create_database()
        create_tables_orm()
        insert_mock_data_orm()
        verify_data_orm()
        
        print("\n" + "=" * 50)
        print("✓ 数据库初始化完成!")
        print("=" * 50)
        print(f"\n连接信息:")
        print(f"  Host: {DB_CONFIG['host']}")
        print(f"  Port: {DB_CONFIG['port']}")
        print(f"  Database: {DATABASE_NAME}")
        print(f"  User: {DB_CONFIG['user']}")
        
    except psycopg2.Error as e:
        print(f"\n✗ 数据库错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
