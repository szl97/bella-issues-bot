# WorkflowEngine 客户端

一个强大的命令行接口和编程API，用于运行WorkflowEngine处理用户需求，支持个人开发助手模式和GitHub自动化工作流模式。

## 记忆与上下文管理

客户端依赖于强大的后台记忆系统，包括三个核心组件：

### 日志管理 (LogManager)

LogManager负责存储每次交互的详细记录：

- **结构化存储**：日志按issue ID和轮次有序组织，便于检索
- **完整性**：记录系统提示词、用户提示词、AI响应和文件修改
- **差异追踪**：保存每个修改文件的完整差异信息

所有日志保存在项目的`.eng/memory`目录下，按照`issues/#<issue-id>/round_<num>`格式组织，可随时查看历史交互。

### 版本管理 (VersionManager)

VersionManager提供智能版本控制功能：

- **历史分析**：自动提取历史轮次的数据形成上下文
- **需求整合**：在新需求与历史需求有冲突时，提供智能整合
- **版本回退**：根据需要自动执行版本回退操作

每次启动新的需求处理时，系统会：
1. 提取过去所有轮次的需求和响应
2. 格式化为结构化历史记录
3. 分析新需求与历史的关系
4. 决定是保持当前状态还是执行回退

### 文件记忆 (FileMemory)

FileMemory为AI提供项目文件的深度理解：

- **自动描述**：为项目中的每个文件生成功能描述
- **增量更新**：只更新被修改的文件描述，提高效率
- **批量处理**：使用智能分批策略处理大型代码库
- **失败处理**：对无法处理的文件提供重试机制

当工作流运行时，系统会：
1. 检测新建或修改的文件
2. 使用AI生成这些文件的功能描述
3. 将描述保存在`.eng/memory/file_details.txt`中
4. 在后续需求处理时提供这些描述作为上下文

## 工作模式

bella-issues-bot 支持两种主要工作模式：

- **客户端模式 (client)**：默认模式，适合作为个人开发助手使用，每次运行时基于project_dir目录下的当前代码状态进行操作。
- **机器人模式 (bot)**：专为GitHub集成设计，会在project_dir目录下创建临时目录作为工作区，自动拉取issues对应的最新分支状态，处理完成后自动提交更改并在Issues中回复处理结果，最后清理临时工作区。

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

- Python 3.10 或更高版本 (< 3.13)
- Git 客户端
- OpenAI API 密钥

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

- `--issue-id -i`：（必需）问题ID，用于跟踪和引用
- `--requirement -r` 或 `--requirement-file -f`：（必需）具体需求描述或包含需求的文件路径
- `--project-dir -p`：项目目录路径（默认：当前目录）

#### AI模型配置

- `--model -m`： 同时配置核心模型和数据模型
- `--temperature -t`： 同时配置核心模型和数据模型温度
- `--core-model --cm`：核心AI操作使用的模型（默认：gpt-4o）
- `--data-model --dm`：数据操作使用的模型（默认：gpt-4o）
- `--core-temperature --ct`：核心模型的温度参数（默认：0.7）
- `--data-temperature --dt`：数据模型的温度参数（默认：0.7）

#### 工作流配置

- `--mode`：工作模式，可选"client"或"bot"（默认：client）
  - `client`：个人开发助手模式，基于当前代码状态工作
  - `bot`：GitHub自动化模式，拉取最新分支，自动提交并回复Issues
- `--default-branch --branch`：默认Git分支（默认：main）
- `--base-url -u`：API调用的基础URL
- `--api-key -k`：API密钥（也可以通过OPENAI_API_KEY环境变量设置）
- `--github-remote-url --git-url`：GitHub远程URL
- `--github-token --git-token`：GitHub令牌

#### 执行控制

- `--max-retry`：最大重试次数（默认：3）

### 示例命令

```bash
# 基本用法
bella-issues-bot --issue-id 123 --requirement "添加用户认证功能"

# 从文件读取需求
bella-issues-bot --issue-id 123 --requirement-file requirements.txt

# 自定义模型和温度
bella-issues-bot --issue-id 123 --requirement "优化数据库查询" --core-model gpt-4o --core-temperature 0.5

# GitHub机器人模式
bella-issues-bot --issue-id 123 --requirement "修复登录bug" --mode bot --github-token YOUR_TOKEN
```

### 简易脚本使用

你也可以使用提供的脚本简化命令行调用：

```bash
./scripts/run_bot.sh <问题ID> [需求文件路径]
```

## 编程方式使用

你也可以在Python代码中以编程方式使用客户端包：

```python
from client.runner import run_workflow

# 基本用法
result = run_workflow(
    issue_id=42,
    requirement="为项目创建一个README文件",
    project_dir="./my_project"
)
print(f"处理结果: {result}")

# 高级配置
result = run_workflow(
    issue_id=123,
    requirement="实现用户注册功能",
    project_dir="./my_project",
    core_model="gpt-4o",
    data_model="gpt-4o",
    core_temperature=0.7,
    data_temperature=0.5,
    mode="client",
    max_retry=5,
    default_branch="develop",
    github_remote_url="https://github.com/username/repo.git",
    github_token="your_github_token"
)
```

## 环境变量

工具会读取以下环境变量：

- `OPENAI_API_KEY`：OpenAI的API密钥（必需）
- `OPENAI_API_BASE`：OpenAI API的基础URL（可选）
- `GITHUB_REMOTE_URL`：GitHub远程仓库URL（可选，用于bot模式）
- `GITHUB_TOKEN`：GitHub身份验证令牌（可选，用于bot模式）

## 配置文件

除了命令行参数和环境变量外，bella-issues-bot 还支持以下配置文件：

- `.eng/config.json`：项目级配置文件，可以设置默认参数
- `.eng/.engignore`：指定文件记忆系统应忽略的文件模式

## 工作流程详解

### 个人开发助手模式 (client)

1. **初始化**：创建工作流引擎，设置项目目录和AI配置
2. **文件记忆**：检查并更新文件记忆系统
3. **版本管理**：分析历史需求和当前需求的关系
4. **需求处理**：使用AI分析需求并生成代码修改
5. **代码实现**：应用生成的代码修改到项目文件
6. **日志记录**：保存完整的交互历史和文件修改

### GitHub自动化模式 (bot)

1. **初始化**：创建临时工作目录
2. **分支管理**：创建或检出与Issue相关的分支
3. **需求处理**：与client模式相同，但在临时目录中操作
4. **代码提交**：自动提交代码修改
5. **拉取请求**：创建拉取请求到默认分支
6. **Issue回复**：在原Issue中添加处理结果的评论
7. **清理**：删除临时工作目录

## 输出与日志

bella-issues-bot 生成以下输出：

1. **控制台输出**：显示处理进度和结果
2. **日志文件**：保存在 `.eng/memory/issues/#<issue-id>/round_<num>/` 目录下
   - `system_prompt.txt`：系统提示词
   - `user_prompt.txt`：用户提示词
   - `response.txt`：AI响应
   - `diff/`：文件修改差异

## 最佳实践

1. **明确需求**：提供清晰、具体的需求描述
2. **使用Issue ID**：为不同的需求使用不同的Issue ID
3. **初始化文件记忆**：首次使用前运行 `bella-file-memory`
4. **审查代码**：检查AI生成的代码，确保符合预期
5. **增量开发**：将复杂需求分解为多个小步骤

## 故障排除

### 常见问题

1. **API密钥错误**：确保OPENAI_API_KEY环境变量正确设置
2. **Git错误**：检查Git配置和权限
3. **文件记忆问题**：如果文件描述不准确，尝试重新运行 `bella-file-memory`
4. **模型限制**：如果遇到模型容量限制，尝试将需求分解为更小的部分

### 日志和调试

设置环境变量 `LOG_LEVEL=DEBUG` 可以获取更详细的日志输出，帮助诊断问题。

## 相关文档

- [主项目文档](../README.md)
- [文件记忆系统文档](./README_FILE_MEMORY.md)
- [GitHub工作流文档](./README_GITHUB_WORKFLOWS.md)