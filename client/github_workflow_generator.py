"""
GitHub Workflow Generator

A module for generating GitHub Actions workflow files to integrate bella-issues-bot with GitHub.
Creates two workflows:
1. File Memory Initialization - Triggered on push to a configurable branch
2. Issue Processing Bot - Triggered when issues are created or commented on
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Optional

from core.log_config import get_logger, setup_logging

logger = get_logger(__name__)

# Template for memory initialization workflow
MEMORY_INIT_TEMPLATE = """name: Initialize File Memory

on:
  workflow_dispatch:  # Allow manual triggering
    inputs:
      force_run:
        description: 'Force execution even for automated commits'
  push:
    branches:
      - {branch}

jobs:
  init-memory:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    if: ${{{{ !contains(github.event.head_commit.message, '[skip memory]') || github.event_name == 'workflow_dispatch' }}}}
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install bella-issues-bot
        run: |
          python -m pip install --upgrade pip
          pip install bella-issues-bot{package_version}

      - name: Initialize file memory
        env:
          OPENAI_API_KEY: ${{{{ secrets.OPENAI_API_KEY }}}}
          OPENAI_API_BASE: ${{{{ secrets.OPENAI_API_BASE }}}}
          GIT_REMOTE: ${{{{ github.server_url }}}}/${{{{ github.repository }}}}
          GITHUB_TOKEN: ${{{{ secrets.GIT_TOKEN }}}}
        run: |
          bella-file-memory --mode bot -b {branch} -m {model} -t {temperature} --git-url "${{{{ github.server_url }}}}/${{{{ github.repository }}}}" --git-token "${{{{ secrets.GIT_TOKEN }}}}" -u "${{{{ secrets.OPENAI_API_BASE }}}}" -k "${{{{ secrets.OPENAI_API_KEY }}}}"
"""

# Template for issue processing workflow
ISSUE_PROCESS_TEMPLATE = """name: Process Issues with bella-issues-bot

on:
  issues:
    types: [opened]
  issue_comment:
    types: [created]

jobs:
  process-issue:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
    if: ${{{{ github.event_name == 'issues' || !startsWith(github.event.comment.body, 'bella-issues-bot已处理：') }}}}
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install bella-issues-bot
        run: |
          python -m pip install --upgrade pip
          pip install bella-issues-bot{package_version}

      - name: Extract issue info
        id: issue
        run: |
          if [[ "${{{{ github.event_name }}}}" == "issues" ]]; then
            echo "issue_id=${{{{ github.event.issue.number }}}}" >> $GITHUB_OUTPUT
            echo "requirement<<EOF" >> $GITHUB_OUTPUT
            echo "${{{{ github.event.issue.body }}}}" >> $GITHUB_OUTPUT
            echo "EOF" >> $GITHUB_OUTPUT
          else
            echo "issue_id=${{{{ github.event.issue.number }}}}" >> $GITHUB_OUTPUT
            echo "requirement<<EOF" >> $GITHUB_OUTPUT
            echo "${{{{ github.event.comment.body }}}}" >> $GITHUB_OUTPUT
            echo "EOF" >> $GITHUB_OUTPUT
          fi

      - name: Process issue with bella-issues-bot
        env:
          OPENAI_API_KEY: ${{{{ secrets.OPENAI_API_KEY }}}}
          OPENAI_API_BASE: ${{{{ secrets.OPENAI_API_BASE }}}}
          GIT_REMOTE: ${{{{ github.server_url }}}}/${{{{ github.repository }}}}
          GITHUB_TOKEN: ${{{{ secrets.GIT_TOKEN }}}}
          ISSUE_ID: ${{{{ steps.issue.outputs.issue_id }}}}
        run: |
          # Run bella-issues-bot in bot mode - it will handle branch creation and pushing
          bella-issues-bot --mode bot -b {base_branch} --issue-id ${{{{ steps.issue.outputs.issue_id }}}} --core-model {core_model} --data-model {data_model} --core-temperature {core_temperature} --data-temperature {data_temperature} --requirement "${{{{ steps.issue.outputs.requirement }}}}" --git-url "${{{{ github.server_url }}}}/${{{{ github.repository }}}}" --git-token "${{{{ secrets.GIT_TOKEN }}}}" -u "${{{{ secrets.OPENAI_API_BASE }}}}" -k "${{{{ secrets.OPENAI_API_KEY }}}}"
"""

def generate_workflow_files(
    output_dir: str,
    base_branch: str = "main",
    model: str = "gpt-4o",
    core_model: Optional[str] = None,
    data_model: Optional[str] = None,
    temperature: float = 0.7,
    core_temperature: Optional[float] = None,
    data_temperature: Optional[float] = None,
    package_version: str = ""
) -> Dict[str, str]:
    """
    Generate GitHub workflow YAML files.
    
    Args:
        output_dir: Directory to write workflow files
        base_branch: Base branch for pull requests
        model: Default model to use for all operations
        core_model: Model for core operations (if different from model)
        data_model: Model for data operations (if different from model)
        temperature: Default temperature setting for all models
        core_temperature: Temperature for core model (if different)
        data_temperature: Temperature for data model (if different)
        package_version: Specific version of package to install (e.g. "==0.1.1")
        
    Returns:
        Dictionary mapping file paths to their contents
    """
    workflows_dir = os.path.join(output_dir, ".github", "workflows")
    os.makedirs(workflows_dir, exist_ok=True)
    
    # Format version specification if provided
    if package_version and not package_version.startswith("=="):
        package_version = f"=={package_version}"
    
    # Use provided models or default to the general model
    actual_core_model = core_model or model
    actual_data_model = data_model or model
    
    # Use provided temperatures or default to the general temperature
    actual_core_temp = core_temperature if core_temperature is not None else temperature
    actual_data_temp = data_temperature if data_temperature is not None else temperature
    
    # Generate memory initialization workflow
    memory_workflow_path = os.path.join(workflows_dir, "memory_init.yml")
    memory_workflow_content = MEMORY_INIT_TEMPLATE.format(
        branch=base_branch,
        model=actual_data_model,
        temperature=actual_data_temp,
        package_version=package_version
    )
    
    # Generate issue processing workflow
    issue_workflow_path = os.path.join(workflows_dir, "issue_process.yml")
    issue_workflow_content = ISSUE_PROCESS_TEMPLATE.format(
        core_model=actual_core_model,
        data_model=actual_data_model,
        core_temperature=actual_core_temp,
        data_temperature=actual_data_temp,
        base_branch=base_branch,
        package_version=package_version
    )
    
    # Write the files
    with open(memory_workflow_path, 'w') as f:
        f.write(memory_workflow_content)
    
    with open(issue_workflow_path, 'w') as f:
        f.write(issue_workflow_content)
    
    logger.info(f"Generated workflow files in {workflows_dir}")
    
    return {
        memory_workflow_path: memory_workflow_content,
        issue_workflow_path: issue_workflow_content
    }

def main() -> None:
    """Command line interface for GitHub workflow generator."""
    parser = argparse.ArgumentParser(description="Generate GitHub Actions workflows for bella-issues-bot integration")
    parser.add_argument("--output", "-o", type=str, default=".", help="Output directory (default: current directory)")
    parser.add_argument("--base-branch", "-b", type=str, default="main", help="Base branch for pull requests (default: main)")
    parser.add_argument("--model", "-m", type=str, default="gpt-4o", help="Default model for all operations (default: gpt-4o)")
    parser.add_argument("--core-model", "--cm", type=str, help="Model for core operations (defaults to --model)")
    parser.add_argument("--data-model", "--dm", type=str, help="Model for data operations (defaults to --model)")
    parser.add_argument("--temperature", "-t", type=float, default=0.7, help="Default temperature for all models (default: 0.7)")
    parser.add_argument("--core-temperature", "--ct", type=float, help="Temperature for core model (defaults to --temperature)")
    parser.add_argument("--data-temperature", "--dt", type=float, help="Temperature for data model (defaults to --temperature)")
    parser.add_argument("--package-version", "-v", type=str, default="", help="Specific package version to install (e.g. '0.1.1')")
    parser.add_argument("--log-level", "-l", type=str, choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    import logging
    setup_logging(log_level=getattr(logging, args.log_level))
    
    # Generate workflow files
    try:
        generate_workflow_files(
            output_dir=args.output,
            base_branch=args.base_branch,
            model=args.model,
            core_model=args.core_model,
            data_model=args.data_model,
            temperature=args.temperature,
            core_temperature=args.core_temperature,
            data_temperature=args.data_temperature,
            package_version=args.package_version
        )
        logger.info("Successfully generated GitHub workflow files")
    except Exception as e:
        logger.error(f"Error generating workflow files: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
