# coder_agent.py
from agno.storage.sqlite import SqliteStorage
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.file import FileTools
from agno.tools import tool
from pathlib import Path
import dotenv
import os
import json
from typing import Dict, Any, List, Optional

dotenv.load_dotenv()

class CoderAgentNode:
    def __init__(
        self,
        agent_id: str = "coder_agent",
        db_file: str = "agents.db",
        table_name: str = "coder_sessions",
        base_dir: Path = None
    ):
        self.storage = SqliteStorage(table_name=table_name, db_file=db_file)
        self.agent_id = agent_id
        self.base_dir = base_dir or Path.cwd()
        self.file_tools = FileTools(base_dir=self.base_dir)
        
        @tool(show_result=True)
        def write_code_file(file_name: str, code: str, language: str = "python") -> str:
            """Write code to a file with proper extension and formatting"""
            try:
                extensions = {
                    "python": ".py", "javascript": ".js", "typescript": ".ts",
                    "java": ".java", "cpp": ".cpp", "c": ".c", "html": ".html",
                    "css": ".css", "sql": ".sql", "shell": ".sh", "json": ".json",
                    "rust": ".rs", "go": ".go", "ruby": ".rb", "php": ".php"
                }
                
                if not any(file_name.endswith(ext) for ext in extensions.values()):
                    file_name += extensions.get(language.lower(), ".py")
                
                file_path = self.base_dir / file_name
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                
                return f"✅ Code written to {file_name}"
            except Exception as e:
                return f"❌ Error: {str(e)}"

        @tool(show_result=True)
        def analyze_code(code: str, language: str = "python") -> str:
            """Analyze code for quality, best practices, and potential issues"""
            analysis = f"""
📊 Code Analysis Report:

1. Code Structure:
   - Language: {language}
   - Lines of code: {len(code.splitlines())}
   - Complexity: {'High' if code.count('if') + code.count('for') + code.count('while') > 10 else 'Low'}

2. Best Practices Check:
   - Documentation: {'✅' if '"""' in code or "'''" in code else '❌'}
   - Error Handling: {'✅' if 'try' in code and 'except' in code else '❌'}
   - Type Hints: {'✅' if ': ' in code and '->' in code else '❌'}

3. Recommendations:
   - Add docstrings if missing
   - Implement error handling
   - Add type hints for better code clarity
   - Consider breaking down complex functions
"""
            return analysis

        @tool(show_result=True)
        def generate_tests(code: str, language: str = "python") -> str:
            """Generate unit tests for the provided code"""
            test_code = f"""
# Generated test file for {language} code
import unittest

class TestGeneratedCode(unittest.TestCase):
    def setUp(self):
        # Setup code here
        pass

    def test_main_functionality(self):
        # Add test cases here
        pass

if __name__ == '__main__':
    unittest.main()
"""
            return test_code

        @tool(show_result=True)
        def review_code(code: str, language: str = "python") -> str:
            """Review code and provide detailed feedback"""
            review = f"""
🔍 Code Review:

1. Code Quality:
   - Readability: {'Good' if len(code.splitlines()) < 50 else 'Could be improved'}
   - Maintainability: {'Good' if code.count('def') < 5 else 'Consider refactoring'}
   - Documentation: {'Good' if '"""' in code else 'Needs improvement'}

2. Security:
   - Input Validation: {'✅' if 'input' in code and 'validate' in code else '❌'}
   - Error Handling: {'✅' if 'try' in code else '❌'}
   - Data Sanitization: {'✅' if 'sanitize' in code else '❌'}

3. Performance:
   - Algorithm Complexity: {'Good' if code.count('for') < 3 else 'Could be optimized'}
   - Resource Usage: {'Good' if 'open' not in code else 'Consider context managers'}

4. Recommendations:
   - Add more error handling
   - Improve documentation
   - Consider performance optimizations
   - Add input validation where needed
"""
            return review

        self.write_code_file = write_code_file
        self.analyze_code = analyze_code
        self.generate_tests = generate_tests
        self.review_code = review_code
        
        self.model = Groq(id="deepseek-r1-distill-llama-70b")
        self.agent = Agent(
            model=self.model,
            tools=[
                self.write_code_file,
                self.analyze_code,
                self.generate_tests,
                self.review_code
            ],
            storage=self.storage,
            agent_id=self.agent_id,
            show_tool_calls=True,
            markdown=True,
            instructions="""You are a specialized coding wizard agent in a multi-agent system. Your primary responsibilities are:

1. Code Generation:
   - Write clean, well-documented code
   - Follow language-specific best practices
   - Implement proper error handling
   - Use type hints where appropriate
   - Create modular and maintainable code

2. Code Analysis:
   - Analyze code quality and structure
   - Identify potential issues and bugs
   - Suggest improvements and optimizations
   - Check for security vulnerabilities
   - Verify best practices compliance

3. Testing:
   - Generate appropriate unit tests
   - Create test cases for edge cases
   - Ensure code coverage
   - Implement integration tests when needed

4. Code Review:
   - Provide detailed code reviews
   - Suggest performance improvements
   - Check for security best practices
   - Verify documentation quality
   - Recommend refactoring when needed

When receiving tasks from other agents:
1. Analyze the requirements carefully
2. Break down complex tasks into manageable pieces
3. Generate code with proper documentation
4. Include error handling and edge cases
5. Provide analysis and review of the code
6. Generate appropriate tests

Remember:
- Focus on code quality and maintainability
- Follow language-specific conventions
- Consider security and performance
- Provide clear documentation
- Make code reusable and modular

You are part of a larger system where other agents handle:
- File operations
- Shell commands
- Package installation
- Error resolution
- Task planning

Your job is to be the coding expert - write the best possible code and let other agents handle the rest."""
        )

    def run(self, prompt: str, stream: bool = True) -> Dict[str, Any]:
        """
        Execute a coding task and return a structured response.
        
        Args:
            prompt (str): The coding task to execute
            stream (bool): Whether to stream the response
            
        Returns:
            Dict[str, Any]: A structured response containing:
                - status: 'success' or 'error'
                - message: The main response message
                - code: The generated code (if any)
                - analysis: Code analysis results
                - tests: Generated tests
                - review: Code review results
        """
        try:
            # Initialize response structure
            response = {
                "status": "success",
                "message": "",
                "code": "",
                "analysis": "",
                "tests": "",
                "review": ""
            }
            
            # Get the main response from the agent
            main_response = self.agent.print_response(prompt, stream=stream)
            response["message"] = main_response
            
            # Extract code if present
            if "```" in main_response:
                code_blocks = main_response.split("```")
                for i in range(1, len(code_blocks), 2):
                    if code_blocks[i].strip():
                        response["code"] = code_blocks[i].strip()
                        break
            
            # If code was generated, analyze and review it
            if response["code"]:
                response["analysis"] = self.analyze_code(response["code"])
                response["tests"] = self.generate_tests(response["code"])
                response["review"] = self.review_code(response["code"])
            
            return response
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error executing coding task: {str(e)}",
                "code": "",
                "analysis": "",
                "tests": "",
                "review": ""
            }

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a structured coding task.
        
        Args:
            task (Dict[str, Any]): A dictionary containing:
                - type: The type of task ('generate', 'analyze', 'test', 'review')
                - language: The programming language
                - requirements: The coding requirements
                - existing_code: Any existing code to work with
                
        Returns:
            Dict[str, Any]: The structured response from run()
        """
        try:
            # Convert task to prompt
            prompt = self._task_to_prompt(task)
            return self.run(prompt)
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error processing coding task: {str(e)}",
                "code": "",
                "analysis": "",
                "tests": "",
                "review": ""
            }

    def _task_to_prompt(self, task: Dict[str, Any]) -> str:
        """Convert a structured task to a natural language prompt."""
        task_type = task.get('type', '')
        language = task.get('language', 'python')
        requirements = task.get('requirements', '')
        existing_code = task.get('existing_code', '')
        
        if task_type == 'generate':
            return f"""Generate {language} code for the following requirements:
{requirements}

Please include:
1. Proper documentation
2. Error handling
3. Type hints
4. Best practices
"""
        elif task_type == 'analyze':
            return f"""Analyze this {language} code:
{existing_code}

Please provide:
1. Code quality assessment
2. Potential issues
3. Improvement suggestions
"""
        elif task_type == 'test':
            return f"""Generate tests for this {language} code:
{existing_code}

Please include:
1. Unit tests
2. Edge cases
3. Integration tests if needed
"""
        elif task_type == 'review':
            return f"""Review this {language} code:
{existing_code}

Please provide:
1. Code review
2. Security assessment
3. Performance analysis
4. Best practices check
"""
        
        return json.dumps(task)  # Fallback to JSON representation
    



