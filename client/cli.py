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
        type=str, 
        default=os.path.abspath(os.getcwd()),
        help="Path to the project directory (default: current directory)"
    )
    parser.add_argument(
        "--issue-id", 
        type=int, 
        required=True,
        help="The ID of the issue being processed"
    )
    parser.add_argument(
        "--requirement", 
        type=str, 
        help="The user requirement text"
    )
    parser.add_argument(
        "--requirement-file", 
        type=str, 
        help="Path to file containing the user requirement"
    )

    # Optional arguments for WorkflowEngineConfig
    parser.add_argument(
        "--core-model", 
        type=str, 
        default="gpt-4o",
        help="Model to use for core AI operations"
    )
    parser.add_argument(
        "--data-model", 
        type=str, 
        default="gpt-4o",
        help="Model to use for data operations"
    )
    parser.add_argument(
        "--core-temperature", 
        type=float, 
        default=0.7,
        help="Temperature for core model"
    )
    parser.add_argument(
        "--data-temperature", 
        type=float, 
        default=0.7,
        help="Temperature for data model"
    )
    parser.add_argument(
        "--max-retry", 
        type=int, 
        default=3,
        help="Maximum number of retry attempts"
    )
    parser.add_argument(
        "--default-branch", 
        type=str, 
        default="main",
        help="Default branch name"
    )
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=["client", "bot"],
        default="client",
        help="Operation mode: 'client' or 'bot'"
    )
    parser.add_argument(
        "--base-url", 
        type=str, 
        help="Base URL for API calls"
    )
    parser.add_argument(
        "--api-key", 
        type=str, 
        help="API key for authentication"
    )
    parser.add_argument(
        "--github-remote-url", 
        type=str, 
        help="GitHub remote repository URL"
    )
    parser.add_argument(
        "--github-token", 
        type=str, 
        help="GitHub authentication token"
    )
    
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
    config_params = {
        "project_dir": args.project_dir,
        "issue_id": args.issue_id,
        "core_model": args.core_model,
        "data_model": args.data_model,
        "core_template": args.core_temperature,  # Note: using template to match original param name
        "data_template": args.data_temperature,  # Note: using template to match original param name
        "max_retry": args.max_retry,
        "default_branch": args.default_branch,
        "mode": args.mode,
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
