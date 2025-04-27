"""
这个示例展示如何使用WorkflowEngine处理用户需求，自动决策是代码生成还是对话流程
"""
import logging
import os

from dotenv import load_dotenv

from core.workflow_engine import WorkflowEngine, WorkflowEngineConfig
from core.log_config import setup_logging


def main():
    setup_logging(log_level=logging.DEBUG, log_dir="../logs")
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
        data_template=0.7
    )
    
    # 初始化工作流引擎
    workflow_engine = WorkflowEngine(config)

    requirement = """
    - **客户端模式 (client)**：默认模式，适合作为个人开发助手使用，每次运行时基于project_dir目录下的当前代码状态进行操作。
    - **机器人模式 (bot)**：专为GitHub集成设计，会在project_dir目录下创建临时目录作为project_dir，自动拉取issues对应的最新分支状态，处理完成后自动提交更改并在Issues中回复处理结果，并且删除当前工作区。
    这个功能还没实现，在workflow_engine.py中实现
    """
    
    # 处理代码修改需求
    workflow_engine.process_requirement(requirement)

if __name__ == "__main__":
    main()
