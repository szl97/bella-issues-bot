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
    core_model: str = "gpt-4o",
    data_model: str = "gpt-4o",
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
    
    # Create config with provided parameters
    config = WorkflowEngineConfig(
        project_dir=project_dir, issue_id=issue_id, core_model=core_model,
        data_model=data_model, core_template=core_temperature, data_template=data_temperature,
        max_retry=max_retry, default_branch=default_branch, mode=mode,
        base_url=base_url, api_key=api_key, github_remote_url=github_remote_url,
        github_token=github_token, **kwargs
    )
    
    # Run the workflow engine
    engine = WorkflowEngine(config)
    response = engine.process_requirement(requirement)
    
    return response
