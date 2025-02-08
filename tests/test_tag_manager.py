"""标签管理器测试"""
import os
import json
import pytest
from file_tag_manager.core import TagManager

def normalize_path(path: str) -> str:
    """标准化路径"""
    return os.path.normpath(path)

@pytest.fixture
def temp_tag_file(tmp_path):
    """创建临时标签文件"""
    tag_file = tmp_path / "test_tags.json"
    return str(tag_file)

@pytest.fixture
def tag_manager(temp_tag_file):
    """创建标签管理器实例"""
    return TagManager(config_dir=os.path.dirname(temp_tag_file))

def test_create_tag(tag_manager):
    """测试创建标签"""
    # 创建普通标签
    tag_id = tag_manager.create_tag("工作", "工作相关文件")
    assert tag_id in tag_manager.tags
    assert tag_manager.tags[tag_id].name == "工作"
    assert tag_manager.tags[tag_id].description == "工作相关文件"
    assert tag_manager.tags[tag_id].parent is None
    
    # 创建子标签
    child_tag_id = tag_manager.create_tag("项目", "项目文档", parent=tag_id)
    assert child_tag_id in tag_manager.tags
    assert tag_manager.tags[child_tag_id].parent == tag_id

def test_add_file_tags(tag_manager):
    """测试为文件添加标签"""
    # 创建测试标签
    tag1 = tag_manager.create_tag("标签1")
    tag2 = tag_manager.create_tag("标签2")
    
    # 添加标签到文件
    file_path = normalize_path("/test/file.txt")
    tag_manager.add_tag_to_file(file_path, tag1)
    tag_manager.add_tag_to_file(file_path, tag2)
    
    assert file_path in tag_manager.file_tags
    assert tag1 in tag_manager.file_tags[file_path]
    assert tag2 in tag_manager.file_tags[file_path]

def test_remove_file_tags(tag_manager):
    """测试移除文件的标签"""
    # 创建测试标签并添加到文件
    tag1 = tag_manager.create_tag("标签1")
    tag2 = tag_manager.create_tag("标签2")
    file_path = normalize_path("/test/file.txt")
    tag_manager.add_tag_to_file(file_path, tag1)
    tag_manager.add_tag_to_file(file_path, tag2)
    
    # 移除一个标签
    tag_manager.remove_tag_from_file(file_path, tag1)
    assert tag1 not in tag_manager.file_tags[file_path]
    assert tag2 in tag_manager.file_tags[file_path]
    
    # 移除所有标签
    tag_manager.remove_tag_from_file(file_path, tag2)
    assert file_path not in tag_manager.file_tags

def test_get_file_tags(tag_manager):
    """测试获取文件的标签"""
    # 创建测试标签
    tag1 = tag_manager.create_tag("标签1", "描述1")
    tag2 = tag_manager.create_tag("标签2", "描述2")
    file_path = normalize_path("/test/file.txt")
    
    # 测试空文件
    assert tag_manager.get_file_tags(file_path) == set()
    
    # 添加标签后测试
    tag_manager.add_tag_to_file(file_path, tag1)
    tag_manager.add_tag_to_file(file_path, tag2)
    tags = tag_manager.get_file_tags(file_path)
    assert len(tags) == 2
    assert tag1 in tags
    assert tag2 in tags

def test_find_files_by_tags(tag_manager):
    """测试通过标签查找文件"""
    # 创建测试标签
    tag1 = tag_manager.create_tag("标签1")
    tag2 = tag_manager.create_tag("标签2")
    tag3 = tag_manager.create_tag("标签3")
    
    # 创建测试文件和标签关联
    file1 = normalize_path("/test/file1.txt")
    file2 = normalize_path("/test/file2.txt")
    file3 = normalize_path("/test/file3.txt")
    
    tag_manager.add_tag_to_file(file1, tag1)
    tag_manager.add_tag_to_file(file1, tag2)
    tag_manager.add_tag_to_file(file2, tag2)
    tag_manager.add_tag_to_file(file2, tag3)
    tag_manager.add_tag_to_file(file3, tag1)
    tag_manager.add_tag_to_file(file3, tag3)
    
    # 测试匹配所有标签
    files = tag_manager.find_files_by_tags([tag1, tag2], match_all=True)
    assert len(files) == 1
    assert file1 in files
    
    # 测试匹配任意标签
    files = tag_manager.find_files_by_tags([tag1, tag2], match_all=False)
    assert len(files) == 3
    assert file1 in files
    assert file2 in files
    assert file3 in files

def test_data_persistence(temp_tag_file):
    """测试数据持久化"""
    # 创建标签并保存
    tag_manager1 = TagManager(config_dir=os.path.dirname(temp_tag_file))
    tag1 = tag_manager1.create_tag("标签1", "描述1")
    file_path = normalize_path("/test/file.txt")
    tag_manager1.add_tag_to_file(file_path, tag1)
    
    # 创建新的实例并验证数据
    tag_manager2 = TagManager(config_dir=os.path.dirname(temp_tag_file))
    assert tag1 in tag_manager2.tags
    assert tag_manager2.tags[tag1].name == "标签1"
    assert tag_manager2.tags[tag1].description == "描述1"
    assert file_path in tag_manager2.file_tags
    assert tag1 in tag_manager2.file_tags[file_path]
