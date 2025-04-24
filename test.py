from gpt_engineer.applications.cli.gpt_engineer_client import GPTEngineerClient

def main():
    # 创建客户端实例
    client = GPTEngineerClient(
        project_path="/Users/saizhuolin/test/bella-openapi",
        openai_api_key="",
        openai_api_base="https://test-bella-openapi.ke.com/v1",  # 可选
        model="coder-model",
        temperature=1
    )
    # 生成代码
    files = client.improve(prompt = "【代码分析与修改规范】请遵循以下步骤进行代码修改：\n1、深度代码分析阶段\n绘制模块依赖图：分析所有关联代码文件，标注各模块的输入输出和依赖关系\n2、功能映射表：为每个文件创建功能说明（包含：核心职责、调用关系、关键接口）\n3、识别敏感区域：标记出会影响核心功能的关键代码段\n4、安全修改准则\n影响评估清单：必须验证修改不会影响：\n✓ 现有 API 接口契约\n✓ 数据流关键路径\n✓ 跨模块交互协议\n4、框架化开发要求\n风格统一检查表：\n√ 命名规范（类 / 方法 / 变量前缀后缀）\n√ 代码组织结构（包 / 目录层级）\n√ 注释模板\n扩展性设计：\n→ 采用开放封闭原则（OCP）\n→ 预留扩展点（extension points）\n→ 配置驱动而非硬编码\n→ 重要接口添加。\n**********用户要求：你的任务是为/v1/chat/completions实现一个备选模型的功能。用户请求，可以传入两个模型，用“，”分割。当第一个模型不可用时，选择 第二个模型。**************comment：应该新增一个Adpaptor来处理*******注意：你可以新增文件，但是如果要修改的文件，文件名一定要和我提供的一致，否则程序会报错！！",
                           no_execution=False)

    # 处理生成的文件
    for file_path, content in files.items():
        print(f"Generated file: {file_path}, content: {content}")
 
if __name__ == "__main__":
    main()