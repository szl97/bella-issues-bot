"""
这个示例展示如何使用ChatProcessor处理用户对话需求
与example_generate.py不同之处在于：
1. 不需要使用版本管理
2. 使用ChatProcessor替代CodeEngineer
"""

import os

from dotenv import load_dotenv

from core.ai import AIConfig
from core.chat_processor import ChatProcessor, ChatProcessorConfig
from core.file_memory import FileMemory, FileMemoryConfig
from core.file_selector import FileSelector
from core.git_manager import GitManager, GitConfig, get_issues_branch_name
from core.log_manager import LogManager, LogConfig


def main():
    # 加载环境变量
    load_dotenv()
    
    # 创建工作目录
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../."))

    issue_id = 5  # 使用一个新的issue_id
    
    # 初始化日志管理器
    log_config = LogConfig(project_dir=project_dir, issue_id=issue_id)
    log_manager = LogManager(config=log_config)
    current_round = log_manager.get_current_round()

    
    # 初始化Git管理器
    git_config = GitConfig(
        repo_path=project_dir
    )
    git_manager = GitManager(config=git_config)
    branch_name = get_issues_branch_name(issue_id, current_round)
    
    # 初始化AI助手
    ai_config = AIConfig(
        model_name="coder-model",
        temperature=1
    )
    
    current_requirement = '''
    请详细解释下工作流引擎(workflow_engine)在本项目中的作用，以及它是如何协调各个组件工作的
    '''

    if current_round > 1:
        file_memory = FileMemory(config=FileMemoryConfig(git_manager=git_manager, ai_config=ai_config, project_dir=project_dir))
        file_memory.update_file_details()

    git_manager.switch_branch(branch_name, True)

    selector = FileSelector(
        project_dir,
        issue_id,
        ai_config=ai_config,
    )

    # 选择相关文件来提供上下文
    files = selector.select_files_for_requirement(current_requirement)
    descriptions = FileMemory.get_selected_file_descriptions(project_dir, files)

    # 使用ChatProcessor处理用户请求
    chat_config = ChatProcessorConfig(
        system_prompt="你是一个项目助手，负责回答关于代码库的问题。下面会给出用户的问题以及相关的项目文件信息。"
    )
    chat_processor = ChatProcessor(ai_config=ai_config, log_manager=log_manager, config=chat_config)
    
    logger.info(chat_processor.process_chat(current_requirement))


if __name__ == "__main__":
    main()
