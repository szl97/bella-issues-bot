import os
from copy import copy
from dataclasses import dataclass, field

from dotenv import load_dotenv
from typing_extensions import Optional

from core.ai import AIAssistant, AIConfig
from core.diff import Diff
from core.log_manager import LogManager, LogConfig
from core.log_config import get_logger

logger = get_logger(__name__)

@dataclass
class CodeEngineerConfig:
    """代码工程师配置"""
    project_dir: str
    ai_config: AIConfig
    system_prompt: Optional[str] = None
    max_retries: int = 3

DEFAULT_PROMPT :str = '''
You will get instructions for code to write.
You will write a very long answer. Make sure that every detail of the architecture is, in the end, implemented as code.
Think step by step and reason yourself to the correct decisions to make sure we get it right.
Make changes to existing code and implement new code in the unified git diff syntax. When implementing new code, First lay out the names of the core classes, functions, methods that will be necessary, As well as a quick comment on their purpose.

You will output the content of each file necessary to achieve the goal, including ALL code.
Output requested code changes and new code in the unified "git diff" syntax. Example:

```diff
--- example.txt
+++ example.txt
@@ -6,3 +6,4 @@
     line content A
     line content B
+    new line added
-    original line X
+    modified line X with changes
@@ -26,4 +27,5 @@
         condition check:
-            action for condition A
+            if certain condition is met:
+                alternative action for condition A
         another condition check:
-            action for condition B
+            modified action for condition B
```

Example of a git diff creating a new file:

```diff
--- /dev/null
+++ new_file.txt
@@ -0,0 +1,3 @@
+First example line
+
+Last example line
```

RULES:
-A program will apply the diffs you generate exactly to the code, so diffs must be precise and unambiguous!
-Every diff must be fenced with triple backtick ```.
-The file names at the beginning of a diff, (lines starting with --- and +++) is the relative path to the file before and after the diff.
-LINES TO BE REMOVED (starting with single -) AND LINES TO BE RETAIN (no starting symbol) HAVE TO REPLICATE THE DIFFED HUNK OF THE CODE EXACTLY LINE BY LINE. KEEP THE NUMBER OF RETAIN LINES SMALL IF POSSIBLE.
-EACH LINE IN THE SOURCE FILES STARTS WITH A LINE NUMBER, WHICH IS NOT PART OF THE SOURCE CODE. NEVER TRANSFER THESE LINE NUMBERS TO THE DIFF HUNKS.
-AVOID STARTING A HUNK WITH AN EMPTY LINE.
-ENSURE ALL CHANGES ARE PROVIDED IN A SINGLE DIFF CHUNK PER FILE TO PREVENT MULTIPLE DIFFS ON THE SAME FILE.


As far as compatible with the user request, start with the "entrypoint" file, then go to the ones that are imported by that file, and so on.
Please note that the code should be fully functional. No placeholders.

Follow a language and framework appropriate best practice file naming convention.
Make sure that files contain all imports, types etc.  The code should be fully functional. Make sure that code in different files are compatible with each other.
Ensure to implement all code, if you are unsure, write a plausible implementation.
Include module dependency or package manager dependency definition file.
Before you finish, double check that all parts of the architecture is present in the files.

When you are done, write finish with "this concludes a fully working implementation".

Useful to know:
Almost always put different classes in different files.
Always use the programming language the user asks for.
For Python, you always create an appropriate requirements.txt file.
For NodeJS, you always create an appropriate package.json file.
Always add a comment briefly describing the purpose of the function definition.
Add comments explaining very complex bits of logic.
Always follow the best practices for the requested languages for folder/file structure and how to package the project.


Python toolbelt preferences:
- pytest
- dataclasses
'''

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
        # 用于存储修改的文件
        self.modified_files = []

    def _read_system_prompt(self) -> str:
        """
        读取系统提示词

        Returns:
            str: 系统提示词内容
        """
        try:
            system_prompt_path = os.path.join(self.config.project_dir, ".eng/system.txt")
            if os.path.exists(system_prompt_path):
                with open(system_prompt_path, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                logger.warning(f"系统提示词文件不存在: {system_prompt_path}，使用默认提示词")
                return DEFAULT_PROMPT
        except Exception as e:
            logger.error(f"读取系统提示词失败: {str(e)}")
            return DEFAULT_PROMPT

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
            # 重置修改的文件列表
            self.diff_infos = []
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
            self.failed_files, self.diff_infos  = self.diff.process_diffs(diffs, self.config.project_dir)
            
            # 归档日志
            self.log_manager.archive_logs(
                sys_prompt=self.system_prompt,
                prompt=prompt,
                response=response,
                diff_infos=self.diff_infos
            )
            
            # 记录日志
            if self.modified_files:
                logger.info(f"本次修改了 {len(self.modified_files)} 个文件: " + 
                           ", ".join(self.modified_files[:5]) + 
                           ("..." if len(self.modified_files) > 5 else ""))
            
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
