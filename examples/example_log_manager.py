"""
这个示例展示如何使用LogManager进行日志管理，包括初始化、存档日志、检索日志和回滚操作
"""
import os
import sys
from typing import List, Optional

# 添加项目根目录到sys.path，确保可以导入core模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.diff import DiffInfo
from core.log_manager import LogManager, LogConfig, LogEntry
from core.log_config import setup_logging
from core.terminal import (
    print_header, print_subheader, print_key_value, 
    print_file_info, print_code_block, print_diff,
    success, error, confirm_action
)


def display_log_entries(entries: List[LogEntry]) -> None:
    """显示日志条目的主要信息"""
    if not entries:
        print("没有找到日志条目")
        return
        
    for i, entry in enumerate(entries):
        if i > 0:
            # Add separator between entries
            print("\n" + "-" * 40)
            
        print_subheader(f"轮次 {entry.round_num} - {entry.timestamp}")
        print_key_value("日志路径", entry.log_path, indent=2)
        
        # Show prompt snippets
        sys_prompt_preview = entry.sys_prompt[:50] + "..." if len(entry.sys_prompt) > 50 else entry.sys_prompt
        user_prompt_preview = entry.prompt[:50] + "..." if len(entry.prompt) > 50 else entry.prompt
        resp_preview = entry.response[:50] + "..." if len(entry.response) > 50 else entry.response
        
        print_key_value("系统提示词", sys_prompt_preview, indent=2)
        print_key_value("用户提示词", user_prompt_preview, indent=2)
        print_key_value("响应预览", resp_preview, indent=2)
        print_key_value("修改的文件数量", len(entry.modified_files), indent=2)


def display_round_info(round_entry: Optional[LogEntry]) -> None:
    """显示特定轮次的详细信息"""
    if not round_entry:
        error("未找到指定轮次的日志条目")
        return
        
    print_header(f"轮次 {round_entry.round_num} 详细信息")
    print_key_value("时间戳", round_entry.timestamp)
    print_key_value("日志路径", round_entry.log_path)
    
    # Show system prompt
    print_subheader("系统提示词")
    print_code_block(round_entry.sys_prompt, language="text")
    
    # Show user prompt
    print_subheader("用户提示词")
    print_code_block(round_entry.prompt, language="text")
    
    # Show modified files
    if round_entry.modified_files:
        print_subheader(f"修改的文件 ({len(round_entry.modified_files)}个)")
        for diff in round_entry.modified_files:
            print_file_info(diff.file_path)
            print_diff(diff.diff_content, max_lines=10)
    else:
        print_key_value("修改的文件", "无")


def main() -> None:
    """示例主函数，展示LogManager的各种用法"""
    # 设置日志
    setup_logging()
    
    # 创建工作目录 - 使用当前项目根目录
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    issue_id = 999  # 使用一个示例issue_id
    
    print_header("LogManager使用示例", char="=")
    
    # 初始化LogManager
    print_subheader("1. 初始化LogManager")
    log_config = LogConfig(
        project_dir=project_dir,
        issue_id=issue_id,
        mode="client"  # 客户端模式
    )
    log_manager = LogManager(config=log_config)
    
    print_key_value("当前轮次", log_manager.get_current_round(), indent=2)
    print_key_value("日志路径", log_manager.logs_path, indent=2)
    print_key_value("Issue日志路径", log_manager.issues_path, indent=2)
    
    # 创建示例数据
    print_subheader("2. 存档日志")
    
    # 示例提示和响应
    sys_prompt = "你是一个代码助手，帮助用户解决编程问题。"
    user_prompt = "请帮我实现一个简单的Python函数，用于计算两个数的最大公约数。"
    ai_response = """
    以下是计算最大公约数的Python函数:
    
    
