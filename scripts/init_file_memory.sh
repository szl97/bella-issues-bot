#!/bin/bash

# Script to initialize file memory using GitManager (without LogManager)
# This script helps to run the bella-file-memory command with common options

show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -d, --directory DIR    Set project directory (default: current directory)"
    echo "  -m, --model MODEL      Set AI model (default: gpt-4o)"
    echo "  -t, --temp VALUE       Set temperature (default: 0.7)"
    echo "  -f, --failed-only      Process only previously failed files"
    echo "  -h, --help             Show this help message"
    echo ""
}

if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    show_help
    exit 0
fi

# Pass all arguments to the Python module
python -m client.file_memory_client "$@"

# Exit with the same status code as the Python command
exit $?
