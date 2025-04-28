"""
高级示例：版本回滚操作

此示例展示如何在生产环境中使用VersionManager进行版本回滚操作，
包括自动分析和手动回滚两种方式。
"""

import logging
import os
from typing import Optional, Tuple

from dotenv import load_dotenv

from core.ai import AIConfig
from core.git_manager import GitManager, GitConfig
from core.log_config import setup_logging
from core.log_manager import LogManager, LogConfig
from core.version_manager import VersionManager


def analyze_rollback_need(version_manager: VersionManager, requirement: str) -> Tuple[bool, Optional[int], Optional[str], Optional[str]]:
    """
    使用AI分析是否需要回滚到特定版本
    
    Args:
        version_manager: 版本管理器实例
        requirement: 用户需求
        
    Returns:
        Tuple[bool, Optional[int], Optional[str], Optional[str]]: 
        (是否需要回滚, 目标轮次, 整合后的需求, 分析原因)
    """
    return version_manager._analyze_rollback_need(requirement)


def execute_rollback(version_manager: VersionManager, target_round: int) -> bool:
    """
    执行版本回滚操作
    
    Args:
        version_manager: 版本管理器实例
        target_round: 目标轮次
        
    Returns:
        bool: 回滚是否成功
    """
    return version_manager._rollback_to_version(target_round)


# 主程序
def main():
    setup_logging(log_level=logging.INFO)
    load_dotenv()
    
    # 设置基本配置
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../."))
    issue_id = 10  # 使用一个示例issue_id
    
    # 初始化必要组件
    log_config = LogConfig(project_dir=project_dir, issue_id=issue_id)
    log_manager = LogManager(config=log_config)
    
    git_config = GitConfig(repo_path=project_dir)
    git_manager = GitManager(config=git_config)
    
    ai_config = AIConfig(model_name="gpt-4o", temperature=0.7)
    
    # 初始化版本管理器
    version_manager = VersionManager(
        issue_id=issue_id, 
        ai_config=ai_config,
        log_manager=log_manager, 
        git_manager=git_manager
    )
    
    # 示例用户需求（包含回滚请求）
    user_requirement = """
    上一轮的代码实现有严重问题，请回滚到轮次1并重新实现特性X。
    我们需要确保新实现解决了之前遇到的性能瓶颈。
    """
    
    # 分析是否需要回滚
    print(f"分析需求是否需要回滚: {user_requirement[:50]}...")
    rollback_needed, target_round, integrated_req, reasoning = analyze_rollback_need(version_manager, user_requirement)
    
    print(f"分析结果: 需要回滚={rollback_needed}, 目标轮次={target_round}")
    print(f"分析原因: {reasoning[:100]}..." if reasoning and len(reasoning) > 100 else reasoning)
    
    # 如果需要回滚，执行回滚操作
    if rollback_needed and target_round is not None:
        print(f"执行回滚到轮次 {target_round}")
        success = execute_rollback(version_manager, target_round)
        print(f"回滚{'成功' if success else '失败'}")


if __name__ == "__main__":
    main()
