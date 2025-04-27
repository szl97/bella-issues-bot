import os
from copy import copy
from dataclasses import dataclass

from dotenv import load_dotenv
from typing_extensions import Optional

from core.ai import AIAssistant, AIConfig
from core.diff import Diff
from core.log_manager import LogManager, LogConfig
from log_config import get_logger

logger = get_logger(__name__)


@dataclass
class CodeEngineerConfig:
    """代码工程师配置"""
    project_dir: str
    ai_config: AIConfig
    system_prompt: Optional[str] = None
    max_retries: int = 3


class CodeEngineer:
    """
    代码工程师类，负责处理用户的 prompt，与 AI 模型交互，解析 diff 并修改文件
    """

    def __init__(self, config: CodeEngineerConfig, log_manager: LogManager, diff: Diff):
        """
        初始化代码工程师

        Args:
            config: CodeEngineerConfig 实例，包含必要的配置信息
            log_manager: LogManager 实例，用于日志管理
        """
        self.config = config
        self.log_manager = log_manager
        self.diff = diff


        if config.system_prompt:
            self.system_prompt = config.system_prompt
        else:
            # 读取系统提示词
            self.system_prompt = self._read_system_prompt()

        self.ai_config = copy(config.ai_config)
        self.ai_config.sys_prompt = self.system_prompt
        self.ai_assistant = AIAssistant(config=self.ai_config)
        # 用于存储处理失败的文件
        self.failed_files = []

    def _read_system_prompt(self) -> str:
        """
        读取系统提示词

        Returns:
            str: 系统提示词内容
        """
        try:
            system_prompt_path = os.path.join(self.config.project_dir, "system.txt")
            if os.path.exists(system_prompt_path):
                with open(system_prompt_path, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                logger.warning(f"系统提示词文件不存在: {system_prompt_path}，使用默认提示词")
                return "You will get instructions for code to write. Output requested code changes in the unified git diff syntax."
        except Exception as e:
            logger.error(f"读取系统提示词失败: {str(e)}")
            return "You will get instructions for code to write. Output requested code changes in the unified git diff syntax."

    def process_prompt(self, prompt: str) ->  tuple[bool, Optional[str]]:
        """
        处理用户的 prompt，与 AI 模型交互，解析 diff 并修改文件

        Args:
            prompt: 用户的 prompt

        Returns:
            bool: 处理是否成功
            str: 模型返回结果
        """
        try:
            # 重置失败文件列表
            self.failed_files = []
            
            # 设置 AI 助手的系统提示词
            self.ai_assistant.config.sys_prompt = self.system_prompt
            
            # 调用 AI 模型生成响应
            response = self.ai_assistant.generate_response(prompt)
            
            # 解析响应中的 diff
            diffs = Diff.parse_diffs_from_text(response)
            
            if not diffs:
                logger.warning("未找到有效的 diff")
                return (False, None)
            
            # 处理每个 diff
            self.failed_files = self.diff.process_diffs(diffs, self.config.project_dir)
            
            # 归档日志
            self.log_manager.archive_logs(
                sys_prompt=self.system_prompt,
                prompt=prompt,
                response=response
            )
            
            # 如果有失败的文件，可以在这里处理
            if self.failed_files:
                logger.warning(f"有 {len(self.failed_files)} 个文件处理失败")
                # 这里可以添加失败文件的重试逻辑，但根据需求，暂时不实现
                return (False, response)
            
            return (True, response)
        except Exception as e:
            logger.error(f"处理 prompt 失败: {str(e)}")
            return (False, None)

    def retry_failed_files(self, ) -> bool:
        """
        重试处理失败的文件（钩子方法，暂不实现具体逻辑）

        Args:
            prompt: 用户的 prompt

        Returns:
            bool: 重试是否成功
        """
        # 这是一个钩子方法，用于未来扩展
        # 根据需求，暂时不实现具体逻辑

        return False

if __name__ == "__main__":
    load_dotenv()
    prompt = '''
    '''
    config = CodeEngineerConfig(project_dir="../.", ai_config=AIConfig(
        temperature=1,
        model_name="claude-3.7-sonnet"
    ))

    engineer = CodeEngineer(config, LogManager(LogConfig("../.", 1)), Diff(AIConfig(temperature=0.1,
                                                                                 model_name="gpt-4o")))
    engineer.process_prompt(prompt)
