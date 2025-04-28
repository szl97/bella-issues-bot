import os
import re
from typing import List, Tuple

from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from core.ai import AIAssistant, AIConfig
from core.log_config import get_logger

logger = get_logger(__name__)

class DiffInfo(BaseModel):
    """存储diff信息的数据类"""
    file_name: str = ""  # 文件路径
    content: str = ""    # diff内容或新文件内容
    file_content: str = ""  # 文件的原始内容（如果是修改文件）
    is_create: bool = False  # 是否为新建文件
    is_modify: bool = False  # 是否为修改文件
    is_delete: bool = False  # 是否为删除文件


class Diff:
    """
    处理Git diff格式的工具类
    使用 AI 模型生成新文件内容
    """
    
    def __init__(self, ai_config: AIConfig):
        """
        初始化 Diff 类
        
        Args:
            ai_config: AI 配置
        """
        # 保存 AI 配置
        self.ai_config = ai_config
        
        # 保存原始系统提示词
        self.original_sys_prompt = ai_config.sys_prompt
        
        # 设置处理 diff 的系统提示词
        ai_config.sys_prompt = self._get_diff_system_prompt()
        
        # 初始化工具列表
        self.tools = [self._create_replace_file_tool()]
        
        # 创建 AI 助手
        self.ai_assistant = AIAssistant(config=ai_config, tools=self.tools)
    
    def __del__(self):
        """析构函数，恢复原始系统提示词"""
        self.ai_config.sys_prompt = self.original_sys_prompt

    @staticmethod
    def parse_diffs_from_text(text: str) -> List[Tuple[str, str, str]]:
        """
        从文本中提取所有文件修改信息

        Args:
            text: 包含文件修改信息的文本

        Returns:
            List[Tuple[str, str, str]]: 解析后的文件信息列表，每个元素为 (原文件路径, 新文件路径, diff内容)
        """
        diffs = []
        last_file_path = None  # 记录前一个文件的路径
        
        logger.info(f"开始解析文本中的 diff 信息，文本长度: {len(text)}")
        
        # 提取所有 ```diff 代码块
        diff_blocks = re.findall(r'```diff\s+(.*?)```', text, re.DOTALL)
        
        for diff_block in diff_blocks:
            if diff_block is None or diff_block == '':
                continue
            # 尝试从 diff 块中提取文件路径
            file_paths = re.findall(r'(?:---|\+\+\+)\s+(?:a/|b/)?([^\n\t]+)', diff_block)
            
            if len(file_paths) >= 2:
                file_path_pre = file_paths[0]
                file_path_post = file_paths[1]
                last_file_path = file_path_post  # 更新最后使用的文件路径
            elif len(file_paths) == 1:
                file_path_pre = file_paths[0]
                file_path_post = file_paths[0]
                last_file_path = file_path_post  # 更新最后使用的文件路径
            else:
                # 如果没有找到文件路径，尝试其他格式
                git_diff_match = re.search(r'diff --git a/(.*?) b/(.*?)[\n\r]', diff_block)
                if git_diff_match:
                    file_path_pre = git_diff_match.group(1)
                    file_path_post = git_diff_match.group(2)
                    last_file_path = file_path_post  # 更新最后使用的文件路径
                elif last_file_path:
                    # 如果没有找到文件路径，但有前一个文件的路径，则使用前一个文件的路径
                    logger.info(f"未找到文件路径，使用前一个文件的路径: {last_file_path}")
                    file_path_pre = last_file_path
                    file_path_post = last_file_path
                else:
                    # 如果仍然没有找到，使用默认名称
                    logger.warning(f"无法从 diff 块中提取文件路径，使用默认名称")
                    file_path_pre = "unknown_file.txt"
                    file_path_post = "unknown_file.txt"
                    last_file_path = file_path_post  # 更新最后使用的文件路径
            
            logger.info(f"找到 diff: {file_path_pre} -> {file_path_post}")
            diffs.append((file_path_pre, file_path_post, f'''diff\n{diff_block}\n'''))
        
        # 如果没有找到 diff 块，尝试提取文件路径和内容
        if not diffs:
            # 尝试提取文件路径和内容
            file_blocks = re.findall(r'```(?:.*?)\n(?:# )?(?:File|文件):\s*([^\n]+)\n(.*?)```', text, re.DOTALL)
            
            for file_path, file_content in file_blocks:
                file_path = file_path.strip()
                logger.info(f"找到文件内容: {file_path}")
                last_file_path = file_path  # 更新最后使用的文件路径
                diffs.append((file_path, file_path, file_content))
        
        # 如果仍然没有找到，尝试匹配任何代码块
        if not diffs:
            code_blocks = re.findall(r'```(?:.*?)\n(.*?)```', text, re.DOTALL)
            
            for i, content in enumerate(code_blocks):
                # 尝试从内容中提取文件路径
                file_path_match = re.search(r'(?:File|文件):\s*([^\n]+)', content)
                if file_path_match:
                    file_path = file_path_match.group(1).strip()
                    logger.info(f"从代码块内容中提取到文件路径: {file_path}")
                    last_file_path = file_path  # 更新最后使用的文件路径
                    diffs.append((file_path, file_path, content))
                elif last_file_path:
                    # 如果没有找到文件路径，但有前一个文件的路径，则使用前一个文件的路径
                    logger.info(f"未从代码块中提取到文件路径，使用前一个文件的路径: {last_file_path}")
                    diffs.append((last_file_path, last_file_path, content))
                else:
                    logger.warning(f"找到代码块但无法提取文件路径，将使用默认文件名: code_block_{i}.txt")
                    file_path = f"code_block_{i}.txt"
                    last_file_path = file_path  # 更新最后使用的文件路径
                    diffs.append((file_path, file_path, content))
        
        if not diffs:
            logger.warning("未找到任何有效的 diff 或文件内容")
            # 打印文本的前200个字符，帮助调试
            logger.debug(f"文本前200个字符: {text[:200]}")
        else:
            logger.info(f"共找到 {len(diffs)} 个文件修改信息")
        
        return diffs

    @staticmethod
    def extract_raw_diff_blocks(text: str) -> List[str]:
        """
        从文本中提取所有原始的diff代码块，包含```diff ```标识

        Args:
            text: 包含文件修改信息的文本

        Returns:
            List[str]: 所有提取到的原始diff块列表，包含```diff ```和``` 标记
        """
        
        # 提取所有 ```diff 开头，以 ``` 结尾的代码块（包含标记）
        pattern = r'(```diff[\s\S]*?```)'  
        raw_diff_blocks = re.findall(pattern, text)
        
        if not raw_diff_blocks:
            logger.warning("未找到任何原始diff代码块")
                
        return raw_diff_blocks

    def process_diffs(self, diffs: List[Tuple[str, str, str]], project_dir: str) -> tuple[List[str], List[DiffInfo]]:
        """
        处理 diff 列表，使用 AI 模型生成新文件内容
        将同一个文件的多个 diff 合并后一起请求模型

        Args:
            diffs: 解析后的文件信息列表，每个元素为 (原文件路径, 新文件路径, diff内容)
            project_dir: 项目根目录

        Returns:
            List[str]: 处理失败的文件列表
        """
        failed_files = []
        diff_infos = []
        
        # 按文件路径分组，合并同一文件的多个 diff
        file_diffs = {}
        for file_path_pre, file_path_post, content_or_diff in diffs:
            if file_path_post not in file_diffs:
                file_diffs[file_path_post] = []
            file_diffs[file_path_post].append((file_path_pre, content_or_diff))
        
        logger.info(f"将 {len(diffs)} 个 diff 合并为 {len(file_diffs)} 个文件的修改")

        # 处理每个文件的所有 diff
        for file_path_post, file_changes in file_diffs.items():
            try:
                full_path_post = os.path.join(project_dir, file_path_post)
                
                # 获取第一个 diff 的原文件路径（通常所有 diff 的原文件路径应该相同）
                file_path_pre = file_changes[0][0]
                full_path_pre = os.path.join(project_dir, file_path_pre)
                
                # 检查是否是新文件
                is_new_file = file_path_pre == "/dev/null" or not os.path.exists(full_path_pre)
                
                # 合并同一文件的所有 diff
                combined_diff = "\n".join([change[1] for change in file_changes])
                info = DiffInfo()
                info.file_name = file_path_post
                if is_new_file:
                    # 对于新文件，直接使用内容创建
                    if combined_diff.startswith("diff ") or combined_diff.startswith("--- ") or combined_diff.startswith("+++ ") or "\n@@" in combined_diff:
                        # 如果是 diff 格式，需要让模型生成完整内容
                        prompt = f"""
                        我需要根据以下 diff 信息创建一个新文件。
                        
                        diff 信息：
                        ```
                        {combined_diff}
                        ```
                        
                        请生成完整的文件内容，然后使用 replace_file 工具将内容写入文件 {full_path_post}。
                        """
                    else:
                        # 如果已经是完整内容，直接使用
                        prompt = f"""
                        请使用 replace_file 工具将以下内容写入文件 {full_path_post}：
                        
                        ```
                        {combined_diff}
                        ```
                        """
                    info.content = combined_diff
                    info.is_create = True
                else:
                    # 对于现有文件，读取原内容，让模型生成新内容
                    try:
                        with open(full_path_pre, "r", encoding="utf-8") as f:
                            original_content = f.read()
                        
                        # 如果有多个 diff，清晰地标记每个 diff
                        if len(file_changes) > 1:
                            diff_sections = []
                            for i, (_, diff_content) in enumerate(file_changes, 1):
                                diff_sections.append(f"Diff #{i}:\n{diff_content}")
                            formatted_diffs = "\n\n".join(diff_sections)
                        else:
                            formatted_diffs = combined_diff
                        
                        prompt = f"""
                        我需要根据 diff 信息修改一个文件。原文件内容如下：
                        ```
                        {original_content}
                        ```
                        
                        {"以下是多个需要应用的 diff，请按顺序应用所有修改：" if len(file_changes) > 1 else "diff 信息如下："}
                        ```
                        {formatted_diffs}
                        ```
                        
                        请根据原文件内容和 diff 信息，生成修改后的完整文件内容，然后使用 replace_file 工具将内容写入文件 {full_path_post}。
                        {"请确保应用所有的 diff 修改，并解决可能的冲突。" if len(file_changes) > 1 else ""}
                        """
                        info.file_content = original_content
                        info.content = formatted_diffs
                        info.is_modify = True
                    except Exception as e:
                        logger.error(f"读取原文件失败: {str(e)}")
                        failed_files.append(file_path_post)
                        continue

                # 调用 AI 模型处理
                logger.info(f"处理文件: {file_path_post} (包含 {len(file_changes)} 个 diff)")
                response = self.ai_assistant.generate_response(prompt, use_tools=True)
                
                # 检查响应中是否包含成功信息
                if "文件已更新:" not in response:
                    logger.warning(f"文件处理可能失败: {file_path_post}, 响应: {response}")
                    failed_files.append(file_path_post)
                else:
                    diff_infos.append(info)
                    logger.info(f"处理文件成功: {file_path_post}")
            except Exception as e:
                logger.error(f"处理文件失败: {file_path_post}, 错误: {str(e)}")
                failed_files.append(file_path_post)
        
        return (failed_files, diff_infos)

    def _replace_file(self, file_path: str, content: str) -> str:
        """
        替换或创建UTF-8编码的文本文件
        支持自动创建不存在的目录结构
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"文件已更新: {file_path}"
        except UnicodeEncodeError:
            return "错误：内容包含非UTF-8字符"
        except Exception as e:
            return f"操作失败: {str(e)}"


    class _ReplaceFileSchema(BaseModel):
        file_path: str = Field(
            ...,
            examples=["data/config.json"],
            description="文件的相对目录"
        )
        content: str = Field(
            ...,
            examples=["""
    def calculate_sum(a, b):
        return a + b
    
    if __name__ == '__main__':
        print(calculate_sum(3, 5))
    """],
            description="UTF-8编码的文本内容，最大支持10MB"
        )

    def _create_replace_file_tool(self) -> StructuredTool:
        """创建替换文件内容的工具"""
        return StructuredTool.from_function(
            func=self._replace_file,
            name="replace_file",
            description="替换或创建文件内容。输入应为文件路径和文件内容。",
            args_schema=self._ReplaceFileSchema,
            return_direct=True,
        )


    def _get_diff_system_prompt(self) -> str:
        """
        获取处理 diff 的系统提示词

        Returns:
            str: 系统提示词
        """
        return """你是一个专业的代码工程师助手，擅长根据 diff 信息修改文件。
    
    你将收到原始文件内容和 diff 信息，需要生成修改后的完整文件内容。
    
    使用以下工具来完成任务：
    1. replace_file: 用于替换或创建文件内容
    
    处理步骤：
    1. 分析原始文件内容和 diff 信息
    2. 生成修改后的完整文件内容
    3. 使用 replace_file 工具将内容写入文件
    
    注意事项：
    - 确保生成的文件内容是完整的，包含所有必要的代码
    - 一定不可以删除原文件中的未修改内容
    - 不要添加额外的注释或标记
    - 只修改 diff 中指定的部分，保持其他部分不变
    - 如果是新文件，直接生成完整的文件内容
    """

if __name__ == "__main__":
    load_dotenv()
    text = '''
'''
    diff = Diff(AIConfig(temperature=0.1,
              model_name="gpt-4o"))
    diff.process_diffs(Diff.parse_diffs_from_text(text), "../.")
