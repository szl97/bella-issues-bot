"""
高级示例：决策流程与工作流集成

演示如何将DecisionProcess集成到自定义工作流中，实现智能路由需求处理
"""

import logging
import os
from typing import Dict, Any

from dotenv import load_dotenv

from core.ai import AIConfig
from core.chat_processor import ChatProcessor, ChatProcessorConfig
from core.code_engineer import CodeEngineer, CodeEngineerConfig
from core.decision import DecisionProcess
from core.diff import Diff
from core.git_manager import GitManager, GitConfig
from core.log_config import setup_logging, get_logger
from core.log_manager import LogManager, LogConfig
from core.version_manager import VersionManager

logger = get_logger(__name__)


class SmartWorkflowHandler:
    """智能工作流处理器，根据决策结果选择合适的处理流程"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化智能工作流处理器"""
        self.project_dir = config.get('project_dir')
        self.issue_id = config.get('issue_id')
        
        # 初始化基础组件
        log_config = LogConfig(project_dir=self.project_dir, issue_id=self.issue_id)
        self.log_manager = LogManager(config=log_config)
        
        git_config = GitConfig(repo_path=self.project_dir)
        self.git_manager = GitManager(config=git_config)
        
        self.ai_config = AIConfig(
            model_name=config.get('model_name', 'gpt-4o'),
            temperature=config.get('temperature', 0.7)
        )
        
        # 初始化版本管理器
        self.version_manager = VersionManager(
            issue_id=self.issue_id,
            log_manager=self.log_manager,
            git_manager=self.git_manager,
            ai_config=self.ai_config
        )
        
        # 初始化决策处理器
        self.decision_process = DecisionProcess(
            ai_config=self.ai_config,
            version_manager=self.version_manager
        )
        
        # 创建处理器
        self.code_engineer = CodeEngineer(
            config=CodeEngineerConfig(project_dir=self.project_dir, ai_config=self.ai_config),
            log_manager=self.log_manager,
            diff_helper=Diff(AIConfig(temperature=0.1, model_name="gpt-4o"))
        )
        
        self.chat_processor = ChatProcessor(
            ai_config=self.ai_config, 
            log_manager=self.log_manager,
            config=ChatProcessorConfig(
                system_prompt="你是一个项目助手，负责回答关于代码库的问题。"
            )
        )
    
    def process_requirement(self, requirement: str) -> str:
        """处理用户需求，自动选择合适的流程"""
        logger.info(f"开始处理需求: {requirement[:50]}...")
        
        # 使用决策处理器分析需求
        decision_result = self.decision_process.analyze_requirement(requirement)
        
        logger.info(f"决策结果: {'代码修改' if decision_result.needs_code_modification else '对话处理'}")
        logger.info(f"决策理由: {decision_result.reasoning}")
        
        # 根据决策结果选择适当的处理器
        if decision_result.needs_code_modification:
            # 需要修改代码，使用CodeEngineer
            return "代码修改流程已启动，正在处理..."
        else:
            # 只需回答问题，使用ChatProcessor
            return self.chat_processor.process_chat(requirement)


# 示例使用
def main():
    setup_logging(log_level=logging.INFO)
    load_dotenv()
    
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../."))
    
    workflow_handler = SmartWorkflowHandler({
        'project_dir': project_dir,
        'issue_id': 25,
        'model_name': 'gpt-4o',
        'temperature': 0.7
    })
    
    # 测试不同类型的需求
    code_requirement = "增加一个新的日志级别，用于调试复杂问题"
    chat_requirement = "请解释一下版本管理器的回滚机制是如何工作的"
    
    print("\n处理代码修改需求:")
    result1 = workflow_handler.process_requirement(code_requirement)
    print(f"处理结果: {result1}\n")
    
    print("\n处理对话类需求:")
    result2 = workflow_handler.process_requirement(chat_requirement)
    print(f"处理结果: {result2[:100]}..." if len(result2) > 100 else f"处理结果: {result2}")


if __name__ == "__main__":
    main()
