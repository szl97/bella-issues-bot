"""
Example showing how to run the workflow using the client runner API.
"""

from client.runner import run_workflow

# Example requirement
requirement = """
Create a simple README file with project description and usage instructions.
"""

# Run the workflow
run_workflow(
    issue_id=7,
    requirement=requirement,
    core_temperature=0.8,
    data_temperature=0.7
)
