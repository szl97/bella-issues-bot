"""
Programmatic API for running the WorkflowEngine.
Provides a simplified interface for use in Python scripts.
"""

import os
from typing import Optional, Dict, Any, Union

from dotenv import load_dotenv

from core.workflow_engine import WorkflowEngine, WorkflowEngineConfig


def run_workflow(
    issue_id: int,
    requirement: str,
    project_dir: Optional[str] = None,
    model: Optional[str] = None,  # 统一的模型设置
    core_model: Optional[str] = "gpt-4o",
    data_model: Optional[str] = None,  # 默认与core_model相同
    temperature: Optional[float] = None,  # 统一的温度设置
    core_temperature: float = 0.7,
    data_temperature: float = 0.7,
    max_retry: int = 3,
    default_branch: str = "main",
    mode: str = "client",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    github_remote_url: Optional[str] = None,
    github_token: Optional[str] = None,
    **kwargs: Dict[str, Any]
) -> None:
    """Run the WorkflowEngine with the given configuration."""
    # Load environment variables
    load_dotenv()
    
    # Use current directory if no project_dir specified
    if project_dir is None:
        project_dir = os.getcwd()
    
    # 处理统一的模型配置
    if model is not None:
        core_model = model
        data_model = model
    
    # 如果未指定data_model，则默认与core_model相同
    if data_model is None:
        data_model = core_model
    
    # 处理统一的温度配置
    if temperature is not None:
        core_temperature = temperature
        data_temperature = temperature
    
    # Create config with provided parameters
    config = WorkflowEngineConfig(
        project_dir=project_dir, issue_id=issue_id, 
        core_model=core_model, data_model=data_model,
        core_template=core_temperature, data_template=data_temperature,
        max_retry=max_retry, default_branch=default_branch, mode=mode, 
        base_url=base_url, api_key=api_key, github_remote_url=github_remote_url,
        github_token=github_token
    )
    
    # Run the workflow engine
    engine = WorkflowEngine(config)
    response = engine.process_requirement(requirement)
    
    return response
