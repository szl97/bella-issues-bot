"""
File Memory Client

A standalone client for initializing and managing FileMemory using only GitManager.
This module provides both CLI and programmatic interfaces for updating file descriptions.
"""

import argparse
import logging
import os
import shutil
import sys
import tempfile
import uuid
from typing import Dict, Optional

from dotenv import load_dotenv

from core.ai import AIConfig
from core.file_memory import FileMemory, FileMemoryConfig
from core.git_manager import GitManager, GitConfig
from core.log_config import setup_logging, get_logger

logger = get_logger(__name__)


def initialize_file_memory(
    project_dir: str,
    base_branch: str = "main",
    model_name: str = "gpt-4o",
    temperature: float = 0.7,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    remote_url: Optional[str] = None,
    auth_token: Optional[str] = None,
) -> FileMemory:
    """
    Initialize FileMemory using GitManager without LogManager.
    
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
        default_branch=base_branch,
        remote_url=remote_url or os.getenv("GIT_REMOTE_URL"),
        auth_token=auth_token or os.getenv("GITHUB_TOKEN")
    )
    
    # Initialize Git manager
    git_manager = GitManager(config=git_config)
    
    # Initialize and return FileMemory
    file_memory_config = FileMemoryConfig(
        project_dir=project_dir,
        git_manager=git_manager,
        ai_config=ai_config,
        log_manager=None  # Explicitly set to None as per requirements
    )
    
    return FileMemory(config=file_memory_config)


def update_file_descriptions(file_memory: FileMemory) -> None:
    """
    Update file descriptions using the given FileMemory instance.
    
    Args:
        file_memory: Initialized FileMemory instance
        
    Returns:
        Dictionary mapping file paths to their descriptions
    """
    return file_memory.update_file_details()


def process_failed_files(file_memory: FileMemory) -> Dict[str, str]:
    """
    Process previously failed files to generate their descriptions.
    
    Args:
        file_memory: Initialized FileMemory instance
        
    Returns:
        Dictionary mapping file paths to their descriptions
    """
    return file_memory.process_failed_files()


def main() -> None:
    """Command line interface for FileMemory client."""
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="FileMemory Client - Update file descriptions for a project")
    parser.add_argument("--base-branch", "-b", type=str, default="main", help="Base branch for pull requests (default: main)")
    parser.add_argument("-d", "--directory", default=".", help="Project directory path (default: current directory)")
    parser.add_argument("-m", "--model", default="gpt-4o", help="AI model name (default: gpt-4o)")
    parser.add_argument("-t", "--temperature", type=float, default=0.7, help="AI temperature (default: 0.7)")
    parser.add_argument("-k", "--api-key", help="OpenAI API key (defaults to OPENAI_API_KEY env var)")
    parser.add_argument("-u", "--base-url", help="Base URL for API calls (optional)")
    parser.add_argument("--git-url", help="Git remote URL (defaults to GIT_REMOTE_URL env var)")
    parser.add_argument("--git-token", help="Git auth token (defaults to GITHUB_TOKEN env var)")
    parser.add_argument("-l", "--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="Logging level")
    parser.add_argument("--failed-only", action="store_true", help="Process only previously failed files")
    parser.add_argument("-md", "--mode", default="client", help="Project directory path (default: current directory)")
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(log_level=getattr(logging, args.log_level))

    if args.mode == "bot":
        project_dir = os.path.join(
            tempfile.gettempdir(),
            f"bella-bot-memory-init-{str(uuid.uuid4())[:8]}"
        )
    else:
        # Get absolute path for project directory
        project_dir = os.path.abspath(args.directory)
        if not os.path.isdir(project_dir):
            logger.error(f"Project directory does not exist: {project_dir}")
            sys.exit(1)
    
    try:
        # Initialize FileMemory
        file_memory = initialize_file_memory(
            project_dir=project_dir,
            base_branch=args.base_branch,
            model_name=args.model,
            temperature=args.temperature,
            api_key=args.api_key,
            base_url=args.base_url,
            remote_url=args.git_url,
            auth_token=args.git_token
        )


        # Update file details or process failed files
        if args.failed_only:
            process_failed_files(file_memory)
            logger.info("Processed failed files")
        else:
            update_file_descriptions(file_memory)
            logger.info("Updated descriptions files")
        if args.mode == "bot":
            file_memory.git_manager.commit("Update file memory [skip memory]", add_all=False, files=[".eng/memory/file_details.txt", ".eng/memory/git_id"])
            file_memory.git_manager.pull()
            file_memory.git_manager.push()
            file_memory.git_manager.delete_local_repository()
    finally:
        if args.mode == "bot":
            # 删除临时目录
            shutil.rmtree(project_dir, ignore_errors=True)
            logger.info(f"已清理临时工作目录: {project_dir}")


if __name__ == "__main__":
    setup_logging(logging.DEBUG)
    main()
