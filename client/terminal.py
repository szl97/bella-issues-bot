"""
Terminal entrypoint for the WorkflowEngine.
Provides functionality to run the engine from terminal with command-line arguments.
"""
import logging
import os
import sys

from dotenv import load_dotenv

from client.cli import parse_args, get_requirement_text, build_config_from_args
from core.log_config import setup_logging
from core.workflow_engine import WorkflowEngine, WorkflowEngineConfig


def run_workflow_from_terminal() -> None:
    """
    Main entry point for running the workflow engine from terminal.
    Parses command line arguments and runs the workflow engine.
    """
    # Load environment variables from .env file if present
    load_dotenv()
    
    # Parse command line arguments
    args = parse_args()
    
    # Get requirement text
    requirement = get_requirement_text(args)
    if not requirement:
        sys.exit(1)
    
    # Build config from arguments
    config_params = build_config_from_args(args)

    setup_logging(log_level=getattr(logging, args.log_level))
    
    # Try to get API key from environment if not provided as argument
    if "api_key" not in config_params and os.environ.get("OPENAI_API_KEY"):
        config_params["api_key"] = os.environ.get("OPENAI_API_KEY")
    
    # Create the workflow engine config
    config = WorkflowEngineConfig(**config_params)
    
    # Initialize and run the workflow engine
    engine = WorkflowEngine(config)
    engine.process_requirement(requirement)

if __name__ == "__main__":
    response = run_workflow_from_terminal()

