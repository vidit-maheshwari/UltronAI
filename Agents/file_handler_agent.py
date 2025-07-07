# Agents/file_handler_agent.py

from agno.utils.log import log_info
from pathlib import Path
import dotenv
from typing import Dict, Any, List, Optional
import re
import json
from shared_state import SharedState

dotenv.load_dotenv()

class FileAgentNode:
    """
    An intelligent file operations agent that can create complex project structures,
    handle file content awareness, and prevent accidental data loss.
    """
    def __init__(self):
        log_info("Initialized intelligent FileAgentNode.")
        
        # Common project structure templates
        self.project_templates = {
            "python_package": {
                "description": "Standard Python package structure",
                "structure": [
                    "setup.py",
                    "requirements.txt", 
                    "README.md",
                    "src/__init__.py",
                    "src/main.py",
                    "tests/__init__.py",
                    "tests/test_main.py",
                    ".gitignore"
                ]
            },
            "web_project": {
                "description": "Standard web project structure",
                "structure": [
                    "index.html",
                    "styles.css",
                    "script.js",
                    "assets/",
                    "README.md"
                ]
            },
            "react_app": {
                "description": "React application structure",
                "structure": [
                    "package.json",
                    "public/index.html",
                    "src/App.js",
                    "src/index.js",
                    "src/components/",
                    "src/styles/",
                    "README.md"
                ]
            },
            "node_backend": {
                "description": "Node.js backend structure",
                "structure": [
                    "package.json",
                    "server.js",
                    "routes/",
                    "models/",
                    "middleware/",
                    "config/",
                    ".env",
                    "README.md"
                ]
            }
        }

    def _detect_project_type(self, task: str) -> str:
        """Intelligently detect the type of project based on the task description."""
        task_lower = task.lower()
        
        # Check for explicit React/component keywords first
        if any(keyword in task_lower for keyword in ["react", "component", "jsx", "tsx", "create-react-app"]):
            return "react_app"
        
        # Check for backend/server keywords
        elif any(keyword in task_lower for keyword in ["api", "backend", "server", "express", "node", "database", "mongodb", "postgresql"]):
            return "node_backend"
        
        # Check for Python-specific keywords (more specific to avoid false positives)
        elif any(keyword in task_lower for keyword in ["python script", "python package", "python module", "django", "flask", "fastapi", "pip install", "requirements.txt"]):
            return "python_package"
        
        # Check for portfolio/website keywords (should be web_project) - HIGH PRIORITY
        elif any(keyword in task_lower for keyword in ["portfolio", "resume", "cv", "personal website", "landing page", "single page", "html format", "css and javascript"]):
            return "web_project"
        
        # Check for general web keywords
        elif any(keyword in task_lower for keyword in ["html", "css", "javascript", "website", "web page", "responsive", "mobile friendly"]):
            return "web_project"
        
        # Default to web_project for most cases (safer default)
        else:
            return "web_project"

    def _create_intelligent_project_structure(self, shared_state: 'SharedState') -> Dict[str, Any]:
        """Creates an intelligent project structure based on the task type."""
        try:
            # Detect project type
            project_type = self._detect_project_type(shared_state.original_task)
            template = self.project_templates.get(project_type, self.project_templates["web_project"])
            
            log_info(f"Task: '{shared_state.original_task}'")
            log_info(f"Detected project type: {project_type}")
            log_info(f"Using template: {template['description']}")
            
            # Generate project name
            original_task = shared_state.original_task.lower()
            words = [word for word in original_task.split() if word.isalnum()]
            project_name = "-".join(words[:3]) if words else "new-project"
            
            base_projects_dir = Path.cwd() / "projects"
            base_projects_dir.mkdir(exist_ok=True)

            project_dir = base_projects_dir / project_name
            project_dir.mkdir(exist_ok=True)
            
            # Create the intelligent structure
            created_files = []
            for item in template["structure"]:
                item_path = project_dir / item
                
                if item.endswith("/"):
                    # Create directory
                    item_path.mkdir(parents=True, exist_ok=True)
                    log_info(f"Created directory: {item_path}")
                else:
                    # Create file with appropriate content
                    item_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Generate intelligent default content based on file type
                    default_content = self._generate_default_content(item, project_name)
                    
                    with open(item_path, 'w', encoding='utf-8') as f:
                        f.write(default_content)
                    
                    created_files.append(str(item_path))
                    log_info(f"Created file: {item_path}")
            
            log_info(f"Intelligent project structure created at: {project_dir}")
            log_info(f"Project type detected: {project_type}")
            
            return {
                "status": "success",
                "output": f"Intelligent {template['description']} structure created for '{project_name}'.",
                "project_directory": project_dir,
                "project_type": project_type,
                "created_files": created_files
            }
        except Exception as e:
            log_info(f"Error creating intelligent project structure: {e}")
            return {"status": "error", "error": str(e)}

    def _generate_default_content(self, filename: str, project_name: str) -> str:
        """Generate intelligent default content for common file types."""
        if filename == "README.md":
            return f"""# {project_name.replace('-', ' ').title()}

## Description
{project_name.replace('-', ' ').title()} - A professional project.

## Getting Started
1. Clone this repository
2. Follow the setup instructions below

## Setup
[Add setup instructions here]

## Usage
[Add usage instructions here]

## Contributing
[Add contribution guidelines here]

## License
[Add license information here]
"""
        elif filename == "package.json":
            return f"""{{
  "name": "{project_name}",
  "version": "1.0.0",
  "description": "{project_name.replace('-', ' ').title()}",
  "main": "index.js",
  "scripts": {{
    "start": "node index.js",
    "test": "echo \\"Error: no test specified\\" && exit 1"
  }},
  "keywords": [],
  "author": "",
  "license": "ISC"
}}
"""
        elif filename == "setup.py":
            return f"""from setuptools import setup, find_packages

setup(
    name="{project_name}",
    version="1.0.0",
    description="{project_name.replace('-', ' ').title()}",
    author="",
    packages=find_packages(),
    install_requires=[
        # Add your dependencies here
    ],
)
"""
        elif filename == "requirements.txt":
            return """# Add your Python dependencies here
# Example:
# requests==2.31.0
# flask==3.0.0
"""
        elif filename == ".gitignore":
            return """# Dependencies
node_modules/
__pycache__/
*.pyc

# Environment variables
.env
.env.local

# Build outputs
dist/
build/
*.egg-info/

# IDE files
.vscode/
.idea/

# OS files
.DS_Store
Thumbs.db
"""
        elif filename == "index.html":
            return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name.replace('-', ' ').title()}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <h1>{project_name.replace('-', ' ').title()}</h1>
    </header>
    
    <main>
        <p>Welcome to {project_name.replace('-', ' ').title()}!</p>
    </main>
    
    <footer>
        <p>&copy; 2024 {project_name.replace('-', ' ').title()}</p>
    </footer>
    
    <script src="script.js"></script>
</body>
</html>
"""
        elif filename == "styles.css":
            return """/* Reset and base styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    color: #333;
}

/* Header styles */
header {
    background-color: #f4f4f4;
    padding: 1rem;
    text-align: center;
}

/* Main content */
main {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
}

/* Footer */
footer {
    background-color: #333;
    color: white;
    text-align: center;
    padding: 1rem;
    position: fixed;
    bottom: 0;
    width: 100%;
}
"""
        elif filename == "script.js":
            return """// Main JavaScript file
document.addEventListener('DOMContentLoaded', function() {
    console.log('Application loaded successfully!');
    
    // Add your JavaScript functionality here
});
"""
        else:
            return f"# {filename}\n\nContent for {filename}"

    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """Read existing file content to prevent data loss."""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                log_info(f"Read existing content from {file_path} ({len(content)} characters)")
                return content
            return None
        except Exception as e:
            log_info(f"Error reading file {file_path}: {e}")
            return None

    def _backup_existing_file(self, file_path: Path) -> bool:
        """Create a backup of an existing file before overwriting."""
        try:
            if file_path.exists():
                backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                import shutil
                shutil.copy2(file_path, backup_path)
                log_info(f"Created backup: {backup_path}")
                return True
            return False
        except Exception as e:
            log_info(f"Error creating backup for {file_path}: {e}")
            return False

    def _write_file_intelligently(self, command: str, shared_state: 'SharedState') -> Dict[str, Any]:
        """Intelligently write files with content awareness and backup protection."""
        try:
            file_name_match = re.search(r"['\"]([\w\.\-]+)['\"]", command)
            if not file_name_match:
                return {"status": "error", "error": "Malformed write command. Could not find filename."}
            file_name = file_name_match.group(1)

            # Try to find the generated code - be more flexible about matching
            code_to_write = shared_state.generated_code.get(file_name, "")
            
            # If not found, try to find any generated code that might match
            if not code_to_write and shared_state.generated_code:
                # Look for code with similar filename or appropriate type
                for stored_filename, stored_code in shared_state.generated_code.items():
                    if stored_code and len(stored_code.strip()) > 0:
                        # Check if this is the right type of file
                        if file_name.endswith('.html') and (stored_filename.endswith('.html') or 'html' in stored_filename.lower()):
                            code_to_write = stored_code
                            log_info(f"Found HTML code in '{stored_filename}' for '{file_name}'")
                            break
                        elif file_name.endswith('.css') and (stored_filename.endswith('.css') or 'css' in stored_filename.lower() or 'style' in stored_filename.lower()):
                            code_to_write = stored_code
                            log_info(f"Found CSS code in '{stored_filename}' for '{file_name}'")
                            break
                        elif file_name.endswith('.js') and (stored_filename.endswith('.js') or 'javascript' in stored_filename.lower() or 'script' in stored_filename.lower()):
                            code_to_write = stored_code
                            log_info(f"Found JavaScript code in '{stored_filename}' for '{file_name}'")
                            break
                        elif file_name.endswith('.py') and (stored_filename.endswith('.py') or 'python' in stored_filename.lower()):
                            code_to_write = stored_code
                            log_info(f"Found Python code in '{stored_filename}' for '{file_name}'")
                            break
                        # Don't use fallback for wrong file types - this was causing issues
                        # elif not code_to_write:  # Use any available code as fallback
                        #     code_to_write = stored_code
                        #     log_info(f"Using fallback code from '{stored_filename}' for '{file_name}'")
                        #     break
            
            if not code_to_write and "SAVE CODE" in command.upper():
                log_info(f"Warning: No code found for '{file_name}' during SAVE operation.")

            # Ensure project directory exists
            if not shared_state.project_directory:
                project_dir = Path.cwd() / "projects" / "default-project"
                project_dir.mkdir(parents=True, exist_ok=True)
                shared_state.set_project_directory(project_dir)
                log_info(f"Project directory was not set, created default at {project_dir}")
            
            file_path = shared_state.project_directory / file_name
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if file exists and read current content
            existing_content = self._read_file_content(file_path)
            
            # Create backup if file exists and has content
            if existing_content and len(existing_content.strip()) > 0:
                backup_created = self._backup_existing_file(file_path)
                if backup_created:
                    log_info(f"Backup created for existing file: {file_path}")
                else:
                    log_info(f"Warning: Could not create backup for {file_path}")

            # Write the new content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code_to_write)

            log_info(f"Successfully wrote {len(code_to_write)} characters to {file_path}")
            
            return {
                "status": "success",
                "output": f"File '{file_name}' saved successfully.",
                "created_files": [str(file_path)],
                "backup_created": existing_content is not None and len(existing_content.strip()) > 0
            }
        except Exception as e:
            log_info(f"Error saving file: {e}")
            return {"status": "error", "error": str(e)}

    def _create_standard_structure(self, structure_type: str, shared_state: 'SharedState') -> Dict[str, Any]:
        """Create a specific standard project structure."""
        try:
            if structure_type not in self.project_templates:
                return {"status": "error", "error": f"Unknown structure type: {structure_type}"}
            
            template = self.project_templates[structure_type]
            
            # Generate project name
            words = [word for word in shared_state.original_task.split() if word.isalnum()]
            project_name = "-".join(words[:3]) if words else f"{structure_type}-project"
            
            base_projects_dir = Path.cwd() / "projects"
            base_projects_dir.mkdir(exist_ok=True)

            project_dir = base_projects_dir / project_name
            project_dir.mkdir(exist_ok=True)
            
            # Create the structure
            created_files = []
            for item in template["structure"]:
                item_path = project_dir / item
                
                if item.endswith("/"):
                    item_path.mkdir(parents=True, exist_ok=True)
                    log_info(f"Created directory: {item_path}")
                else:
                    item_path.parent.mkdir(parents=True, exist_ok=True)
                    default_content = self._generate_default_content(item, project_name)
                    
                    with open(item_path, 'w', encoding='utf-8') as f:
                        f.write(default_content)
                    
                    created_files.append(str(item_path))
                    log_info(f"Created file: {item_path}")
            
            return {
                "status": "success",
                "output": f"Standard {template['description']} created for '{project_name}'.",
                "project_directory": project_dir,
                "project_type": structure_type,
                "created_files": created_files
            }
        except Exception as e:
            log_info(f"Error creating standard structure: {e}")
            return {"status": "error", "error": str(e)}

    def run(self, command: str, shared_state: 'SharedState') -> Dict[str, Any]:
        """Executes intelligent file operations based on the command."""
        command_upper = command.strip().upper()
        try:
            if command_upper == "CREATE PROJECT STRUCTURE":
                log_info("File agent routing to: _create_intelligent_project_structure")
                return self._create_intelligent_project_structure(shared_state)
            
            elif command_upper.startswith("CREATE STANDARD STRUCTURE"):
                # Extract structure type from command
                structure_match = re.search(r"CREATE STANDARD STRUCTURE\s+(\w+)", command_upper)
                if structure_match:
                    structure_type = structure_match.group(1).lower()
                    log_info(f"File agent creating standard structure: {structure_type}")
                    return self._create_standard_structure(structure_type, shared_state)
                else:
                    return {"status": "error", "error": "Please specify structure type: CREATE STANDARD STRUCTURE <type>"}
            
            elif command_upper.startswith("SAVE CODE TO") or command_upper.startswith("CREATE EMPTY FILE"):
                log_info(f"File agent routing to: _write_file_intelligently for command: {command}")
                return self._write_file_intelligently(command, shared_state)

            elif command_upper.startswith("READ FILE"):
                # Extract filename and read content
                file_match = re.search(r"READ FILE\s+['\"]([\w\.\-]+)['\"]", command_upper)
                if file_match:
                    filename = file_match.group(1)
                    
                    # Check if this is a PDF file that should be read from Desktop
                    if filename.lower().endswith('.pdf'):
                        desktop_path = Path.home() / "Desktop"
                        file_path = desktop_path / filename
                        log_info(f"Attempting to read PDF from Desktop: {file_path}")
                    elif shared_state.project_directory:
                        file_path = shared_state.project_directory / filename
                    else:
                        return {"status": "error", "error": "No project directory set"}
                    
                    content = self._read_file_content(file_path)
                    if content is not None:
                        shared_state.add_to_history(f"Read file: {filename}")
                        return {
                            "status": "success",
                            "output": f"File '{filename}' read successfully.",
                            "file_content": content
                        }
                    else:
                        return {"status": "error", "error": f"Could not read file: {filename} from {file_path}"}
                else:
                    return {"status": "error", "error": "Malformed READ FILE command"}

            else:
                log_info(f"File agent received unhandled command: {command}")
                return {"status": "error", "error": f"File agent does not support the command: '{command}'"}
        except Exception as e:
            log_info(f"A critical error occurred in the FileAgentNode run method: {e}")
            return {"status": "error", "error": str(e)}