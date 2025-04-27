#!/bin/bash

# 启动bella-issues-bot的帮助脚本
# 此脚本简化了命令行参数的输入，便于快速使用

# 检查是否提供了issue-id参数
if [ -z "$1" ]; then
    echo "使用方法: $0 <issue-id> [需求文件路径]"
    echo ""
    echo "示例:"
    echo "  $0 42 ./requirements.txt  # 使用文件中的需求"
    echo "  $0 42                    # 将会要求您输入需求"
    exit 1
fi

python -m client.terminal --issue-id "$1" ${2:+--requirement-file "$2"}
