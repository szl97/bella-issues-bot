"""
版本管理器使用示例

展示如何使用VersionManager进行版本控制、历史追踪和回退操作
"""

import logging
import os
from dotenv import load_dotenv

from core.ai import AIConfig
from core.git_manager import GitManager, GitConfig
from core.log_config import setup_logging
from core.log_manager import LogManager, LogConfig
from core.version_manager import VersionManager


def setup_test_environment():
    """设置测试环境"""
    # 加载环境变量
    load_dotenv()
    
    # 创建工作目录
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../."))
    issue_id = 99  # 使用测试issue ID
    
    # 创建AI配置
    ai_config = AIConfig(
        model_name="gpt-4o",
        temperature=0.7
    )
    
    # 创建Git配置
    git_config = GitConfig(
        repo_path=project_dir,
        default_branch="main"
    )
    git_manager = GitManager(config=git_config)
    
    # 创建日志配置
    log_config = LogConfig(
        project_dir=project_dir,
        issue_id=issue_id,
        mode="client"
    )
    log_manager = LogManager(config=log_config)
    
    # 创建版本管理器
    version_manager = VersionManager(
        issue_id=issue_id,
        ai_config=ai_config,
        log_manager=log_manager,
        git_manager=git_manager
    )
    
    return version_manager, log_manager, project_dir


def example_basic_version_info():
    """示例1: 获取基本版本信息"""
    print("=" * 60)
    print("示例1: 获取基本版本信息")
    print("=" * 60)
    
    version_manager, log_manager, project_dir = setup_test_environment()
    
    # 获取当前轮次
    current_round = log_manager.get_current_round()
    print(f"当前轮次: {current_round}")
    
    # 获取历史记录
    history = version_manager.get_formatted_history()
    if history:
        print("\n历史记录:")
        print(history)
    else:
        print("暂无历史记录")


def example_version_context_generation():
    """示例2: 版本上下文生成"""
    print("=" * 60)
    print("示例2: 版本上下文生成")
    print("=" * 60)
    
    version_manager, log_manager, project_dir = setup_test_environment()
    
    # 模拟用户需求
    original_requirement = """
    优化代码性能，特别是文件处理部分。
    同时需要确保之前实现的功能不会被破坏。
    """
    
    # 确定版本并生成上下文
    requirement, history = version_manager.ensure_version_and_generate_context(original_requirement)
    
    print(f"处理后的需求:")
    print(requirement)
    print(f"\n生成的历史上下文:")
    print(history if history else "无历史上下文")


def example_version_rollback_analysis():
    """示例3: 版本回退分析"""
    print("=" * 60)
    print("示例3: 版本回退分析")
    print("=" * 60)
    
    version_manager, log_manager, project_dir = setup_test_environment()
    
    # 模拟一个可能需要回退的需求
    requirement_that_may_need_rollback = """
    上一次的修改有问题，请回退到第2轮的状态，
    然后重新实现用户登录功能，确保安全性。
    """
    
    print(f"分析需求: {requirement_that_may_need_rollback}")
    
    # 如果当前轮次大于1，演示回退分析
    if version_manager.current_round_num > 1:
        print("\n开始分析是否需要版本回退...")
        # 这里会调用AI分析是否需要回退
        # 在实际使用中，这会通过ensure_version_and_generate_context自动处理
        requirement, history = version_manager.ensure_version_and_generate_context(requirement_that_may_need_rollback)
        print(f"分析结果 - 最终需求: {requirement}")
    else:
        print("当前为第一轮，无需回退分析")


def example_log_entries_extraction():
    """示例4: 日志条目提取"""
    print("=" * 60)
    print("示例4: 日志条目提取")
    print("=" * 60)
    
    version_manager, log_manager, project_dir = setup_test_environment()
    
    # 获取所有历史版本信息
    history_versions = version_manager._extract_history()
    
    if history_versions:
        print(f"找到 {len(history_versions)} 个历史版本:")
        for version in history_versions:
            print(f"  轮次 {version.round_num}: {version.requirement[:50]}...")
    else:
        print("暂无历史版本记录")


def main():
    """主函数，运行所有示例"""
    setup_logging(log_level=logging.INFO)
    
    print("版本管理器使用示例")
    print("=" * 80)
    
    try:
        # 运行各个示例
        example_basic_version_info()
        example_version_context_generation()
        example_version_rollback_analysis()
        example_log_entries_extraction()
        
        print("\n" + "=" * 80)
        print("所有示例运行完成！")
        
    except Exception as e:
        print(f"运行示例时出错: {str(e)}")
        logging.error(f"示例运行失败: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
