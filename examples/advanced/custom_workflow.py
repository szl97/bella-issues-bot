"""
高级示例：自定义工作流处理程序

展示如何将bella-issues-bot集成到自定义应用程序中，
包括自定义前处理和后处理逻辑。
"""

import os
from typing import Optional
from client.runner import run_workflow


def preprocess_requirement(raw_requirement: str) -> str:
    """
    预处理用户需求，增加额外的上下文信息
    
    Args:
        raw_requirement: 原始需求文本
        
    Returns:
        增强后的需求文本
    """
    # 例如：添加项目特定的规范或约束
    return f"{raw_requirement}\n\n注意：请确保代码遵循PEP 8规范，并包含适当的单元测试。"


def postprocess_response(response: str) -> str:
    """
    处理AI响应，进行后期格式化或额外操作
    
    Args:
        response: AI生成的原始响应
        
    Returns:
        处理后的响应
    """
    # 例如：添加时间戳或标记
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"处理时间: {timestamp}\n\n{response}"


# 示例使用
if __name__ == "__main__":
    # 1. 读取并预处理需求
    with open("requirements/feature_request.txt", "r") as f:
        raw_requirement = f.read()
    
    enhanced_requirement = preprocess_requirement(raw_requirement)
    
    # 2. 运行工作流
    response = run_workflow(
        issue_id=301,
        requirement=enhanced_requirement,
        project_dir=os.getenv("PROJECT_DIR", "."),
        core_model=os.getenv("CORE_MODEL", "gpt-4o"),
        core_temperature=float(os.getenv("CORE_TEMP", "0.7"))
    )
    
    # 3. 后处理响应
    final_response = postprocess_response(response)
    
    print(final_response)
