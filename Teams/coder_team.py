from agno.team import Team
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.file import FileTools
from agno.tools.shell import ShellTools
from agno.tools.python import PythonTools
from pathlib import Path


# Define the Coder Agent
coder = Agent(
    model=Groq(id="deepseek-r1-distill-llama-70b"),
    name="Coder",
    role="Senior Software Developer",
    description=(
        "You are an expert software developer with deep knowledge of multiple programming languages, "
        "design patterns, and best practices. You write clean, efficient, and well-documented code."
    ),
    tools=[PythonTools(base_dir=Path("./projects"))],
    instructions=[
        "Write the core application code with proper architecture.",
        "Create HTML, CSS, and JavaScript files for the landing page.",
        "Ensure the code is responsive and follows best practices.",
        "Include necessary meta tags and viewport settings.",
        "Write clean, well-structured, and documented code.",
        "Consider edge cases and error handling.",
        "Once code is written, explicitly state 'CODE WRITING COMPLETED'."
    ],
    add_datetime_to_instructions=True,
)

# Define the File Manager Agent
file_manager = Agent(
    model=Groq(id="deepseek-r1-distill-llama-70b"),
    name="FileManager",
    role="File Operations Specialist",
    description=(
        "You are responsible for all file and directory operations. You create, organize, "
        "and manage project structure efficiently."
    ),
    tools=[FileTools(base_dir=Path("./projects"))],
    instructions=[
        "Create a single project folder named 'landing-page' in the './projects' directory.",
        "Create the following structure:",
        "  - index.html",
        "  - styles.css",
        "  - script.js",
        "  - README.md",
        "Create each file only once.",
        "After creating all files, explicitly state 'FILE CREATION COMPLETED'.",
        "Do not modify files after creation unless specifically requested."
    ],
    add_datetime_to_instructions=True,
)

# Define the Shell Operations Agent
shell_operator = Agent(
    model=Groq(id="deepseek-r1-distill-llama-70b"),
    name="ShellOperator", 
    role="System and Environment Manager",
    description=(
        "You are an expert in command-line operations, environment setup, and system administration. "
        "You handle all shell commands, package installation, and environment configuration."
    ),
    tools=[ShellTools(), PythonTools(base_dir=Path("./projects"))],
    instructions=[
        "Create the './projects' directory if it doesn't exist.",
        "Verify that all required files are present.",
        "Test the landing page by opening it in a browser.",
        "After verification, explicitly state 'VERIFICATION COMPLETED'.",
        "Do not run additional commands unless there are errors to fix."
    ],
    add_datetime_to_instructions=True,
)

# Create the Coder Team in coordinate mode
coder_team = Team(
    name="Development Team",
    mode="coordinate",
    model=Groq(id="deepseek-r1-distill-llama-70b"),
    members=[coder, file_manager, shell_operator],
    description=(
        "You are a senior development team lead coordinating a complete software development process. "
        "Your goal is to deliver high-quality, working software solutions from conception to deployment."
    ),
    instructions=[
        "Follow these steps in order:",
        "1. Ask FileManager to create the project structure",
        "2. Wait for 'FILE CREATION COMPLETED'",
        "3. Ask Coder to write the code",
        "4. Wait for 'CODE WRITING COMPLETED'",
        "5. Ask ShellOperator to verify the setup",
        "6. Wait for 'VERIFICATION COMPLETED'",
        "7. Conclude with 'PROJECT COMPLETED SUCCESSFULLY'",
        "Do not proceed to the next step until the current step is completed.",
        "If any step fails, stop and report the error."
    ],
    success_criteria=(
        "all files are created, code is written, and verification is completed"
    ),
    add_datetime_to_instructions=True,
    add_member_tools_to_system_message=False,
    enable_agentic_context=True,
    share_member_interactions=True,
    show_members_responses=True,
    markdown=True,
)

# Example usage
if __name__ == "__main__":
    # Create a responsive landing page
    try:
        # Run the team with streaming enabled
        response_stream = coder_team.run(
            "create a basic landing page for a website and it should be in html, css, js and it should be responsive",
            stream=True,
            stream_intermediate_steps=True
        )
        
        # Process the response stream
        for event in response_stream:
            if hasattr(event, 'content'):
                print(event.content)
            elif hasattr(event, 'event'):
                print(f"Event: {event.event}")
            else:
                print(f"Response: {event}")
                
    except Exception as e:
        print(f"Error occurred: {str(e)}")
