"""
这个示例展示如何使用WorkflowEngine处理用户需求，自动决策是代码生成还是对话流程
"""
import logging
import os

from dotenv import load_dotenv

from core.workflow_engine import WorkflowEngine, WorkflowEngineConfig
from core.log_config import setup_logging


def main():
    setup_logging(log_level=logging.DEBUG)
    # 加载环境变量
    load_dotenv()
    
    # 创建工作目录
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../."))
    issue_id = 5
    
    # 创建工作流引擎配置
    config = WorkflowEngineConfig(
        project_dir=project_dir,
        issue_id=issue_id,
        core_model="coder-model",
        data_model="gpt-4o",
        core_template=1,
        data_template=0.7,
        default_branch="dev"
    )
    
    # 初始化工作流引擎
    workflow_engine = WorkflowEngine(config)

    requirement = """
    分析项目的所有代码。把项目的Read.me进行完善。尤其是未完成的。
    """
    
    # 处理代码修改需求
    workflow_engine.process_requirement(requirement)

if __name__ == "__main__":
    main()
