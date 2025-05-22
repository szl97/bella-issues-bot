"""
Terminal utilities for improving console output formatting and styling.
Provides functions for colorful and well-structured terminal output.
"""
import os
import shutil
from typing import Optional, Dict, Any, List, Union

# Check if colorama is available and use it for Windows compatibility
try:
    from colorama import init, Fore, Back, Style
    init()  # Initialize colorama
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False
    # Fallback color codes
    class DummyColors:
        def __getattr__(self, name):
            return ""
    Fore = DummyColors()
    Back = DummyColors()
    Style = DummyColors()

# Terminal size detection
def get_terminal_size():
    """Get the terminal size"""
    return shutil.get_terminal_size((80, 20))  # Default to 80x20 if detection fails

# Color definitions for different message types
COLORS = {
    'title': Fore.CYAN + Style.BRIGHT,
    'info': Fore.GREEN,
    'warning': Fore.YELLOW,
    'error': Fore.RED + Style.BRIGHT,
    'success': Fore.GREEN + Style.BRIGHT,
    'prompt': Fore.BLUE + Style.BRIGHT,
    'file': Fore.MAGENTA,
    'key': Fore.YELLOW,
    'value': Fore.WHITE,
    'code': Fore.CYAN,
    'diff_add': Fore.GREEN,
    'diff_remove': Fore.RED,
    'diff_context': Fore.WHITE,
    'reset': Style.RESET_ALL
}

def print_header(title: str, width: Optional[int] = None, char: str = "=", color: str = 'title') -> None:
    """
    Print a header with a title centered in a line of characters.
    
    Args:
        title: The title to display
        width: Width of the header (defaults to terminal width)
        char: Character to use for the line (default: =)
        color: Color name to use from COLORS dict
    """
    if width is None:
        width = get_terminal_size().columns
    
    padding = max(2, (width - len(title) - 2) // 2)
    header = char * padding + " " + title + " " + char * padding
    # Ensure the header fills the width
    header = header + char * (width - len(header))
    
    print(f"{COLORS[color]}{header}{COLORS['reset']}")

def print_subheader(title: str, color: str = 'info') -> None:
    """Print a smaller section header"""
    print(f"\n{COLORS[color]}▶ {title}{COLORS['reset']}")

def print_key_value(key: str, value: Any, indent: int = 0) -> None:
    """Print a key-value pair with appropriate styling"""
    indent_str = " " * indent
    print(f"{indent_str}{COLORS['key']}{key}:{COLORS['reset']} {COLORS['value']}{value}{COLORS['reset']}")

def print_file_info(file_path: str, details: Optional[str] = None) -> None:
    """Print information about a file with styling"""
    print(f"{COLORS['file']}📄 {file_path}{COLORS['reset']}")
    if details:
        print(f"   {details}")

def print_code_block(code: str, language: str = "python", indent: int = 2) -> None:
    """Print a formatted code block with syntax coloring indication"""
    indent_str = " " * indent
    width = get_terminal_size().columns - indent
    
    # Print code block header
    print(f"{indent_str}{COLORS['code']}"