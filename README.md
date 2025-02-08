# File Tag Manager

一个强大的文件标签管理工具，帮助你更好地组织和查找文件。

## 功能特点

- 文件监控和自动标记
- 灵活的文件模式匹配
- 标签层级管理
- 快速文件搜索
- 实时文件系统监控
- 数据导入导出
- 数据备份和恢复
- 支持未来NAS服务扩展

## 安装

### 系统要求

- Python 3.8 或更高版本
- pip 包管理器

### 安装步骤

## 开发指南

### 开发环境设置

1. 克隆仓库：

```bash
git clone https://github.com/yourusername/file_tag_manager.git
cd file_tag_manager
```

2. 创建并激活虚拟环境（推荐）

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python3 -m venv .venv
source venv/bin/activate
```

3. 安装包

```bash
# 安装开发依赖
pip install -e ".[dev]"
# 安装基本包
pip install file-tag-manager

```

## 快速开始

1. 初始化目录监控：
```bash
ftm init /path/to/project
```
配置文件默认保存目录：
Windows: `C:/Users/user_name/.file_tag_manager` 
Linux: `~/.file_tag_manager` 

2. 添加文件包含模式：

```bash
ftm add-pattern "*.py"    # 监控所有Python文件
ftm add-pattern "src/*"   # 监控src目录下的所有文件
```

3. 创建标签：

```bash
ftm create-tag "项目" -d "项目相关文件"
ftm create-tag "文档" -p project-id -d "项目文档"  # 创建子标签
```

4. 为文件添加标签：

```bash
ftm add-file-tags /path/to/file tag-id1 tag-id2
```


### 运行测试

我们使用pytest进行单元测试。测试文件位于`tests/`目录下。

1. 运行所有测试：

```bash
python -m pytest
```

2. 运行特定测试文件：

```bash
python -m pytest tests/test_file_manager.py
```

3. 运行特定测试用例：

```bash
python -m pytest tests/test_file_manager.py::test_scan_directory
```

4. 显示详细输出：

```bash
python -m pytest -v
```

5. 显示测试覆盖率报告：

```bash
python -m pytest --cov=file_tag_manager tests/
```

### 代码风格

我们使用以下工具确保代码质量：

- black：代码格式化
- flake8：代码风格检查
- mypy：类型检查

运行代码质量检查：

```bash
# 格式化代码
black .

# 运行风格检查
flake8 .

# 运行类型检查
mypy .
```

## CLI 命令详解

### 文件监控管理

#### 初始化目录监控

```bash
ftm init [OPTIONS] DIRECTORY

选项：
  -p, --patterns TEXT     要监控的文件模式，支持多次使用
  --recursive/--no-recursive  是否递归监控子目录（默认：是）
  --config-dir TEXT      配置文件目录
  --help                 显示帮助信息
```

文件模式支持两种格式：

1. 扩展名模式：
   - `.py` 或 `py`：匹配所有Python文件
   - `.txt` 或 `txt`：匹配所有文本文件

2. 路径模式：
   - `src/*`：匹配src目录下的所有文件
   - `!temp/*`：排除temp目录下的所有文件
   - `docs/api/*`：匹配docs/api目录下的所有文件
   - `/src/*.py`：从项目根目录开始匹配
   - `!!docs/api/*`：重新包含已排除目录中的特定子目录

示例：

```bash
# 监控所有Python和文本文件
ftm init /path/to/project -p "*.py" -p "*.txt"

# 监控src目录，但排除测试文件
ftm init /path/to/project -p "src/*" -p "!src/tests/*"

# 使用自定义配置目录
ftm init /path/to/project -p "*.py" --config-dir ~/.my-config
```

#### 管理文件模式

```bash
# 列出当前的文件包含模式
ftm list-patterns

# 添加新的文件包含模式
ftm add-pattern "*.jpg"

# 移除文件包含模式
ftm remove-pattern "*.jpg"

# 列出当前监控的目录
ftm list-directories
```

### 标签管理

#### 创建和管理标签

```bash
# 创建新标签
ftm create-tag "标签名" -d "标签描述"

# 创建子标签
ftm create-tag "子标签" -p "父标签ID" -d "标签描述"

# 列出所有标签
ftm list-tags

# 删除标签
ftm remove-tag "标签ID"
```

#### 文件标签操作

```bash
# 为文件添加标签
ftm add-file-tags /path/to/file tag-id1 tag-id2

# 显示文件的标签
ftm show-tags /path/to/file

# 从文件移除标签
ftm remove-file-tags /path/to/file tag-id1 tag-id2
```

#### 查找文件

```bash
# 查找包含指定标签的文件
ftm find-files 标签ID1 标签ID2 [选项]

选项：
  --match-all    要求文件包含所有指定的标签（默认：否）
```

## 配置文件

配置文件默认保存目录：
Windows: `C:/Users/user_name/.file_tag_manager` 
Linux: `~/.file_tag_manager` 


- `files.json`: 保存文件监控配置和目录信息
- `tags.json`: 保存标签信息和文件-标签关联关系

可以通过 `--config-dir` 参数指定其他配置目录。

## 故障排除

1. **文件监控问题**
   - 确保有权限访问监控的目录
   - 检查文件包含模式是否正确
   - 验证目录是否在监控列表中

2. **标签操作失败**
   - 检查标签ID是否存在
   - 确保文件路径正确且存在
   - 验证配置文件权限

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件
