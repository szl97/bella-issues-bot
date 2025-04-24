import os
from typing import List, Optional

from dotenv import load_dotenv
from langchain.tools import Tool

from core.ai import AIAssistant, AIConfig
from core.file_manager import FileManager
from core.file_memory import FileMemory, FileMemoryConfig


class FileSelector:
    """
    使用 AI 辅助选择实现特定功能所需的文件
    """

    def __init__(self, project_dir: str, ai_config: Optional[AIConfig] = None):
        """
        初始化 FileSelector
        
        Args:
            project_dir: 项目根目录
            ai_config: AI 配置，如果为 None 则使用默认配置
        """
        self.project_dir = project_dir
        self.ai_config = ai_config or AIConfig()
        self.file_manager = FileManager()
        
        # 确保 .gpteng 目录和文件选择文件存在
        self._ensure_selection_file()
        
        # 创建 AI 助手和工具
        self.select_files_tool = self._create_select_files_tool()
        self.ai_assistant = AIAssistant(
            config=self.ai_config,
            tools=[self.select_files_tool]
        )

        # # 初始化并更新文件描述
        # file_memory = FileMemory(FileMemoryConfig(
        #     project_dir=project_dir,
        #     ai_config=ai_config
        # ))
        # file_memory.update_file_details()
    
    def _ensure_selection_file(self) -> None:
        """确保文件选择文件存在"""
        selection_path = os.path.join(self.project_dir, ".gpteng", "file_selection.toml")
        if not os.path.exists(selection_path):
            FileManager.create_selection_file(self.project_dir)
    
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
            print(f"===== select_files 工具被调用! 文件列表: {file_list} =====")  
            try:
                # 解析文件列表
                files = [f.strip() for f in file_list.split(',')]
                
                # 使用 FileManager 重新设置文件选择状态
                FileManager.reuncomment_files(self.project_dir, files)
                log_dir = os.path.join(self.project_dir, ".gpteng/memory/logs")
                os.makedirs(log_dir, exist_ok=True)
                log_path = os.path.join(log_dir, "file_selected_log.txt")
                # 写日志
                with open(log_path, "w", encoding="utf-8") as f:
                    f.writelines("\n".join(files))

                result = f"已成功选择以下文件:\n{', '.join(files)}"
                print(f"===== select_files 工具执行结果: {result} =====")  
                return result
            except Exception as e:
                error_msg = f"选择文件时出错: {str(e)}"
                print(f"===== select_files 工具执行错误: {error_msg} =====")  
                return error_msg
        
        return Tool(
            name="select_files",
            description="选择实现功能所需的文件。输入应该是以逗号分隔的文件路径列表，相对于项目根目录。",
            func=select_files,
        )
    
    def select_files_for_requirement(self, requirement: str) -> None:
        """
        根据需求选择所需的文件
        
        Args:
            requirement: 功能需求描述
            
        Returns:
            选择的文件列表
        """
        # 获取项目中的所有文件
        all_files = FileManager.get_selected_files(self.project_dir)
        print(f"获取到项目中的文件数量: {len(all_files)}")
        
        # 构建提示词
        prompt = self._build_prompt(requirement, all_files)
        
        # 使用 AI 助手生成响应，使用工具但不指定 tool_choice
        self.ai_assistant.generate_response(
            prompt, 
            use_tools=True
        )

    def select_files_for_requirement_with_log(self, requirement: str) -> None:
        log_path = os.path.join(
            self.project_dir, ".gpteng", "memory/logs/file_selected_log.txt"
        )
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read()
            FileManager.reuncomment_files(self.project_dir, content.split('\n'))
        else:
            self.select_files_for_requirement(requirement)


    
    def _build_prompt(self, requirement: str, all_files: List[str]) -> str:
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
以下是项目中的所有文件:
{file_str}
"""
        # 获取文件描述
        file_descriptions = FileMemory.get_file_descriptions(self.project_dir)

        if len(file_descriptions) > 0:
            # 构建文件描述字符串
            file_str = "\n".join([
                f"- {file}：{file_descriptions.get(file, '无描述')}"
                for file in sorted(all_files)
            ])
            files_memory = f"""
以下是项目中的所有文件及其功能描述：

{file_str}
"""
        else:
            print("file memory is not exists")


        
        return f"""
我需要实现以下功能：

{requirement}


{files_memory}

请分析这个功能需求，并根据文件的功能描述，确定实现这个功能所需的文件。
你的回答应该只包含文件名列表，每个文件名应该与上面列表中的完全匹配。
请使用 select_files 工具提交你的选择，文件名之间用逗号分隔。
"""

if __name__ == "__main__":
    load_dotenv()
    requirement = """
    file_selector.py 在解决用户编码需求前选择文件，
    目前仅仅使用了文件名，应该将文件描述给模型效果会更好，因此，请实现 file_memory。
    1、如果不存在file_memory，为项目目录中的每个文件生成描述
    2、注意调用大模型的提示词的优化和上下文长度，提示词请使用中文，每次处理小于10000行
    3、模型生成的文件描述，保存在.gpteng/memory/file_details中，格式为一个文件一行，filename:描述，filename要和file_manager的filename对应。
    4、在.gpteng/memory/file_details保存当前的git的id，下一次触发时，如果存在.gpteng/memory/file_details.txt，根据gitlog找到修改的文件、新增的文件和删除的文件，只进行增量处理
    *******************************************************
    项目的依赖在 pyproject.toml文件中获取
    """
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../."))
    selector = FileSelector(project_dir, ai_config=AIConfig(
        temperature=0.7,
        model_name="claude-3.5-sonnet"
    ))

    selector.select_files_for_requirement_with_log(requirement)