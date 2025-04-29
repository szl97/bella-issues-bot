# bella-issues-bot

- [![Static Badge](https://img.shields.io/badge/doc-deepwiki-blue?style=flat-square)](https://deepwiki.com/szl97/bella-issues-bot)
- [![Static Badge](https://img.shields.io/badge/support-BellaOpenAPI-%23C76300?style=flat-square)](https://github.com/LianjiaTech/bella-openapi)

## 项目简介

bella-issues-bot 是一个基于人工智能的多功能代码开发助手，具备两种强大的工作模式：

1. **个人开发助手模式**：在日常开发过程中，作为命令行工具辅助编码，帮助分析代码、生成实现、解决技术难题。
2. **GitHub自动化模式**：集成到GitHub工作流中，自动监控和处理项目Issues，无需人工干预即可分析需求、提出解决方案并实现代码变更。

通过对项目结构的深入理解和强大的代码生成能力，bella-issues-bot 能够显著提高开发效率，减少重复工作，让您专注于更有创造性的任务。

## 主要功能

- **需求分析**：自动理解和分解用户的功能需求，确定所需的代码修改
- **代码生成**：根据需求生成符合项目风格的代码，自动实现新功能或修复问题
- **版本管理**：与Git深度集成，支持分支创建、代码提交和拉取请求的自动管理
- **记忆系统**：记录项目文件描述和操作历史，提供上下文感知能力，持续改进代码质量

### 典型使用场景

- **日常开发辅助**：在本地开发过程中，使用命令行工具快速生成代码、解决技术问题
- **项目自动化**：集成到GitHub工作流，实现Issue的自动处理和代码实现
- **代码文档生成**：自动分析项目文件并生成详细的功能描述
- **技术难题解决**：分析项目上下文后，针对性地提供解决方案

## 记忆与上下文管理

bella-issues-bot 配备了强大的记忆系统，由三个核心组件构成：

### 记忆系统的工作流程

1. **初始化阶段**：首次运行时，系统会扫描整个项目并为每个文件生成详细描述
2. **增量更新**：后续运行时，只会更新新增或修改的文件描述，提高效率
3. **上下文提取**：处理用户需求时，系统根据需求内容选择相关文件作为上下文

### 1. 日志管理 (LogManager)

LogManager 负责记录每次交互的完整历史，包括：
- 系统提示词和用户需求
- AI响应内容
- 文件修改记录和差异对比

这些日志按issue和轮次组织，支持历史追溯和问题诊断。每轮交互都会生成详细日志，便于追踪AI的决策过程和代码修改历史。

### 2. 版本管理 (VersionManager)

VersionManager 提供智能的版本控制功能：
- 自动提取历史轮次的需求和响应
- 生成格式化的历史执行记录作为上下文
- 分析当前需求与历史需求的关系
- 根据需要执行版本回退操作

系统会分析新需求与先前修改的关系，判断是否需要回滚，确保代码修改的连贯性和一致性。

### 3. 文件记忆 (FileMemory)

FileMemory 模块为项目的每个文件维护详细描述：
- 自动生成文件功能、结构和关系描述
- 跟踪文件变更，更新受影响文件的描述
- 提供上下文相关的文件选择
- 支持配置忽略文件，默认包含项目的.gitignore，支持自定义添加.eng/.engignore

这使得AI助手能够理解整个代码库的结构和功能，在修改代码时考虑到更广泛的项目上下文。

## 安装方法

### 通过 pip 安装

```bash
pip install bella-issues-bot
```

### 从源码安装

```bash
git clone https://github.com/szl97/bella-issues-bot.git
cd bella-issues-bot
pip install -e .
```

## 系统要求

- Python 3.10 或更高版本（<3.13）
- Git 客户端（用于版本控制功能）
- OpenAI API 密钥（用于 AI 功能）

## 配置文件

bella-issues-bot 支持多种配置方式：

### 环境变量配置

工具会读取以下环境变量：

- `OPENAI_API_KEY`: OpenAI API密钥（必需）
- `OPENAI_API_BASE`: OpenAI API基础URL（可选，用于自定义API端点）
- `GITHUB_REMOTE_URL`: GitHub远程仓库URL（可选，用于GitHub集成）
- `GITHUB_TOKEN`: GitHub身份验证令牌（可选，用于GitHub集成）

### 项目配置文件


- `.eng/system.txt`: 配置代码工程师的提示词
- `.eng/.engignore`: 类似于 `.gitignore`，用于指定文件记忆系统应忽略的文件

示例 `.engignore` 文件:
```
# 忽略所有日志文件
*.log

# 忽略构建目录
/build/
/dist/

# 忽略虚拟环境
/venv/
/.venv/

# 忽略缓存文件
__pycache__/
*.py[cod]
*$py.class
```

## 详细使用示例

### 0. 进入您的项目目录

### 1. 初始化文件记忆系统

首次使用前，建议初始化文件记忆系统，这将帮助 AI 理解您的项目结构：

```bash
# 在项目根目录执行
bella-file-memory --project-dir .
```

这将分析您的项目文件并生成描述信息，存储在 `.eng/memory/file_details.txt` 中。

### 2. 作为个人开发助手使用

```bash
# 基本使用
bella-issues-bot --issue-id 123 --requirement "实现一个新的日志记录功能"

# 使用自定义模型和温度
bella-issues-bot --issue-id 123 --requirement "优化文件读取性能" --core-model gpt-4o --core-temperature 0.5
```

### 3. 设置 GitHub 工作流

为您的项目生成 GitHub Actions 工作流配置：

```bash
# 生成默认工作流配置
bella-github-workflows

# 自定义基础分支和模型
bella-github-workflows --base-branch develop --model gpt-4o
```

生成的工作流文件将保存在 `.github/workflows/` 目录中。

### 4. 使用编程 API

```python
from client.runner import run_workflow

# 基本使用
run_workflow(
    issue_id=123,
    requirement="添加单元测试覆盖核心功能",
    project_dir="./my_project"
)

# 高级配置
run_workflow(
    issue_id=123,
    requirement="重构数据处理模块以提高性能",
    project_dir="./my_project",
    core_model="gpt-4o",
    data_model="gpt-4o",
    core_temperature=0.7,
    data_temperature=0.5,
    mode="client",  # 或 "bot" 用于 GitHub 自动化
    max_retry=5
)
```

## 项目结构

```
bella-issues-bot/
├── core/               # 核心功能模块
│   ├── ai.py           # AI 助手接口
│   ├── file_memory.py  # 文件记忆系统
│   ├── git_manager.py  # Git 版本控制
│   └── workflow_engine.py  # 工作流引擎
├── client/             # 客户端接口
│   ├── terminal.py     # 命令行界面
│   ├── file_memory_client.py  # 文件记忆客户端
│   └── github_workflow_generator.py  # GitHub 工作流生成器
└── examples/           # 使用示例
```
