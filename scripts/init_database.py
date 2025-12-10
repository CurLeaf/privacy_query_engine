"""
数据库初始化脚本
-----------------
用于创建 privacy 数据库和测试表。

用法说明:
    1. 根据需要修改数据库配置（host、port、user、password）。
    2. 运行脚本初始化数据库:
        python scripts/init_database.py

    若要使用不同的数据库名称或配置，可根据实际需求调整脚本内容。
"""
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "123456",  # 修改为你的 PostgreSQL 密码
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
        cursor.execute(f'CREATE DATABASE "{DATABASE_NAME}"')
        print(f"✓ 数据库 '{DATABASE_NAME}' 创建成功")
    
    cursor.close()
    conn.close()


def create_tables():
    """创建测试表"""
    print(f"\n正在连接数据库 '{DATABASE_NAME}'...")
    
    conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DATABASE_NAME
    )
    cursor = conn.cursor()
    
    # 创建 users 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            age INTEGER,
            phone VARCHAR(20)
        )
    """)
    print("✓ 表 'users' 创建成功")
    
    # 创建 orders 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            amount DECIMAL(10, 2),
            status VARCHAR(50)
        )
    """)
    print("✓ 表 'orders' 创建成功")
    
    conn.commit()
    cursor.close()
    conn.close()


def insert_mock_data():
    """插入模拟数据"""
    print(f"\n正在插入模拟数据...")
    
    conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DATABASE_NAME
    )
    cursor = conn.cursor()
    
    # 清空现有数据
    cursor.execute("TRUNCATE orders, users RESTART IDENTITY CASCADE")
    
    # 插入 users 数据
    users_data = [
        ("张三", "zhangsan@example.com", 28, "13812345678"),
        ("李四", "lisi@example.com", 35, "13987654321"),
        ("王五", "wangwu@example.com", 42, "13611112222"),
        ("John Doe", "john@example.com", 30, "13522223333"),
        ("Jane Smith", "jane@example.com", 25, "13633334444"),
    ]
    
    cursor.executemany(
        "INSERT INTO users (name, email, age, phone) VALUES (%s, %s, %s, %s)",
        users_data
    )
    print(f"✓ 插入 {len(users_data)} 条 users 数据")
    
    # 插入 orders 数据
    orders_data = [
        (1, 100.0, "completed"),
        (2, 250.5, "pending"),
        (1, 75.0, "completed"),
    ]
    
    cursor.executemany(
        "INSERT INTO orders (user_id, amount, status) VALUES (%s, %s, %s)",
        orders_data
    )
    print(f"✓ 插入 {len(orders_data)} 条 orders 数据")
    
    conn.commit()
    cursor.close()
    conn.close()


def verify_data():
    """验证数据"""
    print(f"\n正在验证数据...")
    
    conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DATABASE_NAME
    )
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    users_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM orders")
    orders_count = cursor.fetchone()[0]
    
    print(f"✓ users 表: {users_count} 条记录")
    print(f"✓ orders 表: {orders_count} 条记录")
    
    cursor.close()
    conn.close()


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


def main():
    """主函数"""
    print("=" * 50)
    print("Privacy Query Engine - 数据库初始化脚本")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        drop_database()
        return
    
    try:
        create_database()
        create_tables()
        insert_mock_data()
        verify_data()
        
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
        sys.exit(1)


if __name__ == "__main__":
    main()

