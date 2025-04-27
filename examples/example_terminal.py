"""
Example showing how to run the workflow from both terminal and programmatically.

To run from terminal:
python -m client.terminal --issue-id 42 --requirement "Create a README file"

Or programmatically as shown below:
"""

from client.runner import run_workflow


def example_run():
    """Example of running the workflow programmatically."""
    requirement = """
    Create a simple README file with project description and setup instructions.
    """
    
    run_workflow(issue_id=42, requirement=requirement)


if __name__ == "__main__":
    example_run()
