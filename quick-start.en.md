# Quick Start Guide

English | [中文](./quick-start.md)

This guide provides essential information to get started with bella-issues-bot quickly.

## Basic Setup

1. Install the package:
```bash
pip install bella-issues-bot
```

2. Set up environment variables:
```bash
export OPENAI_API_KEY="your-api-key"
```

## Common Use Cases

### 1. Personal Development Assistant

Use bella-issues-bot as your coding assistant:

```bash
# Generate code implementation
bella-issues-bot --requirement "Create a function to calculate fibonacci numbers"

# Analyze existing code
bella-issues-bot --requirement "Review and optimize this function" --file path/to/file.py

# Fix bugs
bella-issues-bot --requirement "Fix the memory leak in this module" --file path/to/module.py
```

### 2. GitHub Integration

1. Create `.github/workflows/bella-bot.yml`:

```yaml
name: Bella Issues Bot
on:
  issues:
    types: [opened, edited]

jobs:
  process-issue:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Bella Issues Bot
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          pip install bella-issues-bot
          bella-issues-bot --mode github
```

2. Add repository secrets:
   - Go to repository Settings > Secrets
   - Add your `OPENAI_API_KEY`

### 3. File Memory System

Initialize the file memory system for better context awareness:

```bash
# Initialize file memory
bella-file-memory --project-dir .

# Update file memory after changes
bella-file-memory --project-dir . --update
```

### 4. Configuration

Create `.eng/.engignore` to exclude files from analysis:

```
# Example .engignore
node_modules/
dist/
*.log
```

## Common Parameters

- `--requirement`: The task or requirement description
- `--mode`: Operation mode (`client` or `github`)
- `--core-model`: AI model to use (default: gpt-4)
- `--core-temperature`: Model temperature (default: 0.7)
- `--project-dir`: Project directory path

## Best Practices

1. **Clear Requirements**: Write clear, specific requirements for better results
2. **File Memory**: Initialize file memory before first use
3. **Version Control**: Always work in a clean git repository
4. **Context**: Provide relevant file paths when needed
5. **Regular Updates**: Keep the tool and file memory system updated