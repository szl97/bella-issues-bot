"""Client package for running the WorkflowEngine from the terminal."""

# Export file memory functions for programmatic use
from client.file_memory_client import initialize_file_memory, update_file_descriptions, process_failed_files
from client.github_workflow_generator import generate_workflow_files
