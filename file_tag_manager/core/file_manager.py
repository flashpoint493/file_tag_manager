"""文件管理核心模块"""
from typing import Dict, List, Optional, Set
import os
import time
import json
import fnmatch
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

class FileManager:
    def __init__(self, root_dir: str, include_patterns: List[str] = None, exclude_patterns: List[str] = None, recursive: bool = True, config_dir: str = None):
        """初始化文件管理器
        
        Args:
            root_dir: 根目录路径
            include_patterns: 文件包含模式列表，支持以下格式：
                - 文件扩展名：*.py, *.txt
                - 目录模式：docs/*, src/**/*
            exclude_patterns: 文件排除模式列表，格式同上
            recursive: 是否递归监控子目录
            config_dir: 配置文件目录，默认为 ~/.file_tag_manager
        """
        self.root_dir = os.path.abspath(root_dir)
        self.config_dir = os.path.abspath(config_dir) if config_dir else os.path.expanduser("~/.file_tag_manager")
        self.storage_path = os.path.join(self.config_dir, "files.json")
        self.files: Dict[str, Dict] = {}  # {file_path: file_info}
        self.directories: Set[str] = set()  # 存储监控的目录路径
        self.include_patterns = list(include_patterns) if include_patterns else ["*"]
        self.exclude_patterns = list(exclude_patterns) if exclude_patterns else []
        self.recursive = recursive  # 是否递归监控子目录
        self.observer: Optional[Observer] = None
        self.file_change_callbacks = []
        os.makedirs(self.config_dir, exist_ok=True)
        self._load_data()
        self._scan_directory(self.root_dir)
        self._save_data()  # 保存初始配置
    
    def _should_include_file(self, file_path: str) -> bool:
        """检查文件是否应该被包含"""
        # 获取相对于根目录的路径
        relative_path = os.path.relpath(file_path, self.root_dir)
        # 将路径分隔符统一为 /
        relative_path = relative_path.replace('\\', '/')
        
        # 分离重新包含模式和普通包含模式
        reinclude_patterns = []
        normal_include_patterns = []
        for pattern in self.include_patterns:
            pattern = pattern.replace('\\', '/')
            if pattern.startswith('!!'):
                reinclude_patterns.append(pattern[2:])  # 移除 !!
            else:
                normal_include_patterns.append(pattern)
        
        # 首先检查是否在排除列表中
        is_excluded = False
        for pattern in self.exclude_patterns:
            # 将模式中的路径分隔符统一为 /
            pattern = pattern.replace('\\', '/').lstrip('!')  # 移除开头的 !
            # 如果模式不是以 / 开头，需要匹配所有层级的目录
            if not pattern.startswith('/'):
                # 检查文件路径的每一层
                path_parts = relative_path.split('/')
                for i in range(len(path_parts)):
                    sub_path = '/'.join(path_parts[i:])
                    if fnmatch.fnmatch(sub_path, pattern):
                        is_excluded = True
                        break
            else:
                # 如果模式以 / 开头，只匹配完整路径
                if fnmatch.fnmatch(relative_path, pattern.lstrip('/')):
                    is_excluded = True
                    break
        
        # 如果文件被排除，检查是否被重新包含
        if is_excluded:
            for pattern in reinclude_patterns:
                if not pattern.startswith('/'):
                    # 检查文件路径的每一层
                    path_parts = relative_path.split('/')
                    for i in range(len(path_parts)):
                        sub_path = '/'.join(path_parts[i:])
                        if fnmatch.fnmatch(sub_path, pattern):
                            return True
                else:
                    # 如果模式以 / 开头，只匹配完整路径
                    if fnmatch.fnmatch(relative_path, pattern.lstrip('/')):
                        return True
            return False
        
        # 最后检查是否在普通包含列表中
        for pattern in normal_include_patterns:
            if not pattern.startswith('/'):
                # 检查文件路径的每一层
                path_parts = relative_path.split('/')
                for i in range(len(path_parts)):
                    sub_path = '/'.join(path_parts[i:])
                    if fnmatch.fnmatch(sub_path, pattern):
                        return True
            else:
                # 如果模式以 / 开头，只匹配完整路径
                if fnmatch.fnmatch(relative_path, pattern.lstrip('/')):
                    return True
        
        return False

    def _should_include_directory(self, dir_path: str) -> bool:
        """检查目录是否应该被包含"""
        # 获取相对于根目录的路径
        relative_path = os.path.relpath(dir_path, self.root_dir)
        # 将路径分隔符统一为 /
        relative_path = relative_path.replace('\\', '/')
        
        # 先检查是否在排除列表中
        for pattern in self.exclude_patterns:
            pattern = pattern.replace('\\', '/').lstrip('!')  # 移除开头的 !
            if not pattern.startswith('/'):
                # 检查当前目录及其所有父目录是否被排除
                path_parts = relative_path.split('/')
                current_path = ""
                for part in path_parts:
                    if current_path:
                        current_path += "/"
                    current_path += part
                    # 检查当前路径是否匹配排除模式
                    if fnmatch.fnmatch(current_path, pattern.rstrip('/*')):
                        # 检查是否有包含模式匹配这个目录
                        for include_pattern in self.include_patterns:
                            include_pattern = include_pattern.replace('\\', '/')
                            if fnmatch.fnmatch(relative_path, include_pattern.rstrip('/*')):
                                return True
                            if fnmatch.fnmatch(relative_path + "/*", include_pattern):
                                return True
                        return False
            else:
                # 如果模式以 / 开头，只匹配完整路径
                if fnmatch.fnmatch(relative_path, pattern.lstrip('/').rstrip('/*')):
                    # 检查是否有包含模式匹配这个目录
                    for include_pattern in self.include_patterns:
                        include_pattern = include_pattern.replace('\\', '/')
                        if fnmatch.fnmatch(relative_path, include_pattern.rstrip('/*')):
                            return True
                        if fnmatch.fnmatch(relative_path + "/*", include_pattern):
                            return True
                    return False
        
        # 如果没有被排除，检查是否在包含列表中
        for pattern in self.include_patterns:
            pattern = pattern.replace('\\', '/')
            if not pattern.startswith('/'):
                # 检查目录路径的每一层
                path_parts = relative_path.split('/')
                for i in range(len(path_parts)):
                    sub_path = '/'.join(path_parts[i:])
                    if fnmatch.fnmatch(sub_path, pattern.rstrip('/*')):
                        return True
            else:
                if fnmatch.fnmatch(relative_path, pattern.lstrip('/').rstrip('/*')):
                    return True
        
        # 如果既没有被排除也没有被包含，返回 True（默认包含所有目录）
        return True

    def _load_data(self):
        """从 JSON 文件加载文件和目录信息"""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 只有当根目录相同时才加载配置
                if data.get('root_dir') == self.root_dir:
                    self.files = data.get('files', {})
                    self.directories = set(data.get('directories', []))
                    # 不要覆盖初始化时设置的模式
                    if not self.include_patterns or self.include_patterns == ["*"]:
                        self.include_patterns = data.get('include_patterns', ["*"])
                    if not self.exclude_patterns:
                        self.exclude_patterns = data.get('exclude_patterns', [])
                    self.recursive = data.get('recursive', True)
    
    def _save_data(self):
        """保存文件和目录信息到 JSON 文件"""
        data = {
            'root_dir': self.root_dir,
            'files': self.files,
            'directories': list(self.directories),
            'include_patterns': self.include_patterns,
            'exclude_patterns': self.exclude_patterns,
            'recursive': self.recursive
        }
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _scan_directory(self, directory):
        """扫描目录并更新文件信息"""
        directory = os.path.abspath(directory)
        
        # 清除现有记录
        self.files.clear()
        self.directories.clear()
        
        # 添加根目录
        self.directories.add(directory)
        self._notify_file_change('directory_created', directory)

        for root, dirs, files in os.walk(directory):
            # 如果不是递归模式，跳过子目录
            if not self.recursive and root != directory:
                continue

            # 添加子目录
            for dir_name in dirs:
                dir_path = os.path.abspath(os.path.join(root, dir_name))
                if self.recursive or os.path.dirname(dir_path) == directory:
                    if self._should_include_directory(dir_path):
                        self.directories.add(dir_path)
                        self._notify_file_change('directory_created', dir_path)

            # 添加文件
            for file_name in files:
                file_path = os.path.abspath(os.path.join(root, file_name))
                if self._should_include_file(file_path):
                    self._add_file(file_path)
        
        self._save_data()

    def _add_file(self, file_path: str):
        """添加文件到管理器"""
        try:
            abs_path = os.path.abspath(file_path)
            if os.path.exists(abs_path) and os.path.isfile(abs_path):
                stat = os.stat(abs_path)
                rel_path = os.path.relpath(abs_path, self.root_dir)
                self.files[abs_path] = {
                    'size': stat.st_size,
                    'created_time': stat.st_ctime,
                    'modified_time': stat.st_mtime,
                    'relative_path': rel_path
                }
                self._save_data()
        except Exception as e:
            print(f"Error adding file {file_path}: {e}")

    def _add_directory(self, dir_path: str):
        """添加目录到管理器"""
        try:
            abs_path = os.path.abspath(dir_path)
            if os.path.exists(abs_path) and os.path.isdir(abs_path):
                if self.recursive or os.path.dirname(abs_path) == self.root_dir:
                    if self._should_include_directory(abs_path):
                        self.directories.add(abs_path)
                        self._notify_file_change('directory_created', abs_path)
                        self._save_data()
        except Exception as e:
            print(f"Error adding directory {dir_path}: {e}")

    def _remove_directory(self, directory):
        """移除目录及其所有文件"""
        directory = os.path.abspath(directory)
        
        # 移除该目录下的所有文件
        files_to_remove = [f for f in self.files if f.startswith(directory)]
        for file_path in files_to_remove:
            del self.files[file_path]
            self._notify_file_change('deleted', file_path)
        
        # 移除该目录下的所有子目录
        subdirs_to_remove = [d for d in self.directories if d.startswith(directory)]
        for subdir in subdirs_to_remove:
            if subdir in self.directories:  # 检查目录是否存在
                self.directories.remove(subdir)
                self._notify_file_change('directory_deleted', subdir)
        
        # 移除目录本身
        if directory in self.directories:  # 检查目录是否存在
            self.directories.remove(directory)
            self._notify_file_change('directory_deleted', directory)
        
        self._save_data()

    def _notify_file_change(self, event_type: str, src_path: str, dst_path: str = None):
        """通知文件变更"""
        for callback in self.file_change_callbacks:
            try:
                callback(event_type, src_path, dst_path)
            except Exception as e:
                print(f"Error in file change callback: {e}")

    def start_monitoring(self):
        """开始监控目录"""
        if not self.observer:
            self.observer = Observer()
            event_handler = FileEventHandler(self)
            self.observer.schedule(event_handler, self.root_dir, recursive=self.recursive)
            self.observer.start()

    def stop_monitoring(self):
        """停止监控目录"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

    def add_file_change_callback(self, callback):
        """添加文件变更回调函数"""
        if callback not in self.file_change_callbacks:
            self.file_change_callbacks.append(callback)

    def remove_file_change_callback(self, callback):
        """移除文件变更回调函数"""
        if callback in self.file_change_callbacks:
            self.file_change_callbacks.remove(callback)

    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息字典，如果文件不存在则返回None
        """
        abs_path = os.path.abspath(file_path)
        return self.files.get(abs_path)
    
    def find_files(self, pattern: str = None, min_size: int = None, max_size: int = None):
        """查找文件"""
        result = []
        for file_path, info in self.files.items():
            if not os.path.exists(file_path):
                continue

            # 检查文件名模式
            if pattern and not fnmatch.fnmatch(os.path.basename(file_path), pattern):
                continue
            
            # 检查文件大小
            size = info.get('size', 0)
            if min_size is not None and size < min_size:
                continue
            if max_size is not None and size > max_size:
                continue
            
            result.append(file_path)
        
        return sorted(result)  # 排序以确保结果顺序一致

    def _match_pattern(self, file_path, pattern):
        """检查文件路径是否匹配模式"""
        return fnmatch.fnmatch(os.path.basename(file_path), pattern)

class FileEventHandler(FileSystemEventHandler):
    """文件事件处理器"""
    def __init__(self, manager):
        self.manager = manager
        self._lock = threading.Lock()

    def on_created(self, event):
        """处理创建事件"""
        with self._lock:
            if event.is_directory:
                if self.manager.recursive or os.path.dirname(event.src_path) == self.manager.root_dir:
                    if self.manager._should_include_directory(event.src_path):
                        self.manager.directories.add(event.src_path)
                        self.manager._notify_file_change('directory_created', event.src_path)
                        self.manager._save_data()
            else:
                if self.manager._should_include_file(event.src_path):
                    self.manager._add_file(event.src_path)
                    self.manager._notify_file_change('created', event.src_path)

    def on_deleted(self, event):
        """处理删除事件"""
        with self._lock:
            src_path = os.path.abspath(event.src_path)
            print("\n收到删除事件:", src_path)  # 调试信息
            print("监控的目录列表:", self.manager.directories)  # 调试信息
            
            # 首先检查是否是被监控的目录
            if src_path in self.manager.directories:
                print("处理目录删除:", src_path)  # 调试信息
                # 移除该目录下的所有文件
                files_to_remove = [f for f in self.manager.files if f.startswith(src_path)]
                for file_path in files_to_remove:
                    del self.manager.files[file_path]
                    self.manager._notify_file_change('deleted', file_path)
                
                # 移除该目录下的所有子目录
                subdirs_to_remove = [d for d in self.manager.directories if d.startswith(src_path)]
                for subdir in subdirs_to_remove:
                    if subdir != src_path:  # 不要重复通知主目录的删除
                        self.manager.directories.remove(subdir)
                        self.manager._notify_file_change('directory_deleted', subdir)
                
                # 移除目录本身
                self.manager.directories.remove(src_path)
                self.manager._notify_file_change('directory_deleted', src_path)
                self.manager._save_data()
            # 然后检查是否是被监控的文件
            elif src_path in self.manager.files:
                print("处理文件删除:", src_path)  # 调试信息
                del self.manager.files[src_path]
                self.manager._notify_file_change('deleted', src_path)
                self.manager._save_data()

    def on_modified(self, event):
        """处理修改事件"""
        if not event.is_directory and self.manager._should_include_file(event.src_path):
            self.manager._add_file(event.src_path)
            self.manager._notify_file_change('modified', event.src_path)

    def on_moved(self, event):
        """处理移动事件"""
        with self._lock:
            src_path = os.path.abspath(event.src_path)
            dest_path = os.path.abspath(event.dest_path)
            if src_path in self.manager.directories:
                self.manager.directories.remove(src_path)
                if self.manager.recursive or os.path.dirname(dest_path) == self.manager.root_dir:
                    if self.manager._should_include_directory(dest_path):
                        self.manager.directories.add(dest_path)
                        self.manager._notify_file_change('directory_moved', src_path, dest_path)
                    else:
                        self.manager._notify_file_change('directory_deleted', src_path)
                else:
                    self.manager._notify_file_change('directory_deleted', src_path)
                self.manager._save_data()
            elif src_path in self.manager.files:
                del self.manager.files[src_path]
                if self.manager._should_include_file(dest_path):
                    self.manager._add_file(dest_path)
                    self.manager._notify_file_change('moved', src_path, dest_path)
                else:
                    self.manager._notify_file_change('deleted', src_path)
                self.manager._save_data()
