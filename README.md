# bella-issues-bot

## 项目简介

bella-issues-bot 是一个基于人工智能的多功能代码开发助手，具备两种强大的工作模式：

1. **个人开发助手模式**：在日常开发过程中，作为命令行工具辅助编码，帮助分析代码、生成实现、解决技术难题。
2. **GitHub自动化模式**：集成到GitHub工作流中，自动监控和处理项目Issues，无需人工干预即可分析需求、提出解决方案并实现代码变更。

通过对项目结构的深入理解和强大的代码生成能力，bella-issues-bot 能够显著提高开发效率，减少重复工作，让您专注于更有创造性的任务。

## 主要功能

- 需求分析：自动理解和分解用户的功能需求
- 代码生成：根据需求生成符合项目风格的代码
- 版本管理：与Git集成，支持分支创建和代码提交
- GitHub集成：支持与GitHub仓库交互

### 个人开发模式特性

- 实时代码生成：根据描述快速生成代码片段或完整功能
- 智能问答：针对代码库回答技术问题，提供解释和建议

### GitHub自动化模式特性

- Issues自动处理：监听新Issues，自动分析需求并生成解决方案
- 代码审查：审查提交的代码，提出优化建议

## 安装方法

使用pip安装：

```bash
pip install bella-issues-bot
```

## 使用方法

bella-issues-bot 提供了多种使用方式：

### 个人开发模式

在日常开发中，您可以通过命令行界面或编程API使用bella-issues-bot：

### 命令行使用

```bash
bella-issues-bot --issue-id <问题ID> --requirement "你的需求描述"
```

更多高级选项和详细使用说明，请参考[客户端文档](./client/README.md)。

### 编程API使用

```python
from client.runner import run_workflow

run_workflow(
    issue_id=42,
    requirement="创建一个简单的README文件",
    core_temperature=0.7
)
```

## 配置环境变量

工具会读取以下环境变量：

- `OPENAI_API_KEY`: OpenAI API密钥
- `OPENAI_API_BASE`: OpenAI API基础URL
- `GITHUB_REMOTE_URL`: GitHub远程仓库URL
- `GITHUB_TOKEN`: GitHub身份验证令牌

## 示例

可以在[examples](./examples/)目录下找到使用示例。
