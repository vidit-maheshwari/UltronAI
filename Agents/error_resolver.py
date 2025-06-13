# error_resolver_agent.py
from agno.storage.sqlite import SqliteStorage
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools import tool
import dotenv
import re

dotenv.load_dotenv()

class ErrorResolverAgentNode:
    def __init__(self, agent_id="error_resolver_agent", db_file="agents.db", table_name="error_resolver_sessions"):
        self.storage = SqliteStorage(table_name=table_name, db_file=db_file)
        self.agent_id = agent_id
        
        @tool(show_result=True)
        def analyze_error(error_message: str, file_name: str = None) -> str:
            """Analyze error message and provide resolution steps"""
            try:
                analysis = f"""
🔍 Error Analysis:
Error: {error_message}
File: {file_name or 'Unknown'}

Common causes and solutions:
"""
                # Common error patterns
                if "ModuleNotFoundError" in error_message or "ImportError" in error_message:
                    module_match = re.search(r"No module named '([^']+)'", error_message)
                    if module_match:
                        module = module_match.group(1)
                        analysis += f"- Missing package '{module}' - needs installation\n"
                
                elif "SyntaxError" in error_message:
                    analysis += "- Code syntax issue - needs code review and fixing\n"
                
                elif "FileNotFoundError" in error_message:
                    analysis += "- File or directory missing - check file paths\n"
                
                elif "PermissionError" in error_message:
                    analysis += "- Permission issue - check file/directory permissions\n"
                
                else:
                    analysis += "- General runtime error - needs code debugging\n"
                
                return analysis
            except Exception as e:
                return f"❌ Error analyzing error: {str(e)}"
        
#         @tool(show_result=True)
#         def create_fix_plan(error_analysis: str, task_context: str) -> str:
#             """Create a step-by-step plan to fix the error"""
#             try:
#                 plan = f"""
# 🛠️ Fix Plan:
# Context: {task_context}
# Analysis: {error_analysis}

# Recommended steps:
# 1. Identify the root cause
# 2. Determine which agent should handle the fix
# 3. Execute the fix
# 4. Test the solution
# 5. Verify the issue is resolved

# Next actions:
# """
#                 if "needs installation" in error_analysis:
#                     plan += "- Use installer_agent to install missing packages\n"
#                 if "needs code review" in error_analysis:
#                     plan += "- Use coder_agent to fix code issues\n"
#                 if "check file paths" in error_analysis:
#                     plan += "- Use file_agent to verify file structure\n"
                
#                 return plan
#             except Exception as e:
#                 return f"❌ Error creating fix plan: {str(e)}"
        
        self.analyze_error = analyze_error
        # self.create_fix_plan = create_fix_plan
        
        self.model = Groq(id="deepseek-r1-distill-llama-70b")
        self.agent = Agent(
            model=self.model,
           tools=[self.analyze_error],
            storage=self.storage,
            agent_id=self.agent_id,
            show_tool_calls=True,
            markdown=True,
            instructions="""You are an error resolution agent. Your job is ONLY to:
1. Analyze error messages and exceptions
2. Identify root causes of problems
3. Create step-by-step fix plans
4. Recommend which agent should handle each fix

Do NOT fix errors directly - other agents handle the actual fixes.
Focus only on analysis and planning the resolution strategy."""
        )
    
    def run(self, prompt: str, stream: bool = True) -> str:
        return self.agent.print_response(prompt, stream=stream)