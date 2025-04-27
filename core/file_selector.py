import os
from typing import List, Optional, Set

from dotenv import load_dotenv
from langchain.tools import Tool

from core.ai import AIAssistant, AIConfig
from core.file_fetcher import FileFetcher
from core.file_memory import FileMemory
from log_config import get_logger

logger = get_logger(__name__)

class FileSelector:
    """
    使用 AI 辅助选择实现特定功能所需的文件
    """

    def __init__(self, project_dir: str, issues_id: int, ai_config: Optional[AIConfig] = None):
        """
        初始化 FileSelector
        
        Args:
            project_dir: 项目根目录
            ai_config: AI 配置，如果为 None 则使用默认配置
        """
        self.project_dir = project_dir
        self.issues_id = issues_id
        self.ai_config = ai_config or AIConfig()
        
        # 创建 AI 助手和工具
        self.select_files_tool = self._create_select_files_tool()
        self.ai_assistant = AIAssistant(
            config=self.ai_config,
            tools=[self.select_files_tool]
        )
    
    def _create_select_files_tool(self) -> Tool:
        """创建选择文件的工具"""
        def select_files(file_list: str) -> str:
            """
            选择指定的文件
            
            Args:
                file_list: 文件列表，以逗号分隔
            
            Returns:
                选择结果
            """
            logger.debug(f"===== select_files 工具被调用! 文件列表: {file_list} =====")  
            try:
                # 解析文件列表
                files = [f.strip() for f in file_list.split(',')]

                log_dir = os.path.join(
                    self.project_dir, ".eng", "memory/issues", "#"+str(self.issues_id)
                )
                os.makedirs(log_dir, exist_ok=True)
                log_path = os.path.join(log_dir, "file_selected.txt")
                # 写日志
                with open(log_path, "w", encoding="utf-8") as f:
                    f.writelines("\n".join(files))

                result = f"已成功选择以下文件:\n{', '.join(files)}"
                logger.debug(f"===== select_files 工具执行结果: {result} =====")  
                return file_list
            except Exception as e:
                error_msg = f"选择文件时出错: {str(e)}"
                logger.error(f"===== select_files 工具执行错误: {error_msg} =====")  
                return ""
        
        return Tool(
            name="select_files",
            description="选择实现功能所需的文件。输入应该是以逗号分隔的文件路径列表，相对于项目根目录。",
            func=select_files,
            return_direct=True,
        )
    
    def select_files_for_requirement(self, requirement: str) -> List[str]:
        """
        根据需求选择所需的文件
        
        Args:
            requirement: 功能需求描述
            
        Returns:
            选择的文件列表
        """
        try:
            # 获取项目中的所有文件
            all_files = FileFetcher.get_all_files_without_ignore(self.project_dir)
            logger.info(f"获取到项目中的文件数量: {len(all_files)}")
            
            # 构建提示词
            prompt = self._build_prompt(requirement, all_files)
            
            # 使用 AI 助手生成响应，使用工具但不指定 tool_choice
            return self.ai_assistant.generate_response(
                prompt, 
                use_tools=True
            ).split(",")
        except Exception as e:
            logger.error(f"select_files_for_requirement 工具执行异常: {str(e)}")
            return []
    
    def _build_prompt(self, requirement: str, all_files: Set[str]) -> str:
        """
        构建提示词
        
        Args:
            requirement: 功能需求
            all_files: 所有可用文件
            
        Returns:
            构建的提示词
        """
        file_str = "\n".join(all_files)
        files_memory = f"""
##角色：
你是一名资深的程序员，现在用户提出了一个需求，首先你要阅读项目代码和文档来了解项目名，你需要根据需求，决定阅读哪些文件。请你根据以下信息做出判断。
##以下是项目中的所有文件:
{file_str}
"""
        # 获取文件描述
        try:
            file_descriptions = FileMemory.get_file_descriptions(self.project_dir)
        except Exception as e:
            logger.warning("file memory is not exists")
            file_descriptions = None

        if file_descriptions:
            # 构建文件描述字符串
            file_str = "\n".join([
                f"- {file}：{file_descriptions.get(file, '无描述')}"
                for file in sorted(all_files)
            ])
            files_memory = f"""
##以下是项目中的所有文件及其功能描述：

{file_str}
"""

        
        return f"""
##需求：

{requirement}


{files_memory}

##请分析这个功能需求，并根据文件名和文件的描述，确定实现这个功能所需阅读的文件。
你的回答应该只包含文件名列表，每个文件名应该与上面列表中的完全匹配。
请使用 select_files 工具提交你的选择，文件名之间用逗号分隔。

##原则：
1、如果你认为该文件和需求的关联性大，有助于你理解如何实现功能那么你应该选择
2、如果你认为该文件可能要在该功能的实现时被修改，那么需要选择
3、如果你认为需要分析项目的依赖配置或新增依赖，那么请选择配置文件
"""

if __name__ == "__main__":
    load_dotenv()
    requirement = """
    """
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../."))
    selector = FileSelector(project_dir, 5, ai_config=AIConfig(
        temperature=0.7,
        model_name="claude-3.5-sonnet"
    ))

    print(selector.select_files_for_requirement(requirement))