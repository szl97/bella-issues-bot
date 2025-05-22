# bella-issues-bot 使用指南

中文 | [English](./quick-start.en.md)

在GitHub上使用bella-issues-bot项目，您可以执行以下主要操作：

## 1. 作为个人开发助手

### 安装项目
```bash
# 通过pip安装
pip install bella-issues-bot

# 或从源码安装
git clone https://github.com/szl97/bella-issues-bot.git
cd bella-issues-bot
pip install -e .
```

### 初始化文件记忆系统
```bash
# 分析您的项目文件并生成描述信息
bella-file-memory --project-dir ./your-project
```

### 使用AI助手处理需求
```bash
# 基本使用 - 提出问题或请求代码修改
bella-issues-bot --issue-id 123 --requirement "实现一个新的日志记录功能"

# 自定义模型和温度
bella-issues-bot --issue-id 123 --requirement "优化文件读取性能" --core-model gpt-4o --core-temperature 0.5
```

## 2. 集成GitHub工作流

### 生成GitHub Actions工作流配置
```bash
# 生成默认配置
bella-github-workflows

# 自定义基础分支和模型
bella-github-workflows --base-branch develop --model gpt-4o
```

这将在`.github/workflows/`目录中创建两个工作流文件：
- `memory_init.yml` - 自动分析项目文件并维护文件记忆
- `issue_process.yml` - 自动处理Issue中的需求

### 配置GitHub仓库权限

在仓库的Settings中设置：
1. 添加必要的Secrets（`OPENAI_API_KEY`）
2. 启用Actions的读写权限和PR创建权限

## 3. 使用GitHub Issues获取AI协助

一旦集成了GitHub工作流，您可以：

1. 创建一个新Issue描述您的需求
2. AI助手会自动：
    - 分析您的需求
    - 在专用分支上实现代码
    - 创建拉取请求
    - 在Issue中回复处理结果

## 4. 使用编程API

在Python代码中使用：

```python
from client.runner import run_workflow

# 处理需求并生成代码
run_workflow(
    issue_id=123,
    requirement="添加单元测试覆盖核心功能",
    project_dir="./my_project",
    core_model="gpt-4o"
)
```

## 5. 配置项目

### 环境变量设置
```
OPENAI_API_KEY=your_api_key
OPENAI_API_BASE=https://api.openai.com/v1  # 可选，自定义API端点
GITHUB_REMOTE_URL=https://github.com/username/repo.git  # 用于GitHub集成
GITHUB_TOKEN=your_github_token  # 用于GitHub集成
```

### 项目配置文件
- `.eng/system.txt` - 自定义AI提示词
- `.eng/.engignore` - 类似`.gitignore`，指定记忆系统应忽略的文件

bella-issues-bot提供了强大的AI代码开发助手功能，无论是作为个人开发工具还是GitHub自动化机器人，都能显著提高开发效率，减少重复工作。