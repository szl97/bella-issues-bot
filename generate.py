import os

from gpt_engineer.applications.cli.gpt_engineer_client import GPTEngineerClient

from core.ai import AIConfig
from core.file_selector import FileSelector


def main():


    requirement = """
    file_selector.py 调用 file_manager 和 ai.py 在解决用户编码需求前选择文件，
    目前仅仅使用了文件名，应该将文件描述给模型效果会更好，因此，请实现 file_memory。
    方法1：
    1、如果不存在file_memory，通过 ai.py 为项目目录中的每个文件生成描述，获取所有文件使用FileManager的get_all_files_without_ignore
    2、注意调用大模型的提示词的优化和上下文长度，提示词请使用中文，每次处理小于10000行
    3、模型生成的文件描述，保存在.gpteng/memory/file_details中，格式为一个文件一行，filename:描述，filename要和file_manager的filename对应。
    4、在.gpteng/memory/file_details保存当前的git的id，下一次触发时，如果存在.gpteng/memory/file_details，根据gitlog找到修改的文件、新增的文件和删除的文件，只进行增量处理
    5、git的相关操作在git_manager中，如果有需要的方法没实现，需要实现
    方法2:
    1、通过file_memory提供一个静态方法来获取文件描述
    2、file_selector的_build_prompt，传入的文件名改为文件描述
    *******************************************************
    项目的依赖在 pyproject.toml文件中获取
    """

    # 生成代码
    # files = client.improve(prompt = "实现GitManager：push，pull，create branches，switch等git的基本操作",
    #                        no_execution=False)

    # files = client.improve(prompt = "使用langchain框架，实现chat completion的功能，需要使用工具调用的能力。用于处理整个系统等chat completion请求。需要的依赖加到pyproject.toml中")

    #files = client.improve("在file_manager.py下实现一个方法，入参是文件目录，获取目录文件下所有的文件，.gitignore标记的文件除外。返回内容写入该文件目录下的.gpteng/file_selection.toml中，如果存在则替换。文件格式即file_selection_example.toml文件的格式")

    #files = client.improve("在file_manager.py下实现两个方法，一个方法入参是文件目录，获取.gpteng/file_selection.toml中所有的文件名，文件格式即file_selection_example.toml文件的格式。文件名前可能有 # 也可能没有，真实的文件名都不会有#。第二个方法，入参是文件目录和文件名列表，去掉.gpteng/file_selection.toml中该列表内的文件名前的#")

    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
    selector = FileSelector(project_dir, ai_config=AIConfig(
        base_url="https://test-bella-openapi.ke.com/v1",
        api_key="",
        temperature=0.7,
        model_name="claude-3.5-sonnet"
    ))

    selector.select_files_for_requirement_with_log(requirement)

    # 创建客户端实例
    client = GPTEngineerClient(
        project_path=project_dir,
        openai_api_key="",
        openai_api_base="https://test-bella-openapi.ke.com/v1",
        model="coder-model",
        temperature=1
    )

    files = client.improve(requirement)

if __name__ == "__main__":
    main()