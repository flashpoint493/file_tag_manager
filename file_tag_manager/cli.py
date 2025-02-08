"""命令行接口"""
import os
import click
from typing import List
from .core import FileManager, TagManager
import json

class Context:
    def __init__(self):
        """初始化 CLI 上下文"""
        self.file_manager = None
        self.tag_manager = None

pass_context = click.make_pass_decorator(Context, ensure=True)

@click.group()
@click.pass_context
def cli(ctx):
    """文件标签管理工具"""
    ctx.obj = Context()

def _get_file_manager(ctx: Context, config_dir: str = None) -> FileManager:
    """从配置文件获取 FileManager 实例"""
    if ctx.obj.file_manager:
        return ctx.obj.file_manager

    storage_path = os.path.join(config_dir if config_dir else os.path.expanduser("~/.file_tag_manager"), "files.json")
    if os.path.exists(storage_path):
        with open(storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            root_dir = data.get('root_dir', '.')
    else:
        root_dir = '.'

    ctx.obj.file_manager = FileManager(root_dir, config_dir=config_dir)
    return ctx.obj.file_manager

def _get_tag_manager(ctx: Context, config_dir: str = None) -> TagManager:
    """从配置文件获取 TagManager 实例"""
    if ctx.obj.tag_manager:
        return ctx.obj.tag_manager

    ctx.obj.tag_manager = TagManager(config_dir=config_dir)
    return ctx.obj.tag_manager

@cli.command()
@click.argument('directory')
@click.option('--patterns', '-p', multiple=True, help='''要监控的文件模式，支持以下格式：
1. 扩展名模式：
   - .py 或 py：匹配所有 Python 文件
   - .txt 或 txt：匹配所有文本文件

2. 路径模式：
   - src/*：匹配 src 目录下的所有文件
   - !temp/*：排除 temp 目录下的所有文件
   - docs/api/*：匹配 docs/api 目录下的所有文件
   - /src/*.py：从项目根目录开始匹配
   - !!docs/api/*：重新包含已排除目录中的特定子目录

多个模式可以多次使用此选项''')
@click.option('--recursive/--no-recursive', default=True, help='是否递归监控子目录')
@click.option('--config-dir', help='配置文件目录，默认为 ~/.file_tag_manager')
@click.pass_context
def init(ctx: Context, directory: str, patterns: List[str], recursive: bool, config_dir: str):
    """初始化文件监控。

    支持两种模式格式：
    1. 扩展名模式：
       - .py 或 py：匹配所有 Python 文件
       - .txt 或 txt：匹配所有文本文件

    2. 路径模式：
       - src/*：匹配 src 目录下的所有文件
       - !temp/*：排除 temp 目录下的所有文件
       - docs/api/*：匹配 docs/api 目录下的所有文件
       - /src/*.py：从项目根目录开始匹配
       - !!docs/api/*：重新包含已排除目录中的特定子目录
    """
    directory = os.path.abspath(directory)
    if not os.path.exists(directory):
        click.echo(f"目录不存在: {directory}")
        return

    # 分离包含模式和排除模式
    include_patterns = []
    exclude_patterns = []
    
    def _process_pattern(pattern: str) -> str:
        """处理文件模式，统一格式"""
        pattern = pattern.strip().replace('\\', '/')
        
        # 处理扩展名模式
        if not ('/' in pattern or '*' in pattern or '!' in pattern):
            # 如果是纯扩展名，添加 *. 前缀
            return f"*.{pattern.lstrip('.')}"
        
        # 处理目录模式
        if pattern.endswith('/'):
            return f"{pattern}*"
        
        return pattern
    
    if patterns:
        for pattern in patterns:
            pattern = pattern.strip()
            if pattern.startswith('!!'):
                # 重新包含模式（添加到包含模式列表）
                include_patterns.append(pattern)  # 保留 !!
            elif pattern.startswith('!'):
                # 排除模式
                exclude_patterns.append(_process_pattern(pattern))  # 保留 !
            else:
                # 包含模式
                include_patterns.append(_process_pattern(pattern))
    else:
        include_patterns = ["*"]

    ctx.obj.file_manager = FileManager(
        directory,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        recursive=recursive,
        config_dir=config_dir
    )
    ctx.obj.tag_manager = TagManager(config_dir=config_dir)

    click.echo(f"开始监控目录: {directory}")
    if include_patterns:
        click.echo("包含模式:")
        for pattern in include_patterns:
            click.echo(f"  - {pattern}")
    if exclude_patterns:
        click.echo("排除模式:")
        for pattern in exclude_patterns:
            click.echo(f"  - {pattern}")
    click.echo(f"递归监控子目录: {recursive}")

@cli.command()
@click.pass_context
@click.option('--config-dir', help='配置文件目录，默认为 ~/.file_tag_manager')
def list_patterns(ctx: Context, config_dir: str):
    """列出当前的文件模式。
    
    包括：
    1. 文件包含模式：用于指定要监控的文件
    2. 文件排除模式：用于指定要排除的文件
    """
    file_manager = _get_file_manager(ctx, config_dir)
    
    # 显示包含模式
    click.echo("当前文件包含模式:")
    if file_manager.include_patterns:
        for pattern in file_manager.include_patterns:
            click.echo(f"  - {pattern}")
    else:
        click.echo("  (无)")
    
    # 显示排除模式
    click.echo("\n当前文件排除模式:")
    if file_manager.exclude_patterns:
        for pattern in file_manager.exclude_patterns:
            click.echo(f"  - {pattern}")
    else:
        click.echo("  (无)")

@cli.command()
@click.pass_context
@click.argument('pattern')
@click.option('--config-dir', help='配置文件目录，默认为 ~/.file_tag_manager')
def add_pattern(ctx: Context, pattern: str, config_dir: str):
    """添加文件模式。
    
    支持两种模式格式：
    1. 扩展名模式：
       - .py 或 py：匹配所有 Python 文件
       - .txt 或 txt：匹配所有文本文件

    2. 路径模式：
       - src/*：匹配 src 目录下的所有文件
       - !temp/*：排除 temp 目录下的所有文件
       - docs/api/*：匹配 docs/api 目录下的所有文件
       - /src/*.py：从项目根目录开始匹配
       - !!docs/api/*：重新包含已排除目录中的特定子目录
    """
    file_manager = _get_file_manager(ctx, config_dir)
    
    # 统一路径分隔符
    pattern = pattern.strip().replace('\\', '/')
    
    # 处理扩展名模式
    if not ('/' in pattern or '*' in pattern or '!' in pattern):
        # 如果是纯扩展名，添加 *. 前缀
        pattern = f"*.{pattern.lstrip('.')}"
    # 处理目录模式
    elif pattern.endswith('/'):
        pattern = f"{pattern}*"
    
    if pattern.startswith('!'):
        # 排除模式添加到 exclude_patterns
        if pattern not in file_manager.exclude_patterns:
            file_manager.exclude_patterns.append(pattern)
            file_manager._save_data()
            click.echo(f"添加文件排除模式: {pattern}")
        else:
            click.echo(f"文件排除模式 {pattern} 已存在")
    else:
        # 包含模式添加到 include_patterns
        if pattern not in file_manager.include_patterns:
            file_manager.include_patterns.append(pattern)
            file_manager._save_data()
            click.echo(f"添加文件包含模式: {pattern}")
        else:
            click.echo(f"文件包含模式 {pattern} 已存在")

@cli.command()
@click.pass_context
@click.argument('pattern')
@click.option('--config-dir', help='配置文件目录，默认为 ~/.file_tag_manager')
def remove_pattern(ctx: Context, pattern: str, config_dir: str):
    """移除文件模式。
    
    支持两种模式格式：
    1. 扩展名模式：
       - .py 或 py：匹配所有 Python 文件
       - .txt 或 txt：匹配所有文本文件

    2. 路径模式：
       - src/*：匹配 src 目录下的所有文件
       - !temp/*：排除 temp 目录下的所有文件
       - docs/api/*：匹配 docs/api 目录下的所有文件
       - /src/*.py：从项目根目录开始匹配
       - !!docs/api/*：重新包含已排除目录中的特定子目录
    """
    file_manager = _get_file_manager(ctx, config_dir)
    
    # 统一路径分隔符
    pattern = pattern.strip().replace('\\', '/')
    
    # 处理扩展名模式
    if not ('/' in pattern or '*' in pattern or '!' in pattern):
        # 如果是纯扩展名，添加 *. 前缀
        pattern = f"*.{pattern.lstrip('.')}"
    # 处理目录模式
    elif pattern.endswith('/'):
        pattern = f"{pattern}*"
    
    # 检查原始模式和转换后的模式
    patterns_to_check = {pattern}
    if pattern.startswith('*.'):
        # 如果是 *.ext 格式，也检查 .ext 和 ext 格式
        ext = pattern[2:]
        patterns_to_check.add(f".{ext}")
        patterns_to_check.add(ext)
    
    # 先检查是否是排除模式
    if pattern.startswith('!'):
        if pattern in file_manager.exclude_patterns:
            file_manager.exclude_patterns.remove(pattern)
            file_manager._save_data()
            click.echo(f"移除文件排除模式: {pattern}")
            return
    else:
        # 检查包含模式
        for p in patterns_to_check:
            if p in file_manager.include_patterns:
                file_manager.include_patterns.remove(p)
                file_manager._save_data()
                click.echo(f"移除文件包含模式: {p}")
                return
    
    click.echo(f"未找到匹配的模式: {pattern}")

@cli.command()
@click.pass_context
@click.option('--config-dir', help='配置文件目录，默认为 ~/.file_tag_manager')
def list_directories(ctx: Context, config_dir: str):
    """列出当前监控的目录"""
    file_manager = _get_file_manager(ctx, config_dir)
    click.echo("当前监控的目录:")
    for directory in sorted(file_manager.directories):
        click.echo(f"  - {directory}")

@cli.command()
@click.pass_context
@click.argument('name')
@click.option('--description', '-d', help='标签描述')
@click.option('--parent', '-p', help='父标签ID')
@click.option('--config-dir', help='配置文件目录，默认为 ~/.file_tag_manager')
def create_tag(ctx: Context, name: str, description: str, parent: str = None, config_dir: str = None):
    """创建新标签"""
    tag_manager = _get_tag_manager(ctx, config_dir)
    tag_id = tag_manager.create_tag(name, description, parent)
    click.echo(f"创建标签成功，ID: {tag_id}")

@cli.command()
@click.pass_context
@click.argument('tag_id')
@click.option('--config-dir', help='配置文件目录，默认为 ~/.file_tag_manager')
def remove_tag(ctx: Context, tag_id: str, config_dir: str):
    """删除标签"""
    tag_manager = _get_tag_manager(ctx, config_dir)
    tag_manager.remove_tag(tag_id)
    click.echo(f"删除标签成功，ID: {tag_id}")

@cli.command()
@click.pass_context
@click.option('--config-dir', help='配置文件目录，默认为 ~/.file_tag_manager')
def list_tags(ctx: Context, config_dir: str):
    """列出所有标签"""
    tag_manager = _get_tag_manager(ctx, config_dir)
    tags = tag_manager.get_all_tags()
    if not tags:
        click.echo("暂无标签")
        return
    
    click.echo("所有标签:")
    for tag_id, tag in tags.items():
        parent_info = f" (父标签: {tag.parent})" if tag.parent else ""
        description = f"\n    描述: {tag.description}" if tag.description else ""
        click.echo(f"  - {tag.name} (ID: {tag_id}){parent_info}{description}")

@cli.command()
@click.pass_context
@click.argument('file_path')
@click.argument('tag_ids', nargs=-1)
@click.option('--config-dir', help='配置文件目录，默认为 ~/.file_tag_manager')
def add_file_tags(ctx: Context, file_path: str, tag_ids: List[str], config_dir: str):
    """为文件添加标签"""
    if not tag_ids:
        click.echo("请指定至少一个标签ID")
        return

    tag_manager = _get_tag_manager(ctx, config_dir)
    file_path = os.path.abspath(file_path)
    if not os.path.exists(file_path):
        click.echo(f"文件不存在: {file_path}")
        return

    for tag_id in tag_ids:
        try:
            tag_manager.add_tag_to_file(file_path, tag_id)
            click.echo(f"已为文件 {file_path} 添加标签: {tag_id}")
        except ValueError as e:
            click.echo(str(e))

@cli.command()
@click.pass_context
@click.argument('file_path')
@click.argument('tag_ids', nargs=-1)
@click.option('--config-dir', help='配置文件目录，默认为 ~/.file_tag_manager')
def remove_file_tags(ctx: Context, file_path: str, tag_ids: List[str], config_dir: str):
    """从文件移除标签"""
    if not tag_ids:
        click.echo("请指定至少一个标签ID")
        return

    tag_manager = _get_tag_manager(ctx, config_dir)
    file_path = os.path.abspath(file_path)
    if not os.path.exists(file_path):
        click.echo(f"文件不存在: {file_path}")
        return

    for tag_id in tag_ids:
        tag_manager.remove_tag_from_file(file_path, tag_id)
        click.echo(f"已从文件 {file_path} 移除标签: {tag_id}")

@cli.command()
@click.pass_context
@click.argument('file_path')
@click.option('--config-dir', help='配置文件目录，默认为 ~/.file_tag_manager')
def show_tags(ctx: Context, file_path: str, config_dir: str):
    """显示文件的标签"""
    tag_manager = _get_tag_manager(ctx, config_dir)
    file_path = os.path.abspath(file_path)
    if not os.path.exists(file_path):
        click.echo(f"文件不存在: {file_path}")
        return

    tag_ids = tag_manager.get_file_tags(file_path)
    if not tag_ids:
        click.echo(f"文件 {file_path} 暂无标签")
        return

    click.echo(f"文件 {file_path} 的标签:")
    for tag_id in tag_ids:
        tag = tag_manager.get_tag(tag_id)
        if tag:
            parent_info = f" (父标签: {tag.parent})" if tag.parent else ""
            description = f"\n    描述: {tag.description}" if tag.description else ""
            click.echo(f"  - {tag.name} (ID: {tag_id}){parent_info}{description}")

@cli.command()
@click.pass_context
@click.argument('tag_ids', nargs=-1)
@click.option('--match-all/--match-any', default=False, help='是否要求文件包含所有指定的标签')
@click.option('--config-dir', help='配置文件目录，默认为 ~/.file_tag_manager')
def find_files(ctx: Context, tag_ids: List[str], match_all: bool, config_dir: str):
    """查找包含指定标签的文件"""
    if not tag_ids:
        click.echo("请指定至少一个标签ID")
        return

    tag_manager = _get_tag_manager(ctx, config_dir)
    files = tag_manager.find_files_by_tags(list(tag_ids), match_all)
    if not files:
        click.echo("未找到匹配的文件")
        return

    click.echo("找到以下文件:")
    for file_path in sorted(files):
        click.echo(f"  - {file_path}")

if __name__ == '__main__':
    cli()
