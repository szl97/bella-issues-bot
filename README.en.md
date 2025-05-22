# bella-issues-bot

- [![Static Badge](https://img.shields.io/badge/deep-wiki-blue?style=flat-square)](https://deepwiki.com/bella-top/bella-issues-bot)
- [![Static Badge](https://img.shields.io/badge/Bella-support-%23C76300?style=flat-square)](https://doc.bella.top/)

English | [中文](./README.md)

## Project Overview

bella-issues-bot is an AI-powered multifunctional code development assistant that operates in two powerful modes:

1. **Personal Development Assistant Mode**: Acts as a command-line tool during daily development, helping analyze code, generate implementations, and solve technical challenges.
2. **GitHub Automation Mode**: Integrates into GitHub workflows, automatically monitoring and handling project issues, analyzing requirements, proposing solutions, and implementing code changes without manual intervention.

Through its deep understanding of project structure and powerful code generation capabilities, bella-issues-bot significantly improves development efficiency, reduces repetitive work, and lets you focus on more creative tasks.

## Key Features

- **Requirement Analysis**: Automatically understands and breaks down user requirements to determine necessary code changes
- **Code Generation**: Generates code that matches project style, automatically implementing new features or fixing issues
- **Version Control**: Deep Git integration, supporting automated branch creation, code commits, and pull request management
- **Memory System**: Records project file descriptions and operation history, providing context-aware capabilities and continuous code quality improvement

### Typical Use Cases

- **Daily Development Support**: Use command-line tools for quick code generation and technical problem-solving
- **Project Automation**: Integrate with GitHub workflows for automated issue handling and code implementation
- **Code Documentation Generation**: Automatically analyze project files and generate detailed functional descriptions
- **Technical Problem Resolution**: Provide targeted solutions after analyzing project context

## Memory and Context Management

bella-issues-bot features a powerful memory system consisting of three core components:

### Memory System Workflow

1. **Initialization Phase**: On first run, the system scans the entire project and generates detailed descriptions for each file
2. **Incremental Updates**: Subsequently, only updates descriptions for new or modified files, improving efficiency
3. **Context Extraction**: When processing user requirements, the system selects relevant files as context based on requirement content

### 1. Log Management (LogManager)

LogManager records complete interaction history, including:
- System prompts and user requirements
- AI responses
- File modification records and diff comparisons

Logs are organized by issue and iteration, supporting historical tracking and problem diagnosis.

### 2. Version Management (VersionManager)

VersionManager provides intelligent version control features:
- Automatically extracts requirements and responses from historical iterations
- Generates formatted execution history as context
- Analyzes relationships between current and historical requirements
- Performs version rollbacks as needed

### 3. File Memory (FileMemory)

FileMemory module maintains detailed descriptions for each project file:
- Automatically generates file functionality, structure, and relationship descriptions
- Tracks file changes and updates affected file descriptions
- Provides context-aware file selection
- Supports ignored files configuration, includes project's .gitignore by default, and supports custom .eng/.engignore

## Installation

### Via pip

```bash
pip install bella-issues-bot
```

### From Source

```bash
git clone https://github.com/szl97/bella-issues-bot.git
cd bella-issues-bot
pip install -e .
```

## System Requirements

- Python 3.10 or higher (< 3.13)
- Git client (for version control features)
- OpenAI API key (for AI functionality)

## Configuration

bella-issues-bot supports multiple configuration methods:

### Environment Variables

The tool reads the following environment variables:

- `OPENAI_API_KEY`: OpenAI API key (required)
- `OPENAI_API_BASE`: OpenAI API base URL (optional, for custom API endpoints)
- `GITHUB_REMOTE_URL`: GitHub repository URL (optional, for GitHub integration)
- `GITHUB_TOKEN`: GitHub authentication token (optional, for GitHub integration)

### Project Configuration Files

- `.eng/system.txt`: Configure code engineer prompts
- `.eng/.engignore`: Similar to `.gitignore`, specifies files to be ignored by the memory system

Example `.engignore` file:
```
# Ignore all log files
*.log

# Ignore build directories
/build/
/dist/

# Ignore virtual environments
/venv/
/.venv/

# Ignore cache files
__pycache__/
*.py[cod]
*$py.class
```

For detailed usage examples and project structure, please refer to the QUICK-START.md guide.