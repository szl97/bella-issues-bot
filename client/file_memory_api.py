"""
File Memory API

Provides programmable API functions for using FileMemory without LogManager.
"""

import os
from typing import Dict, List, Optional

from dotenv import load_dotenv

from core.ai import AIConfig
from core.file_memory import FileMemory, FileMemoryConfig
from core.git_manager import GitManager, GitConfig


def init_file_memory(
    project_dir: str,
    model_name: str = "gpt-4o",
    temperature: float = 0.7,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    remote_url: Optional[str] = None,
    auth_token: Optional[str] = None,
) -> FileMemory:
    """
    Initialize a FileMemory instance with GitManager (no LogManager).
    
    Args:
        project_dir: Path to the project directory
        model_name: AI model to use for generating file descriptions
        temperature: Temperature setting for AI responses
        api_key: API key for AI service (will use env var if None)
        base_url: Base URL for AI service (will use default if None)
        remote_url: Git remote URL (will use env var if None)
        auth_token: Git authentication token (will use env var if None)
        
    Returns:
        Initialized FileMemory instance
    """
    # Load environment variables if not already loaded
    load_dotenv()
    
    # Create AI config
    ai_config = AIConfig(
        model_name=model_name,
        temperature=temperature,
        api_key=api_key,
        base_url=base_url
    )
    
    # Create Git config
    git_config = GitConfig(
        repo_path=project_dir,
        remote_url=remote_url or os.getenv("GIT_REMOTE"),
        auth_token=auth_token or os.getenv("GITHUB_TOKEN")
    )
    
    # Initialize Git manager
    git_manager = GitManager(config=git_config)
    
    # Initialize and return FileMemory
    file_memory_config = FileMemoryConfig(
        project_dir=project_dir,
        git_manager=git_manager,
        ai_config=ai_config,
        log_manager=None  # Explicitly None as per requirements
    )
    
    return FileMemory(config=file_memory_config)


def update_file_descriptions(file_memory: FileMemory) -> None:
    """
    Update file descriptions using the given FileMemory instance.
    
    Args:
        file_memory: Initialized FileMemory instance
    """
    file_memory.update_file_details()


def process_failed_files(file_memory: FileMemory) -> Dict[str, str]:
    """
    Process previously failed files to generate their descriptions.
    
    Args:
        file_memory: Initialized FileMemory instance
        
    Returns:
        Dictionary mapping file paths to their descriptions
    """
    return file_memory.process_failed_files()
