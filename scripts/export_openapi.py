#!/usr/bin/env python3
"""
导出 OpenAPI 规范的命令行工具

使用方法:
    python scripts/export_openapi.py --format json --output openapi.json
    python scripts/export_openapi.py --format yaml --output openapi.yaml
    python scripts/export_openapi.py --format both --output openapi
"""
import argparse
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from main.api.server import app
from main.api.export import OpenAPIExporter, OpenAPIExportError


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="导出 Privacy Query Engine 的 OpenAPI 规范"
    )
    
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "yaml", "both"],
        default="json",
        help="导出格式 (默认: json)"
    )
    
    parser.add_argument(
        "--output",
        "-o",
        default="openapi",
        help="输出文件路径（不含扩展名，如果 format=both）"
    )
    
    parser.add_argument(
        "--indent",
        "-i",
        type=int,
        default=2,
        help="JSON 缩进空格数 (默认: 2)"
    )
    
    args = parser.parse_args()
    
    try:
        exporter = OpenAPIExporter(app)
        
        print(f"📝 正在导出 OpenAPI 规范...")
        print(f"   格式: {args.format}")
        print(f"   输出: {args.output}")
        print()
        
        if args.format == "json":
            output_path = args.output if args.output.endswith(".json") else f"{args.output}.json"
            exporter.export_json(output_path, indent=args.indent)
        
        elif args.format == "yaml":
            output_path = args.output if args.output.endswith(".yaml") else f"{args.output}.yaml"
            exporter.export_yaml(output_path)
        
        elif args.format == "both":
            base_path = args.output.replace(".json", "").replace(".yaml", "")
            exporter.export_both(base_path)
        
        print()
        print("✅ 导出成功！")
        print()
        print("📖 使用导出的规范:")
        print("   - 导入到 Postman: File > Import > 选择文件")
        print("   - 导入到 Insomnia: Application > Preferences > Data > Import Data")
        print("   - 生成客户端: openapi-generator-cli generate -i openapi.json -g python")
        
    except OpenAPIExportError as e:
        print(f"❌ 导出失败: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 未知错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
