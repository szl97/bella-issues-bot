# FileMemory 客户端

FileMemory 是 bella-issues-bot 的强大记忆系统组件之一，负责维护项目中所有文件的功能描述。通过 FileMemory，系统能够了解项目的整体结构和每个文件的作用，从而在处理用户需求时提供更加上下文相关的代码生成和修改。

## 特点与优势

- **文件功能描述**：自动分析并生成项目中每个文件的功能描述
- **智能增量更新**：只为新增和变更的文件生成描述，提高效率
- **Git 集成**：使用 Git 历史记录追踪文件变更
- **独立运行**：可以独立于主工作流运行，专注于文件记忆维护
- **批量处理**：智能地将文件分批处理，可处理大型项目
- **失败重试**：提供对失败文件的重试机制

## 安装

FileMemory 客户端作为 bella-issues-bot 的一部分安装:

```bash
pip install bella-issues-bot
```

## 使用方法

### 命令行使用

FileMemory 客户端提供了简单的命令行接口，可以独立运行：

```bash
# 基本用法 - 在当前目录初始化文件记忆
bella-file-memory

# 指定项目目录
bella-file-memory --project-dir /path/to/your/project

# 使用自定义 AI 模型
bella-file-memory --model gpt-4o --temperature 0.5
```

### 命令行参数

- `--project-dir`, `-p`: 项目目录路径（默认：当前目录）
- `--model`, `-m`: 用于生成文件描述的 AI 模型（默认：gpt-4o）
- `--temperature`, `-t`: AI 模型温度参数（默认：0.7）
- `--api-key`, `-k`: API 密钥（也可通过环境变量设置）
- `--base-url`, `-u`: API 基础 URL（可选）
- `--retry-failed`, `-r`: 是否重试之前失败的文件（默认：False）
- `--remote-url`, `--git-url`: Git 远程 URL（可选）
- `--auth-token`, `--git-token`: Git 认证令牌（可选）

### 编程方式使用

您也可以在 Python 代码中以编程方式使用 FileMemory：

```python
from client.file_memory_api import initialize_file_memory, update_file_descriptions

# 初始化文件记忆
file_memory = initialize_file_memory(
    project_dir="./my_project",
    model_name="gpt-4o",
    temperature=0.7
)

# 更新文件描述
descriptions = update_file_descriptions(file_memory)

# 处理之前失败的文件
failed_descriptions = process_failed_files(file_memory)
```

## 工作原理

FileMemory 的工作流程如下：

1. **初始化**：首次运行时，系统会创建 `.eng/memory` 目录结构
2. **文件扫描**：使用 Git 和文件系统 API 扫描项目中的所有文件
   - 默认遵循 `.gitignore` 规则
   - 可以通过 `.eng/.engignore` 文件指定额外的忽略规则
3. **变更检测**：通过比较 Git 提交 ID 检测自上次运行以来的变更
4. **批量处理**：
   - 将文件分成多个批次，每批包含多个文件
   - 批次大小基于行数、字符数和文件数的限制自动调整
   - 默认限制：每批最多 10,000 行、50,000 字符、20 个文件
5. **描述生成**：使用 AI 模型为每个文件生成功能描述
6. **存储**：将生成的描述保存在 `.eng/memory/file_details.txt` 中
7. **失败处理**：对于处理失败的文件，记录在单独的文件中，可以稍后重试

## 文件记忆格式

文件记忆以结构化文本格式存储在 `.eng/memory/file_details.txt` 中，每个文件的描述包括：

- 文件路径
- 文件类型
- 功能描述
- 关键组件（如类、函数等）
- 与其他文件的关系

示例记录：

```
File: core/file_memory.py
Type: Python
Description: 实现文件记忆系统，负责维护项目中所有文件的功能描述。提供文件扫描、描述生成和增量更新功能。
Components:
- FileMemoryConfig: 配置文件记忆管理的数据类
- FileDetail: 存储文件详细信息的类
- FileMemory: 主要类，管理文件描述的记忆系统
Relations:
- 依赖 core/git_manager.py 进行版本控制
- 依赖 core/ai.py 生成文件描述
```

## 配置文件

FileMemory 支持以下配置文件：

1. `.eng/.engignore`：类似于 `.gitignore`，指定要忽略的文件模式
2. `.eng/memory/failed_files.txt`：记录处理失败的文件，用于后续重试

## 最佳实践

1. **初始设置**：在项目开始时运行一次完整的文件记忆初始化
2. **定期更新**：在代码库有重大变更后更新文件记忆
3. **集成到 CI/CD**：将文件记忆更新集成到 CI/CD 流程中
4. **自定义忽略规则**：为大型项目创建 `.engignore` 文件，排除不需要分析的文件
5. **错误处理**：定期检查并重试失败的文件

## 故障排除

### 常见问题

1. **处理超时**：对于大型项目，可能需要增加批处理限制或分多次运行
2. **API 限制**：如果遇到 API 速率限制，可以降低并发请求数或使用重试机制
3. **内存不足**：处理非常大的文件可能导致内存不足，可以调整批处理大小

### 日志

FileMemory 客户端会生成详细的日志，默认保存在控制台输出中。可以通过设置环境变量 `LOG_LEVEL` 调整日志级别（DEBUG、INFO、WARNING、ERROR）。

## 示例

### 基本用法示例

```bash
# 初始化项目的文件记忆
cd /path/to/your/project
bella-file-memory

# 查看生成的文件描述
cat .eng/memory/file_details.txt
```

### 集成到 GitHub Actions 示例

```yaml
name: Update File Memory

on:
  push:
    branches: [ main ]

jobs:
  update-memory:
    runs-on: ubuntu-latest
    if: ${{ !contains(github.event.head_commit.message, '[skip memory]') || github.event_name == 'workflow_dispatch' }}
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install bella-issues-bot
      - name: Update file memory
        run: bella-file-memory
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      - name: Commit changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add .eng/memory/
          git commit -m "Update file memory [skip memory]" || echo "No changes to commit"
          git push
```

## 相关文档

- [主项目文档](../README.md)
- [GitHub 工作流文档](./README_GITHUB_WORKFLOWS.md)
- [客户端文档](./README.md)
