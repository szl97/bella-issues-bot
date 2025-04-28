import logging
import os

from dotenv import load_dotenv

from core.ai import AIConfig
from core.code_engineer import CodeEngineerConfig, CodeEngineer
from core.diff import Diff
from core.file_memory import FileMemory, FileMemoryConfig
from core.file_selector import FileSelector
from core.git_manager import GitManager, GitConfig
from core.log_config import setup_logging
from core.log_manager import LogManager, LogConfig
from core.prompt_generator import PromptGenerator, PromptData
from core.version_manager import VersionManager


def main():
    setup_logging(log_level=logging.DEBUG)
    # 加载环境变量
    load_dotenv()
    
    # 创建工作目录
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../."))

    issue_id = 3
    
    # 初始化日志管理器
    log_config = LogConfig(project_dir=project_dir, issue_id=issue_id)
    log_manager = LogManager(config=log_config)
    current_round = log_manager.get_current_round()

    
    # 初始化Git管理器
    git_config = GitConfig(
        repo_path=project_dir
    )
    git_manager = GitManager(config=git_config)
    
    # 初始化AI助手
    ai_config = AIConfig(
        model_name="coder-model",
        temperature=1
    )
    
    # 初始化版本管理器
    version_manager = VersionManager(issue_id=issue_id, log_manager=log_manager, git_manager=git_manager, ai_config=ai_config)

    current_requirement = '''
    将 example_chat_process.py 和 example_code_generate.py的流程整合到 workflow_engine.py 中，目前两个代码文件都是写代码和回复用户的完整流程。
    使用DecisionEnvironment来决策选择何种模式。
    '''
    requirement, history = version_manager.ensure_version_and_generate_context(current_requirement)

    if current_round > 1:
        file_memory = FileMemory(config=FileMemoryConfig(git_manager=git_manager, ai_config=ai_config, project_dir=project_dir))
        file_memory.update_file_details()

    selector = FileSelector(
        project_dir,
        issue_id,
        ai_config=ai_config,
    )

    files = selector.select_files_for_requirement(requirement)

    descriptions = FileMemory.get_selected_file_descriptions(project_dir, files)

    data = PromptData(requirement=requirement, project_dir=project_dir, steps = history, files=files, file_desc=descriptions)
    user_prompt = PromptGenerator.generatePrompt(data)
    config = CodeEngineerConfig(project_dir=project_dir, ai_config=ai_config)

    engineer = CodeEngineer(config, LogManager(LogConfig(project_dir=project_dir, issue_id=issue_id)), Diff(AIConfig(temperature=0.1,
                                                                                                              model_name="gpt-4o")))
    engineer.process_prompt(prompt=user_prompt)


if __name__ == "__main__":
    main()
