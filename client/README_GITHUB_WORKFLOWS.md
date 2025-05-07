# GitHub工作流生成器

bella-issues-bot 提供了自动生成 GitHub Actions 工作流配置的功能，可以轻松将 AI 助手集成到您的 GitHub 项目中。

## 功能概述

工作流生成器会创建两个GitHub Actions工作流文件：

1. **记忆初始化工作流** (`memory_init.yml`)
   - 当指定分支有推送时触发
   - 会跳过机器人自身的提交（通过检查提交信息中的"Update file memory"）
   - 分析项目文件并生成文件描述
   - 将记忆文件提交回仓库

2. **Issue处理工作流** (`issue_process.yml`)
   - 在创建新Issue或添加评论时触发
   - 自动提取Issue或评论中的需求
   - 在专用分支上处理需求并实现代码
   - 创建拉取请求，提供解决方案
   - 在Issue中添加处理结果的评论

## 命令行使用方式

运行以下命令生成GitHub工作流文件：

```bash
# 基本用法 - 使用默认配置
bella-github-workflows

# 指定基础分支
bella-github-workflows --base-branch develop

# 自定义模型和温度
bella-github-workflows --model gpt-4o --temperature 0.5
```

### 命令行参数

- `--output-dir`, `-o`: 输出目录，默认为 `.github/workflows`
- `--base-branch`, `-bb`: 拉取请求的目标分支，默认为 `main`
- `--model`, `-m`: 默认 AI 模型，默认为 `gpt-4o`
- `--core-model`, `--cm`: 核心操作使用的模型（如果与默认模型不同）
- `--data-model`, `--dm`: 数据操作使用的模型（如果与默认模型不同）
- `--temperature`, `-t`: 默认温度设置，默认为 `0.7`
- `--core-temperature`, `--ct`: 核心模型的温度（如果与默认温度不同）
- `--data-temperature`, `--dt`: 数据模型的温度（如果与默认温度不同）
- `--package-version`, `-v`: 指定安装的包版本，例如 `==0.1.1`

### 记忆初始化工作流 (`memory_init.yml`)

此工作流在指定分支有推送时运行，它：
1. 检查提交是否由自动化机器人产生（含有"Update file memory"的提交信息）
   - 如果是机器人提交，则会跳过执行，防止无限循环
   - 可以通过workflow_dispatch手动触发并强制执行
2. 检出代码库
3. 设置Python环境
4. 安装bella-issues-bot
5. 初始化文件记忆系统，生成项目文件描述
6. 将生成的记忆文件提交回仓库（提交信息带有[skip memory]标记）

### Issue处理工作流 (`issue_process.yml`)

此工作流在创建新Issue或添加评论时运行，具体步骤如下：
1. 检出代码库
2. 设置Python环境
3. 安装bella-issues-bot
4. 提取Issue或评论中的需求
5. 运行bella-issues-bot处理需求（它会自动创建分支并提交代码）
   - 如果评论以"bella-issues-bot已处理："开头，则跳过处理
6. 创建拉取请求
7. 在Issue中添加处理结果的评论

## GitHub配置要求

要使这些工作流正常运行，您需要在GitHub仓库的设置中配置以下内容：

### 1. Secrets 配置

在仓库的 Settings > Secrets and variables > Actions 中添加以下 secrets：

- `OPENAI_API_KEY`: 您的OpenAI API密钥（必需）
- `OPENAI_API_BASE`: 自定义API基础URL（可选）
- `GITHUB_TOKEN`: GitHub自动提供，无需手动配置

### 2. 权限设置

在仓库的 Settings > Actions > General > Workflow permissions 中：

- 选择 "Read and write permissions"
- 勾选 "Allow GitHub Actions to create and approve pull requests"

## 工作流文件详解

### 记忆初始化工作流 (`memory_init.yml`)

```yaml
name: Initialize File Memory

on:
  workflow_dispatch:  # 允许手动触发
    inputs:
      force_run:
        description: '强制执行，即使是自动提交'
  push:
    branches:
      - main  # 可自定义为您的默认分支

jobs:
  init-memory:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    if: ${{ !contains(github.event.head_commit.message, '[skip memory]') || github.event_name == 'workflow_dispatch' }}
    steps:
      - name: 检出代码
        uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: 设置Python环境
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: 安装依赖
        run: pip install bella-issues-bot
        
      - name: 初始化文件记忆
        env:
           OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
           OPENAI_API_BASE: ${{ secrets.OPENAI_API_BASE }}
           GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
           GIT_REMOTE: ${{ github.server_url }}/${{ github.repository }}
        run: bella-file-memory \
              --mode bot \
              --model gpt-4o \
              -u "https://api.openai.com/v1" \
              -k "sk-xxxxx" \
              --git-url "https://github.com/szl97/bella-issues-bot.git" \
              --git-token "githubxxxxx"
```

### Issue处理工作流 (`issue_process.yml`)

```yaml
name: Process Issues with AI

on:
  issues:
    types: [opened]
  issue_comment:
    types: [created]

jobs:
  process-issue:
    runs-on: ubuntu-latest
    if: ${{ !startsWith(github.event.comment.body, 'bella-issues-bot已处理：') }}
    permissions:
      contents: write
      pull-requests: write
      issues: write
    steps:
      - name: 检出代码
        uses: actions/checkout@v3
        with:
          fetch-depth: 0
          
      - name: 设置Python环境
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: 安装依赖
        run: pip install bella-issues-bot
        
      - name: 处理Issue
        env:
           OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
           OPENAI_API_BASE: ${{ secrets.OPENAI_API_BASE }}
           GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
           GIT_REMOTE: ${{ github.server_url }}/${{ github.repository }}
        run: |
          # 提取Issue ID和需求
          ISSUE_ID=${{ github.event.issue.number }}
          REQUIREMENT="${{ github.event.issue.body || github.event.comment.body }}"
          
          # 运行bella-issues-bot处理需求
          bella-issues-bot \
            --issue-id $ISSUE_ID \
            --requirement "$REQUIREMENT" \
            --mode bot \
            -u "https://api.openai.com/v1" \
            -k "sk-xxxxx" \
            --git-url "https://github.com/szl97/bella-issues-bot.git" \
            --git-token "githubxxxxx"
```

## 使用场景

### 1. 自动化需求实现

当用户在GitHub Issues中提出新功能需求或报告bug时，bella-issues-bot可以：
- 自动分析需求
- 实现所需的代码更改
- 创建拉取请求
- 在Issue中提供详细的解决方案说明

### 2. 代码文档维护

每当有新代码推送到主分支时，bella-issues-bot可以：
- 分析新增或修改的文件
- 更新文件功能描述
- 维护项目的知识库

### 3. 技术支持自动化

当用户在Issues中提出技术问题时，bella-issues-bot可以：
- 分析问题
- 提供解决方案
- 生成示例代码
- 自动回复用户

## 自定义工作流

您可以根据项目需求自定义工作流文件。以下是一些常见的自定义场景：

### 1. 触发条件自定义

您可以修改工作流的触发条件，例如：
- 限制特定标签的Issues
- 只在特定分支上运行
- 添加定时触发

```yaml
on:
  issues:
    types: [opened, labeled]
  issue_comment:
    types: [created]
  schedule:
    - cron: '0 0 * * 1'  # 每周一运行
```

### 2. 环境自定义

您可以自定义Python版本或添加其他环境依赖：

```yaml
- name: 设置Python环境
  uses: actions/setup-python@v4
  with:
    python-version: '3.11'
    
- name: 安装额外依赖
  run: |
    pip install bella-issues-bot
    pip install your-additional-package
```

### 3. 通知自定义

您可以添加Slack、Email或其他通知方式：

```yaml
- name: 发送Slack通知
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    fields: repo,message,commit,author,action,eventName,ref,workflow
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
  if: always()
```

## 故障排除

### 常见问题

1. **权限问题**：确保工作流有适当的权限（contents、issues、pull-requests）
2. **API密钥问题**：检查OPENAI_API_KEY是否正确设置
3. **提交循环**：如果遇到无限提交循环，检查提交消息过滤逻辑
4. **超时问题**：对于大型项目，可能需要增加工作流超时限制

### 日志和调试

GitHub Actions提供了详细的日志，您可以在Actions标签页中查看每次运行的详细日志。

## 最佳实践

1. **明确需求格式**：在项目文档中说明如何编写Issue以获得最佳结果
2. **定期更新依赖**：确保使用最新版本的bella-issues-bot
3. **审查自动生成的代码**：虽然AI生成的代码通常很好，但人工审查仍然重要
4. **设置适当的标签**：使用标签来标记适合AI处理的Issues

## 相关文档

- [主项目文档](../README.md)
- [文件记忆系统文档](./README_FILE_MEMORY.md)
- [客户端文档](./README.md)
