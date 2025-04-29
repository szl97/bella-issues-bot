"""
Command-line interface for the WorkflowEngine.
Provides functionality to parse command-line arguments and run the engine.
"""

import argparse
import os
import sys
from typing import Optional, Dict, Any


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the WorkflowEngine."""
    parser = argparse.ArgumentParser(
        description="Run the WorkflowEngine to process user requirements"
    )

    # Required arguments
    parser.add_argument(
        "--project-dir", 
        "-p",
        type=str, 
        default=os.path.abspath(os.getcwd()),
        help="Path to the project directory (default: current directory)"
    )
    parser.add_argument(
        "--issue-id", 
        "-i",
        type=int, 
        required=True,
        help="The ID of the issue being processed"
    )
    parser.add_argument(
        "--requirement", 
        "-r",
        type=str, 
        help="The user requirement text"
    )
    parser.add_argument(
        "--requirement-file", 
        "-f",
        type=str, 
        help="Path to file containing the user requirement"
    )

    # Optional arguments for WorkflowEngineConfig
    # 统一模型配置
    parser.add_argument(
        "--model", 
        "-m",
        type=str, 
        help="Model to use for both core and data operations (优先级高于单独配置)"
    )
    parser.add_argument(
        "--temperature",
        "-t",
        type=float, 
        help="Temperature for both core and data models (优先级高于单独配置)"
    )
    
    # 独立模型配置
    parser.add_argument(
        "--core-model", 
        "--cm",
        type=str, 
        default="gpt-4o",
        help="Model to use for core AI operations (当未设置--model时使用)"
    )
    parser.add_argument(
        "--data-model", 
        "--dm",
        type=str, 
        default="gpt-4o",
        help="Model to use for data operations (当未设置--model时使用)"
    )
    parser.add_argument(
        "--core-temperature",
        "--ct",
        type=float, 
        default=0.7,
        help="Temperature for core model (当未设置--temperature时使用)"
    )
    parser.add_argument(
        "--data-temperature",
        "--dt",
        type=float, 
        default=0.7,
        help="Temperature for data model (当未设置--temperature时使用)"
    )
    parser.add_argument(
        "--max-retry", 
        "--retry",
        type=int, 
        default=3,
        help="Maximum number of retry attempts"
    )
    parser.add_argument(
        "--default-branch", 
        "--branch",
        type=str, 
        default="main",
        help="Default branch name"
    )
    parser.add_argument(
        "--mode",
        "-md",
        type=str,
        choices=["client", "bot"],
        default="client",
        help="Operation mode: 'client' or 'bot'"
    )
    parser.add_argument(
        "--base-url",
        "-u",
        type=str,
        help="Base URL for API calls"
    )
    parser.add_argument(
        "--api-key",
        "-k",
        type=str,
        help="API key for authentication"
    )
    parser.add_argument(
        "--github-remote-url",
        "--git-url",
        type=str,
        help="GitHub remote repository URL"
    )
    parser.add_argument(
        "--github-token",
        "--git-token",
        type=str,
        help="GitHub authentication token"
    )
    parser.add_argument(
        "--base-branch",
        "-b",
        type=str,
        default="main",
        help="Base branch for pull requests (default: main)"
    )

    parser.add_argument(
        "-l",
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level")
    
    return parser.parse_args()


def get_requirement_text(args: argparse.Namespace) -> Optional[str]:
    """Get requirement text from arguments or file."""
    if args.requirement:
        return args.requirement
    elif args.requirement_file:
        try:
            with open(args.requirement_file, 'r', encoding='utf-8') as file:
                return file.read()
        except IOError as e:
            print(f"Error reading requirement file: {e}", file=sys.stderr)
            return None
    else:
        print("No requirement specified. Use --requirement or --requirement-file", file=sys.stderr)
        return None


def build_config_from_args(args: argparse.Namespace) -> Dict[str, Any]:
    """Build WorkflowEngineConfig parameters from command line arguments."""
    
    # 处理统一的模型和温度配置
    core_model = args.core_model
    data_model = args.data_model
    core_temperature = args.core_temperature
    data_temperature = args.data_temperature
    
    # 如果设置了统一模型，则覆盖个别设置
    if args.model:
        core_model = args.model
        data_model = args.model
        
    # 如果设置了统一温度，则覆盖个别设置
    if args.temperature is not None:
        core_temperature = args.temperature
        data_temperature = args.temperature
    
    config_params = {
        "project_dir": args.project_dir,
        "issue_id": args.issue_id,
        "core_model": core_model,
        "data_model": data_model,
        "core_template": core_temperature,  # Note: using template to match original param name
        "data_template": data_temperature,  # Note: using template to match original param name
        "max_retry": args.max_retry, 
        "default_branch": args.base_branch,
        "mode": args.mode
    }
    
    # Add optional parameters if they're specified
    if args.base_url:
        config_params["base_url"] = args.base_url
    if args.api_key:
        config_params["api_key"] = args.api_key
    if args.github_remote_url:
        config_params["github_remote_url"] = args.github_remote_url
    if args.github_token:
        config_params["github_token"] = args.github_token
        
    return config_params
