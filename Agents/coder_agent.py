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
        name: str = "Coder Agent",  # Add this parameter
        db_file: str = "agents.db",
        table_name: str = "coder_sessions",
        role: str = "Code Developer and Analyzer",
        base_dir: Path = None
    ):
        self.name = name  # Add this line
        self.role = role
        self.storage = SqliteStorage(table_name=table_name, db_file=db_file)
        self.agent_id = agent_id
        self.base_dir = base_dir or Path.cwd()
        self.file_tools = FileTools(base_dir=self.base_dir)

        self.model = Groq(id="deepseek-r1-distill-llama-70b")

        # Register tools
        self.write_code_file = self._define_write_code_file()
        self.analyze_code = self._define_analyze_code()
        self.generate_tests = self._define_generate_tests()
        self.review_code = self._define_review_code()

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
            instructions=self._instructions()
        )

    def _define_write_code_file(self):
        @tool(show_result=True)
        def write_code_file(file_name: str, code: str, language: str = "python") -> str:
            extensions = {
                "python": ".py", "javascript": ".js", "typescript": ".ts",
                "java": ".java", "cpp": ".cpp", "c": ".c", "html": ".html",
                "css": ".css", "sql": ".sql", "shell": ".sh", "json": ".json",
                "rust": ".rs", "go": ".go", "ruby": ".rb", "php": ".php"
            }
            try:
                if not any(file_name.endswith(ext) for ext in extensions.values()):
                    file_name += extensions.get(language.lower(), ".py")
                file_path = self.base_dir / file_name
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                return f"✅ Code written to {file_name}"
            except Exception as e:
                return f"❌ Error: {str(e)}"
        return write_code_file

    def _define_analyze_code(self):
        @tool(show_result=True)
        def analyze_code(code: str, language: str = "python") -> str:
            return f"""
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
   - Add type hints
   - Break down complex functions
"""
        return analyze_code

    def _define_generate_tests(self):
        @tool(show_result=True)
        def generate_tests(code: str, language: str = "python") -> str:
            return f"""
# Generated test file for {language} code
import unittest

class TestGeneratedCode(unittest.TestCase):
    def setUp(self):
        pass

    def test_main_functionality(self):
        pass

if __name__ == '__main__':
    unittest.main()
"""
        return generate_tests

    def _define_review_code(self):
        @tool(show_result=True)
        def review_code(code: str, language: str = "python") -> str:
            return f"""
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
   - Resource Usage: {'Good' if 'open' not in code else 'Consider using context managers'}

4. Recommendations:
   - Improve error handling and input checks
   - Optimize complex loops
   - Add inline documentation
"""
        return review_code

    def _instructions(self):
        return """You are a specialized coding wizard agent in a multi-agent system. Your primary responsibilities are:

1. Write clean, well-documented code
2. Analyze and improve existing code
3. Generate meaningful unit tests
4. Conduct thorough code reviews

Focus on correctness, clarity, security, and modularity. Collaborate with other agents for non-code tasks like file ops or planning."""

    def run(self, prompt: str, stream: bool = True) -> Dict[str, Any]:
        try:
            response = {
                "status": "success",
                "message": "",
                "code": "",
                "analysis": "",
                "tests": "",
                "review": ""
            }
            main_response = self.agent.print_response(prompt, stream=stream)
            response["message"] = main_response

            if "```" in main_response:
                code_blocks = main_response.split("```")
                for i in range(1, len(code_blocks), 2):
                    if code_blocks[i].strip():
                        response["code"] = code_blocks[i].strip()
                        break

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
        try:
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
        task_type = task.get('type', '')
        language = task.get('language', 'python')
        requirements = task.get('requirements', '')
        existing_code = task.get('existing_code', '')

        if task_type == 'generate':
            return f"""Generate {language} code for the following requirements:
{requirements}

Please include:
- Documentation
- Error handling
- Type hints
- Best practices
"""
        elif task_type == 'analyze':
            return f"""Analyze the following {language} code:
{existing_code}

Provide:
- Code quality insights
- Problem areas
- Optimization suggestions
"""
        elif task_type == 'test':
            return f"""Generate tests for this {language} code:
{existing_code}

Include:
- Unit tests
- Edge cases
- Integration tests if needed
"""
        elif task_type == 'review':
            return f"""Perform a review for the following {language} code:
{existing_code}

Include:
- Code review
- Security check
- Performance suggestions
- Best practice alignment
"""
        return json.dumps(task)


# agent = CoderAgentNode()
# result = agent.run("Write a FastAPI endpoint for user login with JWT auth")
# print(result)