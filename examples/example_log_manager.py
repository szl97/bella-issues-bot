"""
这个示例展示如何使用LogManager进行日志管理，包括初始化、存档日志、检索日志和回滚操作
"""
import os
import sys
from typing import List

# 添加项目根目录到sys.path，确保可以导入core模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.diff import DiffInfo
from core.log_manager import LogManager, LogConfig, LogEntry
from core.log_config import setup_logging


def print_separator(title: str):
    """打印分隔线和标题，使输出更易读"""
    print("\n" + "=" * 50)
    print(f"  {title}")
    print("=" * 50)


def display_log_entries(entries: List[LogEntry]):
    """显示日志条目的主要信息"""
    for entry in entries:
        print(f"轮次 {entry.round_num} - {entry.timestamp}")
        print(f"  系统提示词 (前30字符): {entry.sys_prompt[:30]}...")
        print(f"  用户提示词 (前30字符): {entry.prompt[:30]}...")
        print(f"  响应内容 (前30字符): {entry.response[:30]}...")
        print(f"  修改的文件数量: {len(entry.modified_files)}")
        print("---")


def main():
    """示例主函数，展示LogManager的各种用法"""
    # 设置日志
    setup_logging()
    
    # 创建工作目录 - 使用当前项目根目录
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    issue_id = 999  # 使用一个示例issue_id
    
    print_separator("1. 初始化LogManager")
    # 初始化LogManager
    log_config = LogConfig(
        project_dir=project_dir,
        issue_id=issue_id,
        mode="client"  # 客户端模式
    )
    log_manager = LogManager(config=log_config)
    
    print(f"LogManager已初始化，当前轮次: {log_manager.get_current_round()}")
    print(f"日志路径: {log_manager.logs_path}")
    print(f"Issue日志路径: {log_manager.issues_path}")
    
    # 创建示例数据
    print_separator("2. 存档日志")
    
    # 示例提示和响应
    sys_prompt = "你是一个代码助手，帮助用户解决编程问题。"
    user_prompt = "请帮我实现一个简单的Python函数，用于计算两个数的最大公约数。"
    ai_response = """
    以下是计算最大公约数的Python函数:
    
    
    
