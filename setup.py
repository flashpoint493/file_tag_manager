"""文件标签管理器安装配置"""

from setuptools import setup, find_packages

setup(
    name="file_tag_manager",
    version="0.1.0",
    author="Ocarina",
    author_email="Ocarina1024@gmail.com",
    packages=find_packages(),
    install_requires=[
        "PySide6>=6.0.0",
        "PyYAML>=5.1",
        "watchdog>=3.0.0",
        "python-magic-bin>=0.4.14",
        "pytest>=7.3.1",
        "click>=8.1.0",
    ],
    entry_points={
        'console_scripts': [
            'ftm=file_tag_manager.cli:cli',
        ],
    },
    package_data={
        'file_tag_manager.ui': ['config/*.yaml'],
    },
)
