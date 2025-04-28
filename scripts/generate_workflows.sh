#!/bin/bash

# Script to generate GitHub workflow files for bella-issues-bot integration
# This script provides a simple interface to the workflow generator

show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -o, --output DIR        Output directory (default: current directory)"
    echo "  -b, --base-branch      Base branch for pull requests (default: main) "
    echo "  -m, --model MODEL       Default model for all operations (default: gpt-4o)"
    echo "  -t, --temp VALUE        Default temperature setting (default: 0.7)"
    echo "  -v, --version VERSION   Specific package version to install (e.g. '0.1.1')"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Additional options like --core-model, --data-model, etc. are also supported."
    echo "Run 'bella-github-workflows --help' for complete details."
    echo ""
}

# Check if script can be executed on current system
check_requirements() {
    if ! command -v python &> /dev/null; then
        echo "Error: Python is required but not found"
        exit 1
    fi
}
check_requirements

if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    show_help
    exit 0
fi

# Pass all arguments to the Python module
python -m client.github_workflow_generator "$@"
