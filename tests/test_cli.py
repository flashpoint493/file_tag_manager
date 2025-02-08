"""CLI 测试"""
import os
import shutil
import pytest
from click.testing import CliRunner
from file_tag_manager.cli import cli, Context
from file_tag_manager.core.tag_manager import TagManager

@pytest.fixture
def runner():
    """创建 CLI 测试运行器"""
    return CliRunner()

@pytest.fixture
def test_dir(tmp_path):
    """创建临时测试目录"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    return str(test_dir)

@pytest.fixture
def config_dir(tmp_path):
    """创建临时配置目录"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return str(config_dir)

@pytest.fixture
def ctx():
    """创建测试上下文"""
    return Context()

def test_init_with_patterns(runner, test_dir, ctx, config_dir):
    """测试带文件包含模式的初始化命令"""
    # 创建测试文件
    txt_file = os.path.join(test_dir, "test.txt")
    py_file = os.path.join(test_dir, "test.py")
    md_file = os.path.join(test_dir, "test.md")
    os.makedirs(os.path.join(test_dir, "docs"))
    doc_file = os.path.join(test_dir, "docs", "test.doc")

    for file in [txt_file, py_file, md_file, doc_file]:
        with open(file, "w") as f:
            f.write("test")

    # 运行初始化命令
    result = runner.invoke(cli, ['init', test_dir, '-p', '.txt', '-p', '.py', '-p', 'docs/*', '--config-dir', config_dir], obj=ctx)
    assert result.exit_code == 0, f"初始化命令失败: {result.output}"
    assert "开始监控目录" in result.output
    assert "*.txt" in result.output
    assert "*.py" in result.output
    assert "docs/*" in result.output

    # 列出文件包含模式
    result = runner.invoke(cli, ['list-patterns', '--config-dir', config_dir], obj=ctx)
    assert result.exit_code == 0, f"列出模式命令失败: {result.output}"
    print(f"\n当前文件包含模式:\n{result.output}")
    patterns_to_check = ['*.txt', '*.py', 'docs/*']
    for pattern in patterns_to_check:
        assert pattern in result.output, f"模式 {pattern} 不在输出中:\n{result.output}"

    # 添加新的文件包含模式
    result = runner.invoke(cli, ['add-pattern', '*.md', '--config-dir', config_dir], obj=ctx)
    assert result.exit_code == 0, f"添加模式命令失败: {result.output}"
    assert "添加文件包含模式: *.md" in result.output

    # 移除文件包含模式
    result = runner.invoke(cli, ['remove-pattern', '*.txt', '--config-dir', config_dir], obj=ctx)
    assert result.exit_code == 0, f"移除模式命令失败: {result.output}"
    assert "移除文件包含模式: *.txt" in result.output

    # 列出监控的目录
    result = runner.invoke(cli, ['list-directories', '--config-dir', config_dir], obj=ctx)
    assert result.exit_code == 0, f"列出目录命令失败: {result.output}"
    assert os.path.join(test_dir, "docs") in result.output

def test_directory_monitoring(runner, test_dir, ctx, config_dir):
    """测试目录监控功能"""
    # 初始化
    result = runner.invoke(cli, ['init', test_dir, '--config-dir', config_dir], obj=ctx)
    assert result.exit_code == 0, f"初始化命令失败: {result.output}"

    # 创建子目录
    sub_dir = os.path.join(test_dir, "subdir")
    os.makedirs(sub_dir)

    # 等待文件系统事件
    import time
    time.sleep(1)

    # 列出监控的目录
    result = runner.invoke(cli, ['list-directories', '--config-dir', config_dir], obj=ctx)
    assert result.exit_code == 0, f"列出目录命令失败: {result.output}"
    print(f"\n创建目录后的目录列表:\n{result.output}")
    assert sub_dir in result.output, f"新创建的目录 {sub_dir} 不在输出中:\n{result.output}"

    # 删除子目录
    shutil.rmtree(sub_dir)

    # 等待文件系统事件
    time.sleep(1)

    # 再次列出监控的目录
    result = runner.invoke(cli, ['list-directories', '--config-dir', config_dir], obj=ctx)
    assert result.exit_code == 0, f"列出目录命令失败: {result.output}"
    print(f"\n删除目录后的目录列表:\n{result.output}")
    assert sub_dir not in result.output, f"已删除的目录 {sub_dir} 仍在输出中:\n{result.output}"
