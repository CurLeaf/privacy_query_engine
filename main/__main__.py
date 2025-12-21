"""
Privacy Query Engine - CLI 入口

使用方式:
    python -m main --help
    python -m main query "SELECT COUNT(*) FROM users"
    python -m main process data.csv --output protected.csv
"""
from typing import Optional
import typer
from rich.console import Console

from . import __version__

app = typer.Typer(
    name="privacy-query-engine",
    help="差分隐私与去标识化查询引擎",
    add_completion=False,
)
console = Console()


def version_callback(print_version: bool) -> None:
    """打印版本号"""
    if print_version:
        console.print(f"[yellow]privacy-query-engine[/] version: [bold blue]{__version__}[/]")
        raise typer.Exit()


@app.command()
def query(
    sql: str = typer.Argument(..., help="SQL 查询语句"),
    mock: bool = typer.Option(True, "--mock/--no-mock", help="使用 Mock 模式"),
):
    """执行隐私保护查询"""
    from . import QueryDriver
    
    driver = QueryDriver(use_mock=mock)
    result = driver.process_query(sql)
    
    console.print("[green]查询结果:[/]")
    console.print(result)


@app.command()
def process(
    input_file: str = typer.Argument(..., help="输入 CSV 文件路径"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出文件路径"),
    k: int = typer.Option(5, "--k", help="K-匿名化参数"),
):
    """处理 CSV 文件并应用隐私保护"""
    from .data import CSVPrivacyProcessor
    from .data.csv_processor import ProcessingConfig
    
    processor = CSVPrivacyProcessor()
    config = ProcessingConfig(auto_detect=True, k_anonymity=k)
    
    result = processor.process_file(input_file, config)
    
    if result.success:
        console.print(f"[green]处理成功![/] 处理了 {result.processed_row_count} 行")
        console.print(f"脱敏列: {result.columns_processed}")
        
        if output:
            processor.save_csv(result.data, output)
            console.print(f"[green]已保存到:[/] {output}")
    else:
        console.print(f"[red]处理失败:[/] {result.error}")


@app.callback()
def main(
    version: bool = typer.Option(
        None, "-v", "--version",
        callback=version_callback,
        is_eager=True,
        help="显示版本号",
    ),
):
    """Privacy Query Engine - 差分隐私与去标识化查询引擎"""
    pass


if __name__ == "__main__":
    app()
