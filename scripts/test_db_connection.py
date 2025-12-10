#!/usr/bin/env python
"""
PostgreSQL 数据库连接测试脚本

使用方法:
    1. 设置环境变量:
        set PG_HOST=localhost
        set PG_PORT=5432
        set PG_DATABASE=mydb
        set PG_USER=postgres
        set PG_PASSWORD=your_password
    
    2. 运行脚本:
        python scripts/test_db_connection.py
    
    或直接传入参数:
        python scripts/test_db_connection.py --host localhost --port 5432 --database mydb --user postgres --password xxx
"""
import argparse
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main.executor.database import DatabaseConnection


def test_connection(
    host: str = None,
    port: int = None,
    database: str = None,
    user: str = None,
    password: str = None,
):
    """测试数据库连接"""
    print("=" * 60)
    print("🔌 PostgreSQL 连接测试")
    print("=" * 60)
    
    # 创建连接
    db = DatabaseConnection(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        echo=False,
    )
    
    print(f"\n📡 连接配置:")
    print(f"   Host:     {db.config.host}")
    print(f"   Port:     {db.config.port}")
    print(f"   Database: {db.config.database}")
    print(f"   User:     {db.config.user}")
    
    # 测试连接
    print(f"\n🔍 测试连接中...")
    result = db.test_connection()
    
    if result["status"] == "connected":
        print(f"\n✅ 连接成功!")
        print(f"   数据库:   {result['database']}")
        print(f"   用户:     {result['user']}")
        print(f"   版本:     {result['version']}")
        
        # 获取表列表
        print(f"\n📋 数据库表列表:")
        tables = db.get_tables()
        if tables:
            for i, table in enumerate(tables, 1):
                print(f"   {i}. {table}")
        else:
            print("   (无表)")
        
        # 执行示例查询
        print(f"\n🧪 执行测试查询:")
        try:
            # 测试 COUNT 查询
            count = db.execute_scalar("SELECT COUNT(*) FROM information_schema.tables;")
            print(f"   information_schema.tables 行数: {count}")
        except Exception as e:
            print(f"   查询失败: {e}")
        
        db.close()
        return True
    else:
        print(f"\n❌ 连接失败!")
        print(f"   错误: {result.get('error', '未知错误')}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="PostgreSQL 数据库连接测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python scripts/test_db_connection.py
    python scripts/test_db_connection.py --host 192.168.1.100 --database mydb
    python scripts/test_db_connection.py -H localhost -p 5432 -d postgres -u admin -P secret
        """
    )
    
    parser.add_argument("-H", "--host", help="数据库主机 (默认: PG_HOST 环境变量或 localhost)")
    parser.add_argument("-p", "--port", type=int, help="端口号 (默认: PG_PORT 环境变量或 5432)")
    parser.add_argument("-d", "--database", help="数据库名 (默认: PG_DATABASE 环境变量或 postgres)")
    parser.add_argument("-u", "--user", help="用户名 (默认: PG_USER 环境变量或 postgres)")
    parser.add_argument("-P", "--password", help="密码 (默认: PG_PASSWORD 环境变量)")
    
    args = parser.parse_args()
    
    success = test_connection(
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
        password=args.password,
    )
    
    print("\n" + "=" * 60)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()


