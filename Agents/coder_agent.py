# Agents/coder_agent.py

from agno.agent import Agent
from agno.models.groq import Groq
from agno.storage.sqlite import SqliteStorage
from agno.utils.log import log_info
import dotenv
from typing import Dict, Any
import re
from shared_state import SharedState  # Import SharedState

dotenv.load_dotenv()

class CoderAgentNode:
    """
    An advanced, robust coding agent that uses an internal multi-persona
    workflow (Draft -> Review -> Refactor) to produce high-quality code.
    """
    def __init__(
        self,
        agent_id: str = "coder_agent",
        db_file: str = "agents.db",
        table_name: str = "coder_sessions",
    ):
        self.storage = SqliteStorage(table_name=table_name, db_file=db_file)
        self.agent_id = agent_id

        self.drafting_agent = Agent(
            model=Groq(id="deepseek-r1-distill-llama-70b"),
            instructions="You are a senior developer focused on rapid prototyping. You write functional code to meet the user's request. Your output MUST be ONLY the raw code, wrapped in <<START_CODE>> and <<END_CODE>> markers. Do not add any explanations or thoughts."
        )

        self.reviewing_agent = Agent(
            model=Groq(id="deepseek-r1-distill-llama-70b"),
            instructions="You are a meticulous code reviewer. Analyze the provided code for bugs, security vulnerabilities, and deviations from best practices. Provide a concise, bulleted list of necessary improvements. If the code is perfect, simply respond with 'No issues found.'"
        )

        self.refactoring_agent = Agent(
            model=Groq(id="deepseek-r1-distill-llama-70b"),
            instructions="You are a senior software architect specializing in clean code. Rewrite the provided code draft to incorporate the reviewer's feedback. Your goal is to produce a final version that is efficient, readable, and robust. Output ONLY the final, raw code, wrapped in <<START_CODE>> and <<END_CODE>> markers."
        )

    def _extract_code(self, raw_content: str) -> str:
        """A robust method to extract code from the special markers."""
        start_marker = "<<START_CODE>>"
        end_marker = "<<END_CODE>>"
        
        start_index = raw_content.find(start_marker)
        end_index = raw_content.find(end_marker)

        if start_index != -1 and end_index != -1:
            code = raw_content[start_index + len(start_marker):end_index].strip()
            log_info(f"Successfully extracted code using markers. Length: {len(code)}")
            return code
        
        log_info("Warning: Could not find code markers. Returning raw content as a fallback.")
        return raw_content.strip()

    def run(self, prompt: str, shared_state: 'SharedState') -> Dict[str, Any]:
        """Executes a robust, multi-step coding process."""
        try:
            filename_match = re.search(r"for\s*['\"]?([\w\.\-]+)['\"]?", prompt)
            filename = filename_match.group(1) if filename_match else "unknown_file.txt"

            # === THIS IS THE FIX: Construct the full, detailed prompt first ===
            contextual_prompt = f"""
            Based on the following project context, please write the required code for the file: `{filename}`

            **Project Context:**
            - **Original Task:** {shared_state.original_task}
            - **Project Directory:** {shared_state.project_directory}

            **Current Coding Task:**
            {prompt}
            """

            if filename.endswith(".html"):
                contextual_prompt += """
                ---
                **CRITICAL HTML STRUCTURE REQUIREMENTS:**
                Your response MUST be a complete HTML5 document. It MUST include:
                - A `<!DOCTYPE html>` declaration.
                - An `<html>` tag with the `lang="en"` attribute.
                - A `<head>` section containing:
                  - `<meta charset="UTF-8">`
                  - `<meta name="viewport" content="width=device-width, initial-scale=1.0">`
                  - A relevant `<title>`.
                  - A `<link rel="stylesheet" href="styles.css">` tag to link the stylesheet.
                - A `<body>` section containing the main content.
                - A `<script src="script.js"></script>` tag right before the closing `</body>` tag.
                
                Remember to wrap your final code in the special markers.
                """
            
            # === STEP 1: DRAFTING ===
            log_info(f"Step 1: Drafting initial code for '{filename}'...")
            # Use the full contextual_prompt here
            draft_response = self.drafting_agent.run(contextual_prompt)
            initial_code = self._extract_code(draft_response.content)
            if not initial_code:
                raise ValueError("Drafting agent failed to produce code.")
            log_info("Drafting complete.")

            # === STEP 2: REVIEWING ===
            log_info("Step 2: Reviewing drafted code...")
            review_prompt = f"Please review the following code for the file '{filename}':\n\n{initial_code}"
            review_feedback = self.reviewing_agent.run(review_prompt).content
            log_info(f"Review feedback: {review_feedback}")

            # === STEP 3: REFACTORING ===
            if "No issues found" in review_feedback:
                log_info("Step 3: No issues found. Skipping refactoring.")
                final_code = initial_code
            else:
                log_info("Step 3: Refactoring code based on feedback...")
                refactor_prompt = f"""
                Please refactor this code draft for '{filename}':
                ---
                {initial_code}
                ---

                Incorporate this feedback from the code review:
                ---
                {review_feedback}
                ---
                """
                refactor_response = self.refactoring_agent.run(refactor_prompt)
                final_code = self._extract_code(refactor_response.content)
                if not final_code:
                    raise ValueError("Refactoring agent failed to produce code.")
                log_info("Refactoring complete.")

            return {
                "status": "success",
                "output": f"Code robustly generated for {filename}.",
                "filename": filename,
                "generated_code": final_code,
            }

        except Exception as e:
            log_info(f"A critical error occurred in the CoderAgentNode run method: {e}")
            return {
                "status": "error",
                "error": str(e),
                "generated_code": None,
            }