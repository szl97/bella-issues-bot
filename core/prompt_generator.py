import os
import re
from dataclasses import dataclass
from typing import List, Dict, Optional

from dotenv import load_dotenv
from jinja2 import Template

from core.ai import AIConfig
from core.file_memory import FileMemory
from core.file_selector import FileSelector


@dataclass
class PromptData:
    """提示数据类，封装生成提示所需的数据"""
    project_dir: str
    files: List[str]
    file_desc: Dict[str, str]
    requirement: str
    steps: Optional[str] = None


@dataclass
class ExtractedInfo:
    """提取的信息类，封装从提示中提取的数据"""
    project_dir: str
    files: List[str]
    file_desc: Dict[str, str]
    requirement: str
    steps: Optional[str] = None


class PromptGenerator:
    """
    生成结构化提示的工具类，用于根据文件描述、文件内容、历史执行信息和用户需求生成提示
    """
    
    # 提示模板
    PROMPT_TEMPLATE = """# 项目文件描述

{% for file_path in data.files %}
- {{ file_path }}: {{ data.file_desc.get(file_path, "无描述") }}
{% endfor %}

# 文件内容

{% for file_path in data.files %}
{% if file_exists(data.project_dir, file_path) %}
```
File: {{ file_path }}
{{ format_file_content(data.project_dir, file_path) }}
```

{% endif %}
{% endfor %}
{% if data.steps %}
# 历史执行信息

{{ data.steps }}

{% endif %}
# 用户需求

{{ data.requirement }}
"""

    @staticmethod
    def generatePrompt(data: PromptData) -> str:
        """
        根据提示数据生成结构化提示
        
        Args:
            data: 提示数据对象
            
        Returns:
            str: 生成的结构化提示
        """
        # 创建 Jinja2 模板
        template = Template(PromptGenerator.PROMPT_TEMPLATE)
        
        # 定义辅助函数
        def file_exists(project_dir, file_path):
            path = os.path.join(project_dir, file_path)
            return os.path.exists(path)
        
        def format_file_content(project_dir, file_path):
            try:
                path = os.path.join(project_dir, file_path)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 添加行号
                lines = content.split("\n")
                numbered_content = ""
                for i, line in enumerate(lines, 1):
                    numbered_content += f"{i} {line}\n"
                
                return numbered_content.rstrip()
            except Exception as e:
                return f"无法读取文件内容: {str(e)}"
        
        # 渲染模板
        return template.render(
            data=data,
            file_exists=file_exists,
            format_file_content=format_file_content
        )

    @staticmethod
    def extractInfo(prompt: str) -> ExtractedInfo:
        """
        从提示中提取信息
        
        Args:
            prompt: 提示文本
            
        Returns:
            ExtractedInfo: 提取的信息对象
        """
        files = []
        file_desc = {}
        steps = ""
        requirement = ""
        
        # 提取文件描述
        desc_pattern = r"# 项目文件描述\n\n(.*?)(?=\n# )"
        desc_match = re.search(desc_pattern, prompt, re.DOTALL)
        if desc_match:
            desc_text = desc_match.group(1).strip()
            for line in desc_text.split("\n"):
                if line.startswith("- "):
                    parts = line[2:].split(": ", 1)
                    if len(parts) == 2:
                        file_path, desc = parts
                        files.append(file_path)
                        file_desc[file_path] = desc
        
        # 提取历史执行信息
        steps_pattern = r"# 历史执行信息\n\n(.*?)(?=\n# )"
        steps_match = re.search(steps_pattern, prompt, re.DOTALL)
        if steps_match:
            steps = steps_match.group(1).strip()
        
        # 提取用户需求
        req_pattern = r"# 用户需求\n\n(.*)"
        req_match = re.search(req_pattern, prompt, re.DOTALL)
        if req_match:
            requirement = req_match.group(1).strip()
        
        return ExtractedInfo(files, file_desc, steps, requirement)
    
    @staticmethod
    def formatFileContent(file_path: str) -> str:
        """
        格式化文件内容，添加行号
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 格式化后的文件内容
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 添加行号
            lines = content.split("\n")
            numbered_content = ""
            for i, line in enumerate(lines, 1):
                numbered_content += f"{i} {line}\n"
            
            return numbered_content.rstrip()
        except Exception as e:
            return f"无法读取文件 {file_path}: {str(e)}"

if __name__ == "__main__":
    load_dotenv()
    requirement = """
    """
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../."))
    selector = FileSelector(project_dir, 2, ai_config=AIConfig(
        temperature=1,
        model_name="claude-3.7-sonnet"
    ))

    files = selector.select_files_for_requirement(requirement)

    descriptions = FileMemory.get_selected_file_descriptions("../.", files)

    data = PromptData(project_dir = "../.", files=files, file_desc=descriptions, requirement=requirement, steps=None)

    print(PromptGenerator.generatePrompt(data))

