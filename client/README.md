# Workflow 客户端

一个强大的命令行接口和编程API，用于运行WorkflowEngine处理用户需求，支持个人开发助手模式和GitHub自动化工作流模式。

## 工作模式

bella-issues-bot 支持两种主要工作模式：

- **客户端模式 (client)**：默认模式，适合作为个人开发助手使用，每次运行时基于project_dir目录下的当前代码状态进行操作。
- **机器人模式 (bot)**：专为GitHub集成设计，会在project_dir目录下创建临时目录作为工作区，自动拉取issues对应的最新分支状态，处理完成后自动提交更改并在Issues中回复处理结果，最后清理临时工作区。
## 命令行使用方式（个人开发助手模式）

你可以通过以下两种方式从命令行运行WorkflowEngine：

### 使用安装后的CLI命令

```bash
bella-issues-bot --issue-id 42 --requirement "创建一个README文件"
```

### 直接使用Python模块

```bash
python -m client.terminal --issue-id 42 --requirement "创建一个README文件"
```

### 命令行参数

#### 基础参数

- `--issue-id`：（必需）问题ID，用于跟踪和引用
- `--requirement` 或 `--requirement-file`：（必需）具体需求描述或包含需求的文件路径
- `--project-dir`：项目目录路径（默认：当前目录）

#### AI模型配置

- `--core-model`：核心AI操作使用的模型（默认：gpt-4o）
- `--data-model`：数据操作使用的模型（默认：gpt-4o）
- `--core-temperature`：核心模型的温度参数（默认：0.7）
- `--data-temperature`：数据模型的温度参数（默认：0.7）

#### 工作流配置

- `--mode`：工作模式，可选"client"或"bot"（默认：client）
  - `client`：个人开发助手模式，基于当前代码状态工作
  - `bot`：GitHub自动化模式，拉取最新分支，自动提交并回复Issues
- `--default-branch`：默认Git分支（默认：main）
- `--base-url`：API调用的基础URL
- `--api-key`：API密钥（也可以通过OPENAI_API_KEY环境变量设置）
- `--github-remote-url`：GitHub远程URL
- `--github-token`：GitHub令牌

#### 执行控制

- `--max-retry`：最大重试次数（默认：3）

### 简易脚本使用

你也可以使用提供的脚本简化命令行调用：

```bash
./scripts/run_bot.sh <问题ID> [需求文件路径]
```

## 编程方式使用

你也可以在Python代码中以编程方式使用客户端包：

```python
from client.runner import run_workflow

run_workflow(
    issue_id=42,
    requirement="为项目创建一个README文件",
    core_model="gpt-4o",
    data_model="gpt-4o",
    core_temperature=0.7,
    data_temperature=0.7
)
```

## 环境变量

工具会读取以下环境变量：

- `OPENAI_API_KEY`：OpenAI的API密钥
- `OPENAI_API_BASE`：OpenAI API的基础URL
- `GITHUB_TOKEN`：GitHub身份验证令牌
