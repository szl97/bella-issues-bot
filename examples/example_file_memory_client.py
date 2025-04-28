"""
Example demonstrating how to use the FileMemory client without LogManager.

This example shows how to:
1. Initialize FileMemory with only GitManager
2. Update file descriptions
3. Process previously failed files
"""

import os
import logging
from pathlib import Path

from dotenv import load_dotenv

from client.file_memory_api import init_file_memory, update_file_descriptions, process_failed_files
from core.log_config import setup_logging


def main():
    # Setup logging
    setup_logging(log_level=logging.INFO)
    
    # Load environment variables
    load_dotenv()
    
    # Set project directory (this example uses the parent directory of this file)
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    print(f"Initializing FileMemory for project: {project_dir}")
    
    # Initialize FileMemory using only GitManager (no LogManager)
    file_memory = init_file_memory(
        project_dir=project_dir,
        model_name="gpt-4o",
        temperature=0.7
    )
    
    # Update file descriptions
    print("Updating file descriptions...")
    update_file_descriptions(file_memory)
    

if __name__ == "__main__":
    main()
