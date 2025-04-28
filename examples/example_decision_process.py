"""
本示例展示如何使用DecisionProcess进行需求分析和决策

DecisionProcess能够分析用户需求并确定处理流程：
1. 判断需求是否需要修改代码
2. 提供分析结果和推理过程
3. 帮助系统决定使用代码生成流程还是对话流程
"""

import logging
import os

from dotenv import load_dotenv

from core.ai import AIConfig
from core.decision import DecisionProcess, DecisionResult
from core.git_manager import GitManager, GitConfig
from core.log_config import setup_logging, get_logger
from core.log_manager import LogManager, LogConfig
from core.version_manager import VersionManager

logger = get_logger(__name__)


def main():
    """主函数：演示DecisionProcess的使用流程"""
    setup_logging(log_level=logging.INFO)
    # 加载环境变量
    load_dotenv()
    
    # 创建工作目录
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../."))

    # 设置issue_id
    issue_id = 20
    
    # 初始化必要组件
    log_config = LogConfig(project_dir=project_dir, issue_id=issue_id)
    log_manager = LogManager(config=log_config)
    
    git_config = GitConfig(repo_path=project_dir)
    git_manager = GitManager(config=git_config)
    
    ai_config = AIConfig(
        model_name="gpt-4o",
        temperature=0.7
    )
    
    # 初始化版本管理器 (DecisionProcess需要)
    version_manager = VersionManager(
        issue_id=issue_id,
        log_manager=log_manager,
        git_manager=git_manager,
        ai_config=ai_config
    )
    
    # 初始化决策分析器
    print("\n1. 初始化决策分析器")
    decision_process = DecisionProcess(
        ai_config=ai_config,
        version_manager=version_manager
    )
    
    # 准备示例需求
    example_requirements = [
        # 需要修改代码的需求
        "在项目中添加一个新的模块，用于处理用户配置文件",
        "修复file_memory.py中的内存泄漏问题",
        "将log_manager模块重构为单例模式",
        "把这两个文件合并成一个吧：example_chat_process.py和example_code_generate.py",
        # 不需要修改代码的需求
        "请解释一下workflow_engine.py的主要功能",
        "你能告诉我如何使用version_manager吗？",
        "为什么决策模块需要用到AI助手？",
        "代码中的AIConfig和LLMConfig有什么区别？"
    ]
    
    # 分析每个示例需求
    print("\n2. 开始分析示例需求")
    for i, requirement in enumerate(example_requirements):
        print(f"\n示例 {i+1}: {requirement}")
        
        # 使用决策分析器分析需求
        result: DecisionResult = decision_process.analyze_requirement(requirement)
        
        # 输出分析结果
        result_type = "需要修改代码" if result.needs_code_modification else "只需要对话回答"
        print(f"分析结果: {result_type}")
        print(f"分析理由: {result.reasoning}")
        
        # 基于分析结果选择处理流程
        if result.needs_code_modification:
            print("-> 应使用CodeEngineer处理")
        else:
            print("-> 应使用ChatProcessor处理")

if __name__ == "__main__":
    main()
