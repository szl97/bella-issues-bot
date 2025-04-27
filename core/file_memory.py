import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Dict, List

from dotenv import load_dotenv
from langchain.tools import Tool

from core.ai import AIAssistant, AIConfig
from core.file_fetcher import FileFetcher
from core.git_manager import GitManager, GitConfig

logger = logging.getLogger(__name__)


@dataclass
class FileMemoryConfig:
    """配置文件记忆管理"""
    project_dir: str
    ai_config: AIConfig
    git_manager: GitManager


class FileMemory:
    """管理文件描述的记忆"""

    MEMORY_DIR = ".eng/memory"
    FILE_DETAILS_PATH = f"{MEMORY_DIR}/file_details.txt"
    GIT_ID_FILE = f"{MEMORY_DIR}/git_id"
    MAX_RETRIES = 3    # 最大重试次数
    RETRY_DELAY = 30    # 重试延迟（秒）
    # 每批次最大行数和字符数限制
    MAX_LINES_PER_BATCH = 10000  # 最大行数
    MAX_CHARS_PER_BATCH = 100000  # 最大字符数，约为 100KB
    MAX_FILES_PER_BATCH = 100  # 每批次最多处理的文件数

    def __init__(self, config: FileMemoryConfig):
        self.config = config
        self.memory_path = os.path.join(config.project_dir, self.FILE_DETAILS_PATH)
        self.git_id_path = os.path.join(config.project_dir, self.GIT_ID_FILE)

        # 初始化 AI 助手
        self.ai_assistant = AIAssistant(config=self.config.ai_config, tools=[self._create_batch_description_tool()])

        # 初始化 Git 管理器
        self.git_manager = self.config.git_manager

        # 确保内存目录存在
        os.makedirs(os.path.dirname(self.memory_path), exist_ok=True)

    def _ensure_directories(self):
        """确保必要的目录存在"""
        memory_dir = os.path.join(self.config.project_dir, self.MEMORY_DIR)
        os.makedirs(memory_dir, exist_ok=True)

    def _get_failed_files_path(self) -> str:
        """获取失败文件记录的路径"""
        return os.path.join(self.config.project_dir, self.MEMORY_DIR, "failed_files.json")

    def _read_failed_files(self) -> List[str]:
        """读取处理失败的文件列表"""
        failed_files_path = self._get_failed_files_path()
        if os.path.exists(failed_files_path):
            try:
                with open(failed_files_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"读取失败文件列表出错: {str(e)}")
        return []

    def _write_failed_files(self, failed_files: List[str]) -> None:
        """写入处理失败的文件列表"""
        failed_files_path = self._get_failed_files_path()
        try:
            with open(failed_files_path, 'w', encoding='utf-8') as f:
                json.dump(failed_files, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"写入失败文件列表出错: {str(e)}")

    def _create_batch_description_tool(self) -> Tool:
        """创建批量生成文件描述的工具"""
        from langchain.tools import Tool
        
        def process_file_descriptions(file_descriptions: str) -> Dict[str, str]:
            """
            处理文件描述列表
            
            Args:
                file_descriptions: JSON格式的文件描述列表，格式为 [{"fileName": "path/to/file.py", "desc": "文件描述"}]
                
            Returns:
                Dict[str, str]: 文件路径到描述的映射
            """
            try:
                descriptions = {}
                file_list = json.loads(file_descriptions)
                
                if not isinstance(file_list, list):
                    logger.error("错误：输入必须是一个列表")
                    return descriptions
                
                # 处理结果
                for item in file_list:
                    if isinstance(item, dict) and "fileName" in item and "desc" in item:
                        descriptions[item["fileName"]] = item["desc"]
                    else:
                        logger.warning(f"跳过无效的文件描述项: {item}")
                
                logger.info(f"成功处理了 {len(descriptions)} 个文件描述")
                return descriptions
            except json.JSONDecodeError:
                logger.error("错误：输入不是有效的 JSON 格式")
                return {}
            except Exception as e:
                logger.error(f"处理文件描述时出错: {str(e)}")
                return {}
        
        return Tool(
            name="process_file_descriptions",
            description="处理文件描述列表，输入必须是JSON格式的列表，每个元素包含fileName和desc字段",
            func=process_file_descriptions,
            return_direct=True
        )

    def _generate_batch_file_descriptions(self, files_with_content: List[Dict[str, str]]) -> Dict[str, str]:
        """
        批量生成文件描述
        
        Args:
            files_with_content: 包含文件路径和内容的列表，格式为 [{"filepath": "path/to/file.py", "content": "..."}]
            
        Returns:
            Dict[str, str]: 文件路径到描述的映射
        """
        # 构建提示词
        files_text = ""
        for i, file_info in enumerate(files_with_content):
            files_text += f"\n--- 文件 {i+1}: {file_info['filepath']} ---\n{file_info['content']}\n"
        
        prompt = f"""
请分析以下多个代码文件，并为每个文件生成一个简短的中文描述（每个不超过100字）。
描述应该包含：
1. 文件的主要功能
2. 包含的关键类或函数
3. 与其他文件的主要交互（如果明显的话）

{files_text}

请使用process_file_descriptions工具返回结果，输入必须是一个JSON格式的列表，每个元素包含fileName和desc字段。
例如：
[
  {{"fileName": "path/to/file1.py", "desc": "这个文件实现了..."}},
  {{"fileName": "path/to/file2.py", "desc": "这个文件定义了..."}}
]

请确保每个文件都有对应的描述，并且描述准确反映文件的功能和内容。
"""
        
        # 尝试生成描述，最多重试MAX_RETRIES次
        descriptions = {}
        failed_files = []
        file_paths = [file_info["filepath"] for file_info in files_with_content]
        
        for attempt in range(self.MAX_RETRIES):
            try:
                logger.info(f"尝试批量生成文件描述（第{attempt+1}次尝试）")
                
                # 使用工具生成描述
                descriptions = self.ai_assistant.generate_response(prompt, use_tools=True)
                
                # 如果返回的不是字典，可能是字符串响应
                if not isinstance(descriptions, dict):
                    logger.error(f"工具返回了非预期的结果类型: {type(descriptions)}")
                    descriptions = {}
                
                # 检查是否所有文件都有描述
                missing_files = [
                    file_path for file_path in file_paths
                    if file_path not in descriptions
                ]
                
                if missing_files:
                    failed_files.extend(missing_files)
                    logger.warning(f"以下文件未能生成描述: {missing_files}")
                
                # 如果有成功处理的文件，则返回结果
                if descriptions:
                    return descriptions
            
            except Exception as e:
                logger.error(f"批量生成文件描述失败（第{attempt+1}次尝试）: {str(e)}")
            
            # 如果不是最后一次尝试，则等待后重试
            if attempt < self.MAX_RETRIES - 1:
                logger.info(f"等待 {self.RETRY_DELAY} 秒后重试...")
                time.sleep(self.RETRY_DELAY)
        
        # 所有尝试都失败，记录失败的文件
        self._update_failed_files(file_paths)
        
        # 返回空结果
        return descriptions

    def _update_failed_files(self, new_failed_files: List[str]) -> None:
        """更新失败文件列表"""
        if not new_failed_files:
            return
            
        # 读取现有失败文件列表
        existing_failed_files = self._read_failed_files()
        
        # 合并并去重
        all_failed_files = list(set(existing_failed_files + new_failed_files))
        
        # 写入更新后的列表
        self._write_failed_files(all_failed_files)
        logger.info(f"更新了失败文件列表，共 {len(all_failed_files)} 个文件")

    def process_failed_files(self) -> Dict[str, str]:
        """处理之前失败的文件"""
        failed_files = self._read_failed_files()
        if not failed_files:
            logger.info("没有需要处理的失败文件")
            return {}
            
        logger.info(f"开始处理 {len(failed_files)} 个失败文件")
        
        # 准备文件内容
        files_with_content = []
        for filepath in failed_files:
            content = self._get_file_content(filepath)
            if content.strip():  # 跳过空文件
                files_with_content.append({"filepath": filepath, "content": content})
        
        # 按批次处理文件
        descriptions = self._process_files_in_batches(files_with_content)
        
        # 更新失败文件列表
        if descriptions:
            # 找出成功处理的文件
            processed_files = list(descriptions.keys())
            # 更新失败文件列表
            new_failed_files = [f for f in failed_files if f not in processed_files]
            self._write_failed_files(new_failed_files)
            
            logger.info(f"成功处理了 {len(processed_files)} 个之前失败的文件，还有 {len(new_failed_files)} 个文件失败")
        
        return descriptions


    def _get_file_content(self, filepath: str) -> str:
        """获取文件内容"""
        try:
            full_path = os.path.join(self.config.project_dir, filepath)
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取文件 {filepath} 失败: {str(e)}")
            return ""

    def _process_files_in_batches(self, files_with_content: List[Dict[str, str]]) -> Dict[str, str]:
        """将文件分批处理"""
        all_descriptions = {}
        current_batch = []
        current_lines = 0
        current_size = 0

        
        for file_info in files_with_content:
            content = file_info["content"]
            lines = len(content.splitlines())
            chars = len(content)
            
            if lines == 0:
                continue
                
            # 检查是否需要开始新批次
            # 如果当前批次已满或添加此文件会超出限制，则处理当前批次并开始新批次
            if (current_batch and (
                len(current_batch) >= self.MAX_FILES_PER_BATCH or
                current_lines + lines > self.MAX_LINES_PER_BATCH or
                current_size + chars > self.MAX_CHARS_PER_BATCH
            )):
                # 处理当前批次
                logger.info(f"处理批次: {len(current_batch)} 个文件，共 {current_lines} 行，{current_size} 字符")
                batch_descriptions = self._generate_batch_file_descriptions(current_batch)
                all_descriptions.update(batch_descriptions)
                
                # 重置批次
                current_batch = [file_info]
                current_lines = lines
                current_size = chars
            else:
                current_batch.append(file_info)
                current_lines += lines
                current_size += chars
        
        # 处理最后一个批次
        if current_batch:
            logger.info(f"处理最后一个批次: {len(current_batch)} 个文件，共 {current_lines} 行，{current_size} 字符")
            batch_descriptions = self._generate_batch_file_descriptions(current_batch)
            all_descriptions.update(batch_descriptions)
        
        return all_descriptions

    def _process_files_chunk(self, files: List[str]) -> Dict[str, str]:
        """处理一组文件，生成描述"""
        # 准备文件内容
        files_with_content = []
        for filepath in files:
            content = self._get_file_content(filepath)
            if content.strip():  # 跳过空文件
                files_with_content.append({"filepath": filepath, "content": content})
        
        # 按批次处理文件
        return self._process_files_in_batches(files_with_content)

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

    def update_file_details(self) -> None:
        """更新文件描述信息"""
        # 获取当前的 Git ID
        current_git_id = self.git_manager.get_current_commit_id()
        saved_git_id = self._read_git_id()

        # 获取所有文件
        all_files = FileFetcher.get_all_files_without_ignore(self.config.project_dir)

        # 读取现有描述
        existing_details = self._read_file_details()

        if saved_git_id:
            # 获取变更的文件
            changed_files = set(
                self.git_manager.get_changed_files(saved_git_id, current_git_id)
            ) & all_files
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

    @classmethod
    def get_selected_file_descriptions(cls, project_dir: str, files: List[str]) -> Dict[str, str]:
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
                        if filename in files:
                            descriptions[filename] = description
            return descriptions
        except Exception as e:
            logger.error(f"读取文件描述失败: {str(e)}")
            return {}

if __name__ == "__main__":
    load_dotenv()
    project_dir = "../."
    memory = FileMemory(
        FileMemoryConfig(
            ai_config=AIConfig(temperature=1, model_name="claude-3.7-sonnet"),
            git_manager=GitManager(config=GitConfig(project_dir))
        )
    )

    memory.update_file_details()
