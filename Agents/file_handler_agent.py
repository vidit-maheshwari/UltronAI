from agno.agent import Agent
from agno.models.groq import Groq
from agno.storage.sqlite import SqliteStorage as SqlAgentStorage
from agno.utils.log import log_info
from pathlib import Path
import dotenv
import os
import json
import re
from typing import Dict, Any, Optional

dotenv.load_dotenv()


class FileAgentNode:
    def __init__(
        self,
        agent_id: str = "file_agent",
        db_file: str = "agents.db",
        table_name: str = "file_agent_memory",
        model_name: str = "deepseek-r1-distill-llama-70b",
        markdown: bool = True,
        base_dir: Optional[Path] = None
    ):
        self.storage = SqlAgentStorage(table_name=table_name, db_file=db_file)
        self.agent_id = agent_id
        self.base_dir = base_dir or Path.cwd()

        self.agent = Agent(
            model=Groq(id=model_name),
            storage=self.storage,
            agent_id=self.agent_id,
            show_tool_calls=True,
            markdown=markdown,
            instructions="""You are the File Agent in a multi-agent system. Your job is to handle file operations.
            When saving files:
            1. Always extract the actual content from the input
            2. Remove any markdown formatting or tool call syntax
            3. Save the clean content to the specified file
            4. Verify the file was saved correctly
            
            Available operations:
            - save_file: Save content to a file
            - read_file: Read content from a file
            - list_files: List files in a directory
            
            Always verify the content before saving and after reading."""
        )

    def _extract_content(self, text: str) -> str:
        """Extract clean content from text, removing any formatting or tool calls."""
        # Remove tool call syntax
        text = re.sub(r'<tool_call>.*?</tool_call>', '', text, flags=re.DOTALL)
        
        # Remove markdown formatting
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        
        # Remove any remaining XML-like tags
        text = re.sub(r'<.*?>', '', text)
        
        # Remove multiple newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()

    def _save_file(self, content: str, file_name: str, overwrite: bool = False) -> bool:
        """Save content to a file."""
        try:
            # Clean the content
            content = self._extract_content(content)
            
            # Ensure the file has an extension
            if not any(file_name.endswith(ext) for ext in ['.txt', '.md', '.json', '.py', '.csv']):
                file_name += '.txt'
            
            # Create the file path relative to base_dir
            file_path = self.base_dir / file_name
            
            # Check if file exists and handle overwrite
            if file_path.exists() and not overwrite:
                log_info(f"File {file_name} already exists and overwrite is False")
                return False
            
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            log_info(f"Successfully saved content to {file_path}")
            return True
            
        except Exception as e:
            log_info(f"Error saving file {file_name}: {str(e)}")
            return False

    def run(self, prompt: str) -> Dict[str, Any]:
        """Execute a file operation based on the prompt."""
        try:
            # Get response from the agent
            response = self.agent.run(prompt)
            
            # Extract content from response
            content = self._extract_content(str(response))
            
            # Check if this is a save operation
            if "save" in prompt.lower() and "file" in prompt.lower():
                # Extract filename from prompt
                file_name = None
                if "as" in prompt.lower():
                    file_name = prompt.lower().split("as")[-1].strip()
                elif "named" in prompt.lower():
                    file_name = prompt.lower().split("named")[-1].strip()
                
                if file_name:
                    # Remove any quotes or extra words
                    file_name = file_name.strip('"\' .')
                    success = self._save_file(content, file_name, overwrite=True)
                    return {
                        "status": "success" if success else "error",
                        "message": f"File saved as {file_name}" if success else f"Failed to save file {file_name}",
                        "content": content
                    }
            
            return {
                "status": "success",
                "message": "Operation completed",
                "content": content
            }
            
        except Exception as e:
            log_info(f"Error in run method: {str(e)}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}",
                "content": ""
            }

# Usage
# node = FileAgentNode(base_dir=Path("/tmp"))
# print(node.run("Save the text 'Hello World' to a file named example.txt"))


