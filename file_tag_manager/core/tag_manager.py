"""标签管理核心模块"""
from typing import List, Dict, Optional, Set
import os
import json
from dataclasses import dataclass, asdict


@dataclass
class Tag:
    """标签"""
    name: str
    description: str
    parent: Optional[str] = None


class TagManager:
    """标签管理器"""

    def __init__(self, config_dir: Optional[str] = None):
        """初始化标签管理器

        Args:
            config_dir: 配置文件目录，默认为 ~/.file_tag_manager
        """
        self.config_dir = config_dir if config_dir else os.path.expanduser("~/.file_tag_manager")
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

        self.tags_file = os.path.join(self.config_dir, "tags.json")
        self.tags: Dict[str, Tag] = {}  # tag_id -> Tag
        self.file_tags: Dict[str, Set[str]] = {}  # file_path -> set(tag_id)
        self._load_data()

    def _load_data(self) -> None:
        """从文件加载标签数据"""
        if not os.path.exists(self.tags_file):
            return

        with open(self.tags_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.tags = {
                tag_id: Tag(**tag_data)
                for tag_id, tag_data in data.get('tags', {}).items()
            }
            self.file_tags = {
                file_path: set(tag_ids)
                for file_path, tag_ids in data.get('file_tags', {}).items()
            }

    def _save_data(self) -> None:
        """保存标签数据到文件"""
        data = {
            'tags': {
                tag_id: asdict(tag)
                for tag_id, tag in self.tags.items()
            },
            'file_tags': {
                file_path: list(tag_ids)
                for file_path, tag_ids in self.file_tags.items()
            }
        }
        with open(self.tags_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create_tag(self, name: str, description: str = "", parent: Optional[str] = None) -> str:
        """创建新标签

        Args:
            name: 标签名称
            description: 标签描述
            parent: 父标签ID

        Returns:
            新标签的ID
        """
        if parent and parent not in self.tags:
            raise ValueError(f"父标签 {parent} 不存在")

        # 生成唯一ID
        tag_id = name.lower().replace(' ', '-')
        suffix = 1
        while tag_id in self.tags:
            tag_id = f"{name.lower().replace(' ', '-')}-{suffix}"
            suffix += 1

        self.tags[tag_id] = Tag(name=name, description=description, parent=parent)
        self._save_data()
        return tag_id

    def remove_tag(self, tag_id: str) -> None:
        """删除标签及其所有子标签

        Args:
            tag_id: 要删除的标签ID
        """
        if tag_id not in self.tags:
            raise ValueError(f"标签 {tag_id} 不存在")

        # 找到所有子标签
        child_tags = []
        for tid, tag in self.tags.items():
            if tag.parent == tag_id:
                child_tags.append(tid)

        # 递归删除子标签
        for child_id in child_tags:
            self.remove_tag(child_id)

        # 从所有文件中移除此标签
        for file_path in list(self.file_tags.keys()):
            if tag_id in self.file_tags[file_path]:
                self.file_tags[file_path].remove(tag_id)
                if not self.file_tags[file_path]:
                    del self.file_tags[file_path]

        # 删除标签本身
        del self.tags[tag_id]
        self._save_data()

    def get_tag(self, tag_id: str) -> Optional[Tag]:
        """获取标签信息

        Args:
            tag_id: 标签ID

        Returns:
            标签信息，如果标签不存在则返回 None
        """
        return self.tags.get(tag_id)

    def get_all_tags(self) -> Dict[str, Tag]:
        """获取所有标签

        Returns:
            所有标签的字典，key 为标签ID，value 为标签信息
        """
        return self.tags.copy()

    def add_tag_to_file(self, file_path: str, tag_id: str) -> None:
        """为文件添加标签

        Args:
            file_path: 文件路径
            tag_id: 标签ID
        """
        if tag_id not in self.tags:
            raise ValueError(f"标签 {tag_id} 不存在")

        file_path = os.path.normpath(file_path)
        if file_path not in self.file_tags:
            self.file_tags[file_path] = set()
        self.file_tags[file_path].add(tag_id)
        self._save_data()

    def remove_tag_from_file(self, file_path: str, tag_id: str) -> None:
        """从文件移除标签

        Args:
            file_path: 文件路径
            tag_id: 标签ID
        """
        file_path = os.path.normpath(file_path)
        if file_path in self.file_tags and tag_id in self.file_tags[file_path]:
            self.file_tags[file_path].remove(tag_id)
            if not self.file_tags[file_path]:
                del self.file_tags[file_path]
            self._save_data()

    def get_file_tags(self, file_path: str) -> Set[str]:
        """获取文件的所有标签

        Args:
            file_path: 文件路径

        Returns:
            文件的标签ID集合
        """
        file_path = os.path.normpath(file_path)
        return self.file_tags.get(file_path, set()).copy()

    def find_files_by_tags(self, tag_ids: List[str], match_all: bool = False) -> List[str]:
        """查找包含指定标签的文件

        Args:
            tag_ids: 标签ID列表
            match_all: 是否要求文件包含所有指定的标签

        Returns:
            匹配的文件路径列表
        """
        if not tag_ids:
            return []

        for tag_id in tag_ids:
            if tag_id not in self.tags:
                raise ValueError(f"标签 {tag_id} 不存在")

        result = []
        for file_path, file_tag_ids in self.file_tags.items():
            if match_all:
                if all(tag_id in file_tag_ids for tag_id in tag_ids):
                    result.append(os.path.normpath(file_path))
            else:
                if any(tag_id in file_tag_ids for tag_id in tag_ids):
                    result.append(os.path.normpath(file_path))
        return sorted(result)
