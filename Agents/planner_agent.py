from agno.agent import Agent
from agno.models.groq import Groq
from agno.storage.sqlite import SqliteStorage as SqlAgentStorage
from agno.utils.log import log_info
from typing import List, Dict, Any
import dotenv
import os
import json
import re

dotenv.load_dotenv()


class PlannerAgentNode:
    def __init__(
        self,
        agent_id: str = "planner_agent",
        db_file: str = "agents.db",
        table_name: str = "multi_agent_memory",
        model_name: str = "deepseek-r1-distill-llama-70b",
        markdown: bool = True,
    ):
        self.storage = SqlAgentStorage(table_name=table_name, db_file=db_file)
        self.agent_id = agent_id

        self.agent = Agent(
            model=Groq(id=model_name),
            storage=self.storage,
            agent_id=self.agent_id,
            show_tool_calls=False,
            markdown=markdown,
            instructions="""You are the Planner Agent in a multi-agent system. Your job is to decompose tasks into structured subtasks.
            Each subtask must have:
            - A clear description
            - The name of the specialized agent to handle it
            
            Available agents:
            - file_agent: For file operations (read, write, save)
            - shell_agent: For system commands, package management, and execution
            - coder_agent: For writing and modifying code
            - executor_agent: For running code and scripts
            - installer_agent: For package installation
            - web_search_agent: For web research
            
            For package management tasks:
            - Use shell_agent for checking package installation status
            - Use shell_agent for installing/uninstalling packages
            - Use installer_agent only for complex installation scenarios
            
            IMPORTANT: You must return ONLY a JSON array of subtasks in this exact format:
            [
                {
                    "agent": "agent_name",
                    "description": "detailed task description"
                }
            ]
            
            Do not include any other text, explanations, or formatting. Just the JSON array."""
        )

    def _extract_content(self, response: Any) -> str:
        """Extract content from various response types."""
        if hasattr(response, 'content'):
            return str(response.content)
        elif isinstance(response, str):
            return response
        elif isinstance(response, dict) and 'content' in response:
            return str(response['content'])
        return str(response)

    def _clean_response(self, response: str) -> str:
        """Clean the response text to extract valid JSON."""
        if not response or not isinstance(response, str):
            return ""
            
        # Remove any markdown formatting
        response = re.sub(r'```json|```', '', response)
        
        # Remove leading/trailing whitespace
        response = response.strip()
        
        # Remove any think tags or other non-JSON content
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        response = re.sub(r'<.*?>', '', response)
        
        # Find the JSON array - more flexible pattern
        patterns = [
            r'\[\s*\{[\s\S]*?\}\s*\]',  # Standard JSON array
            r'\[[\s\S]*?\]',             # Any array structure
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                candidate = match.group(0).strip()
                # Basic validation - should start with [ and end with ]
                if candidate.startswith('[') and candidate.endswith(']'):
                    return candidate
        
        # If no JSON array found, try to find individual objects and wrap them
        object_matches = re.findall(r'\{[^{}]*\}', response)
        if object_matches:
            return '[' + ','.join(object_matches) + ']'
        
        return response

    def _parse_subtasks(self, response: str) -> List[Dict[str, Any]]:
        """Parse the response into a list of subtasks."""
        if not response:
            log_info("Empty response received")
            return []
            
        try:
            # Clean the response
            cleaned_response = self._clean_response(response)
            log_info(f"Cleaned response: {cleaned_response[:200]}...")  # Log first 200 chars
            
            if not cleaned_response:
                log_info("No valid JSON structure found in response")
                return []
            
            # Try to parse as JSON
            try:
                subtasks = json.loads(cleaned_response)
                log_info(f"Successfully parsed JSON with {len(subtasks) if isinstance(subtasks, list) else 1} items")
            except json.JSONDecodeError as je:
                log_info(f"JSON decode error: {je}")
                # If JSON parsing fails, try to evaluate as Python literal (be careful!)
                try:
                    subtasks = eval(cleaned_response)
                    log_info("Successfully parsed using eval")
                except Exception as ee:
                    log_info(f"Eval parsing also failed: {ee}")
                    return []

            # Ensure we have a list
            if not isinstance(subtasks, list):
                subtasks = [subtasks]

            # Validate each subtask
            valid_subtasks = []
            for i, subtask in enumerate(subtasks):
                if isinstance(subtask, dict) and 'agent' in subtask and 'description' in subtask:
                    valid_subtasks.append({
                        'agent': str(subtask['agent']).strip(),
                        'description': str(subtask['description']).strip()
                    })
                    log_info(f"Valid subtask {i+1}: {subtask['agent']}")
                else:
                    log_info(f"Invalid subtask {i+1}: missing required keys or wrong format")

            return valid_subtasks

        except Exception as e:
            log_info(f"Error parsing subtasks: {e}")
            return []

    def plan(self, task: str) -> List[Dict[str, Any]]:
        """Plans a task by breaking it into subtasks with assigned agents."""
        planning_prompt = f"""Break down this task into subtasks and return ONLY a JSON array:
        [
            {{
                "agent": "agent_name",
                "description": "detailed task description"
            }}
        ]

        Available agents: file_agent, shell_agent, coder_agent, executor_agent, installer_agent, web_search_agent
        
        Task to break down: {task}
        
        Return ONLY the JSON array, no other text."""

        try:
            log_info(f"Planning task: {task}")
            
            # Get response from the agent
            response = self.agent.run(planning_prompt)
            
            # Extract content from response
            content = self._extract_content(response)
            log_info(f"Raw response received (first 200 chars): {content[:200]}...")

            # Parse the response into subtasks
            subtasks = self._parse_subtasks(content)
            
            if not subtasks:
                log_info("Failed to parse subtasks from response")
                return []

            log_info(f"Successfully parsed {len(subtasks)} subtasks")
            for i, subtask in enumerate(subtasks, 1):
                log_info(f"  {i}. {subtask['agent']}: {subtask['description'][:50]}...")
            
            return subtasks
                
        except Exception as e:
            log_info(f"Error in plan method: {e}")
            import traceback
            log_info(f"Traceback: {traceback.format_exc()}")
            return []

    def execute_plan(self, subtasks: List[Dict[str, Any]], agents: Dict[str, Any]):
        """Execute the plan by running each subtask with its assigned agent."""
        if not subtasks:
            log_info("No subtasks to execute")
            return []
            
        results = []
        for i, subtask in enumerate(subtasks, 1):
            agent_key = subtask["agent"]
            prompt = subtask["description"]

            log_info(f"\n🔧 Executing Subtask {i}/{len(subtasks)}")
            log_info(f"Agent: {agent_key}")
            log_info(f"Task: {prompt}")

            if agent_key in agents:
                try:
                    result = agents[agent_key].run(prompt)
                    results.append({
                        "subtask": i,
                        "agent": agent_key,
                        "status": "success",
                        "result": result
                    })
                    log_info(f"✅ Subtask {i} completed successfully")
                except Exception as e:
                    error_msg = f"Error executing subtask {i}: {str(e)}"
                    log_info(f"❌ {error_msg}")
                    results.append({
                        "subtask": i,
                        "agent": agent_key,
                        "status": "error",
                        "error": error_msg
                    })
            else:
                error_msg = f"Agent '{agent_key}' not found!"
                available_agents = list(agents.keys())
                log_info(f"⚠️ {error_msg}")
                log_info(f"Available agents: {available_agents}")
                results.append({
                    "subtask": i,
                    "agent": agent_key,
                    "status": "error",
                    "error": error_msg
                })

        # Log final execution summary
        success_count = sum(1 for r in results if r["status"] == "success")
        log_info(f"\n📊 Execution Summary:")
        log_info(f"Total subtasks: {len(subtasks)}")
        log_info(f"Successful: {success_count}")
        log_info(f"Failed: {len(subtasks) - success_count}")
        
        return results