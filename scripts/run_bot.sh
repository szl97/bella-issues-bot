#!/bin/bash

# 启动bella-issues-bot的帮助脚本
# 此脚本简化了命令行参数的输入，便于快速使用
# 支持简化的参数选项，调用Python客户端模块

show_help() {
    echo "使用方法: $0 <issue-id> [选项] [需求文件路径]"
    echo ""
    echo "必需参数:"
    echo "  <issue-id>               问题ID（必填）"
    echo ""
    echo "选项:"
    echo "  -m, --model MODEL        同时设置core和data模型名称"
    echo "  -t, --temperature TEMP          同时设置core和data模型温度"
    echo "  --cm, --core-model MODEL 单独设置core模型名称"
    echo "  --dm, --data-model MODEL 单独设置data模型名称"
    echo "  --ct, --core-temperature TEMP   单独设置core模型温度"
    echo "  --dt, --data-temperature TEMP   单独设置data模型温度"
    echo "  -k, --key KEY            设置API密钥"
    echo "  -h, --help               显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 42 ./requirements.txt             # 使用文件中的需求"
    echo "  $0 42 -m gpt-4-turbo                # 设置所有模型为gpt-4-turbo"
    echo "  $0 42 -m gpt-4-turbo -t 0.9         # 设置所有模型为gpt-4-turbo，温度为0.9"
    echo "  $0 42 --cm gpt-4-turbo --dm gpt-3.5-turbo  # 分别设置不同模型"
    echo ""
}

# 检查是否请求帮助
if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    show_help
    exit 0
fi

# 检查是否提供了issue-id参数
if [ -z "$1" ] || [[ "$1" == -* ]]; then
    echo "错误: 必须提供issue-id作为第一个参数"
    show_help
    exit 1
fi

ISSUE_ID=$1
shift  # 移除第一个参数，使其他参数可以按顺序处理

# 检查最后一个参数是否是一个文件（不以连字符开头）
ARGS=("$@")
if [ ${#ARGS[@]} -gt 0 ] && [[ ! "${ARGS[-1]}" == -* ]] && [ -f "${ARGS[-1]}" ]; then
    python -m client.terminal -i $ISSUE_ID --requirement-file "${ARGS[-1]}" "${ARGS[@]:0:${#ARGS[@]}-1}"
else
    python -m client.terminal -i $ISSUE_ID "$@"
fi
