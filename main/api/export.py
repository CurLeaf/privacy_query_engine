"""
OpenAPI 导出工具

提供将 OpenAPI 规范导出为 JSON 和 YAML 格式的功能
"""
import json
import yaml
from typing import Dict, Any
from pathlib import Path

from fastapi import FastAPI


class OpenAPIExportError(Exception):
    """OpenAPI 导出错误"""
    pass


class OpenAPIExporter:
    """
    OpenAPI 规范导出工具
    
    支持导出为 JSON 和 YAML 格式
    """
    
    def __init__(self, app: FastAPI):
        """
        初始化导出器
        
        Args:
            app: FastAPI 应用实例
        """
        self.app = app
    
    def get_schema(self) -> Dict[str, Any]:
        """
        获取 OpenAPI schema 字典
        
        Returns:
            OpenAPI schema 字典
        """
        return self.app.openapi()
    
    def export_json(self, output_path: str, indent: int = 2) -> None:
        """
        导出为 JSON 格式
        
        Args:
            output_path: 输出文件路径
            indent: JSON 缩进空格数（默认 2）
        
        Raises:
            OpenAPIExportError: 导出失败时抛出
        """
        try:
            schema = self.get_schema()
            output_file = Path(output_path)
            
            # 确保目录存在
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入 JSON 文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(schema, f, indent=indent, ensure_ascii=False)
            
            print(f"✅ OpenAPI 规范已导出到: {output_path}")
            
        except PermissionError as e:
            raise OpenAPIExportError(f"无法写入文件 {output_path}: 权限不足") from e
        except Exception as e:
            raise OpenAPIExportError(f"导出 JSON 失败: {str(e)}") from e
    
    def export_yaml(self, output_path: str) -> None:
        """
        导出为 YAML 格式
        
        Args:
            output_path: 输出文件路径
        
        Raises:
            OpenAPIExportError: 导出失败时抛出
        """
        try:
            schema = self.get_schema()
            output_file = Path(output_path)
            
            # 确保目录存在
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入 YAML 文件
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(
                    schema,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False
                )
            
            print(f"✅ OpenAPI 规范已导出到: {output_path}")
            
        except PermissionError as e:
            raise OpenAPIExportError(f"无法写入文件 {output_path}: 权限不足") from e
        except Exception as e:
            raise OpenAPIExportError(f"导出 YAML 失败: {str(e)}") from e
    
    def export_both(self, base_path: str = "openapi") -> None:
        """
        同时导出 JSON 和 YAML 格式
        
        Args:
            base_path: 基础文件路径（不含扩展名）
        """
        self.export_json(f"{base_path}.json")
        self.export_yaml(f"{base_path}.yaml")


def export_openapi_spec(
    app: FastAPI,
    format: str = "json",
    output_path: str = "openapi.json"
) -> None:
    """
    便捷函数：导出 OpenAPI 规范
    
    Args:
        app: FastAPI 应用实例
        format: 导出格式 ("json" 或 "yaml")
        output_path: 输出文件路径
    
    Raises:
        ValueError: 格式不支持时抛出
        OpenAPIExportError: 导出失败时抛出
    """
    exporter = OpenAPIExporter(app)
    
    if format.lower() == "json":
        exporter.export_json(output_path)
    elif format.lower() == "yaml":
        exporter.export_yaml(output_path)
    else:
        raise ValueError(f"不支持的格式: {format}。请使用 'json' 或 'yaml'")


if __name__ == "__main__":
    # 示例用法
    from .server import app
    
    print("导出 OpenAPI 规范...")
    exporter = OpenAPIExporter(app)
    exporter.export_both("openapi")
    print("✅ 导出完成！")
