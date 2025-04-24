import os
import logging
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass

from dotenv import load_dotenv

from core.ai import AIAssistant, AIConfig
from core.file_manager import FileManager
from core.git_manager import GitManager, GitConfig

logger = logging.getLogger(__name__)


@dataclass
class FileMemoryConfig:
    """配置文件记忆管理"""

    project_dir: str
    ai_config: AIConfig


class FileMemory:
    """管理文件描述的记忆"""

    MEMORY_DIR = ".gpteng/memory"
    FILE_DETAILS_PATH = f"{MEMORY_DIR}/file_details.txt"
    GIT_ID_FILE = f"{MEMORY_DIR}/git_id"
    CHUNK_SIZE = 10000  # 每次处理的最大行数

    def __init__(self, config: FileMemoryConfig):
        self.config = config
        self.memory_path = os.path.join(config.project_dir, self.FILE_DETAILS_PATH)
        self.git_id_path = os.path.join(config.project_dir, self.GIT_ID_FILE)

        # 初始化 AI 助手
        self.ai_assistant = AIAssistant(config=config.ai_config)

        # 初始化 Git 管理器
        self.git_manager = GitManager(GitConfig(repo_path=config.project_dir))

        # 确保内存目录存在
        os.makedirs(os.path.dirname(self.memory_path), exist_ok=True)

    def _read_file_details(self) -> Dict[str, str]:
        """读取文件描述信息"""
        if not os.path.exists(self.memory_path):
            return {}

        details = {}
        with open(self.memory_path, "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    filename, description = line.strip().split(":", 1)
                    details[filename] = description
        return details

    def _write_file_details(self, details: Dict[str, str]) -> None:
        """写入文件描述信息"""
        with open(self.memory_path, "w", encoding="utf-8") as f:
            for filename, description in sorted(details.items()):
                f.write(f"{filename}:{description}\n")

    def _read_git_id(self) -> str:
        """读取保存的 Git ID"""
        if not os.path.exists(self.git_id_path):
            return ""
        with open(self.git_id_path, "r") as f:
            return f.read().strip()

    def _write_git_id(self, git_id: str) -> None:
        """写入当前 Git ID"""
        with open(self.git_id_path, "w") as f:
            f.write(git_id)

    def _get_file_content(self, filepath: str) -> str:
        """获取文件内容"""
        try:
            full_path = os.path.join(self.config.project_dir, filepath)
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取文件 {filepath} 失败: {str(e)}")
            return ""

    def _generate_file_description(self, filepath: str, content: str) -> str:
        """使用 AI 生成文件描述"""
        prompt = f"""
请分析下面的代码文件，并生成一个简短的中文描述（不超过100字）。
描述应该包含：
1. 文件的主要功能
2. 包含的关键类或函数
3. 与其他文件的主要交互（如果明显的话）

文件路径: {filepath}

代码内容:
{content}

请直接返回描述文本，不要包含其他内容。
"""
        try:
            response = self.ai_assistant.generate_response(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"生成文件 {filepath} 的描述失败: {str(e)}")
            return "文件描述生成失败"

    def _process_files_chunk(self, files: List[str]) -> Dict[str, str]:
        """处理一组文件，生成描述"""
        descriptions = {}
        current_lines = 0
        current_batch = []

        for filepath in files:
            content = self._get_file_content(filepath)
            lines = len(content.splitlines())

            if current_lines + lines > self.CHUNK_SIZE:
                # 处理当前批次
                for batch_file in current_batch:
                    batch_content = self._get_file_content(batch_file)
                    descriptions[batch_file] = self._generate_file_description(
                        batch_file, batch_content
                    )

                # 重置批次
                current_batch = [filepath]
                current_lines = lines
            else:
                current_batch.append(filepath)
                current_lines += lines

        # 处理最后一个批次
        for batch_file in current_batch:
            batch_content = self._get_file_content(batch_file)
            descriptions[batch_file] = self._generate_file_description(
                batch_file, batch_content
            )

        return descriptions

    def update_file_details(self) -> None:
        """更新文件描述信息"""
        # 获取当前的 Git ID
        current_git_id = self.git_manager.get_current_commit_id()
        saved_git_id = self._read_git_id()

        # 获取所有文件
        all_files = FileManager.get_all_files_without_ignore(self.config.project_dir)

        # 读取现有描述
        existing_details = self._read_file_details()

        if saved_git_id:
            # 获取变更的文件
            changed_files = set(
                self.git_manager.get_changed_files(saved_git_id, current_git_id)
            )
            new_files = all_files - set(existing_details.keys())
            files_to_process = list(changed_files | new_files)

            # 删除不存在的文件的描述
            existing_details = {
                k: v for k, v in existing_details.items() if k in all_files
            }
        else:
            # 首次运行，处理所有文件
            files_to_process = list(all_files)

        # 处理需要更新的文件
        if files_to_process:
            new_descriptions = self._process_files_chunk(files_to_process)
            existing_details.update(new_descriptions)

        # 保存结果
        self._write_file_details(existing_details)
        self._write_git_id(current_git_id)

    @classmethod
    def get_file_descriptions(cls, project_dir: str) -> Dict[str, str]:
        """获取文件描述的静态方法"""
        memory_path = os.path.join(project_dir, cls.FILE_DETAILS_PATH)

        if not os.path.exists(memory_path):
            return {}

        try:
            descriptions = {}
            with open(memory_path, "r", encoding="utf-8") as f:
                for line in f:
                    if ":" in line:
                        filename, description = line.strip().split(":", 1)
                        descriptions[filename] = description
            return descriptions
        except Exception as e:
            logger.error(f"读取文件描述失败: {str(e)}")
            return {}


if __name__ == "__main__":
    load_dotenv()
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../."))
    memory = FileMemory(FileMemoryConfig(project_dir, ai_config=AIConfig(
        temperature=0.7,
        model_name="claude-3.5-sonnet"
    )))

    memory.update_file_details()