"""
本示例展示如何使用VersionManager进行代码版本管理和回滚操作

版本管理是代码生成中的重要环节，能够支持：
1. 历史记录的检索和格式化展示
2. 对用户需求进行分析，判断是否需要回滚
3. 执行代码版本回滚
4. 基于不同版本进行代码生成
"""

import logging
import os

from dotenv import load_dotenv

from core.ai import AIConfig
from core.code_engineer import CodeEngineerConfig, CodeEngineer
from core.diff import Diff
from core.file_memory import FileMemory, FileMemoryConfig
from core.git_manager import GitManager, GitConfig
from core.log_config import setup_logging
from core.log_manager import LogManager, LogConfig
from core.prompt_generator import PromptGenerator, PromptData
from core.version_manager import VersionManager


def main():
    """主函数：演示VersionManager的使用流程"""
    setup_logging(log_level=logging.INFO)
    # 加载环境变量
    load_dotenv()
    
    # 创建工作目录
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../."))

    # 设置issue_id (在实际应用中，这通常是从命令行参数或环境变量获取)
    issue_id = 10
    
    # 初始化日志管理器
    print("1. 初始化日志管理器")
    log_config = LogConfig(project_dir=project_dir, issue_id=issue_id)
    log_manager = LogManager(config=log_config)
    current_round = log_manager.get_current_round()
    print(f"   当前轮次: {current_round}")
    
    # 初始化Git管理器
    print("\n2. 初始化Git管理器")
    git_config = GitConfig(
        repo_path=project_dir,
        # 可以在这里设置远程仓库URL和认证令牌
        # remote_url="https://github.com/yourusername/yourrepo.git",
        # auth_token=os.getenv("GITHUB_TOKEN")
    )
    git_manager = GitManager(config=git_config)
    
    # 初始化AI助手
    print("\n3. 初始化AI配置")
    ai_config = AIConfig(
        model_name="gpt-4o",  # 根据需要修改模型名称
        temperature=0.7
    )
    
    # 初始化文件记忆管理器（如果需要）
    file_memory = None
    if current_round > 1:
        print("\n4. 初始化文件记忆管理器")
        file_memory = FileMemory(config=FileMemoryConfig(
            git_manager=git_manager, 
            ai_config=ai_config, 
            project_dir=project_dir,
            log_manager=log_manager
        ))
    
    # 初始化版本管理器
    print("\n5. 初始化版本管理器")
    version_manager = VersionManager(
        issue_id=issue_id, 
        ai_config=ai_config,
        log_manager=log_manager, 
        git_manager=git_manager,
        file_memory=file_memory
    )
    
    # 示例需求
    current_requirement = '''
    添加一个新功能：为版本管理器添加导出历史记录为JSON的功能。
    '''
    print(f"\n6. 当前需求: {current_requirement}")
    
    # 调用版本管理器处理需求
    print("\n7. 处理需求并获取历史记录")
    processed_requirement, history = version_manager.ensure_version_and_generate_context(current_requirement)
    
    # 输出处理后的需求和历史记录
    print(f"\n处理后的需求: {processed_requirement}")
    print(f"\n历史记录概览: {history[:200]}..." if len(history) > 200 else f"\n历史记录: {history}")
    
    # 展示如何手动回滚到特定版本
    if current_round > 1:
        print("\n8. 演示版本回滚功能")
        print("   注意: 此处只是演示，实际不执行回滚操作")
        print(f"   要回滚到轮次 1，您可以使用以下代码:")
        print("   success = version_manager._rollback_to_version(1)")
        
        # 获取格式化的历史记录
        print("\n9. 获取格式化的历史记录")
        formatted_history = version_manager.get_formatted_history()
        print(f"   历史记录长度: {len(formatted_history)} 字符")
        print(f"   历史记录预览: {formatted_history[:150]}..." if len(formatted_history) > 150 else formatted_history)
        
    # 使用版本管理器分析是否需要回滚
    print("\n10. 分析是否需要回滚")
    test_requirement = '''
    之前实现的版本管理功能有严重bug，请回滚到上一个轮次，重新实现版本管理功能。
    '''
    print(f"    测试需求: {test_requirement}")
    
    if current_round > 1:
        print("    调用version_manager._analyze_rollback_need分析是否需要回滚")
        print("    注意: 此处只是演示，不执行实际的分析操作")
        # rollback_needed, target_round, integrated_req, reasoning = version_manager._analyze_rollback_need(test_requirement)
        # print(f"    分析结果: 需要回滚={rollback_needed}, 目标轮次={target_round}")
        # print(f"    回滚原因: {reasoning[:100]}..." if reasoning and len(reasoning) > 100 else reasoning)
    else:
        print("    当前轮次为1，无法进行回滚分析")

    print("\n示例完成！")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"运行示例时发生错误: {str(e)}")
        raise
