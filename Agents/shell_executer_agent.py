# Agents/shell_executer_agent.py

import subprocess
import dotenv
from agno.utils.log import log_info
from pathlib import Path
from typing import Dict, Any
from shared_state import SharedState
import pty # <-- Import pty for pseudo-terminal

dotenv.load_dotenv()

class ShellAgentNode:
    """
    A deterministic shell command executor. It now handles interactive prompts
    by detecting them and asking for human intervention.
    """
    def __init__(self):
        log_info("Initialized deterministic ShellAgentNode.")

    def run(self, command: str, shared_state: 'SharedState') -> Dict[str, Any]:
        """Directly executes the given command string in the shell."""
        try:
            working_dir = shared_state.project_directory or Path.cwd()
            log_info(f"Executing shell command: '{command}' in '{working_dir}'")

            # --- NEW INTERACTIVE COMMAND HANDLING ---
            # Use pty to run the command in a pseudo-terminal, which allows us to
            # detect prompts for passwords or user input.
            master, slave = pty.openpty()
            process = subprocess.Popen(
                command,
                shell=True,
                stdin=slave,
                stdout=slave,
                stderr=slave,
                cwd=str(working_dir),
                close_fds=True
            )
            
            # Close the slave descriptor in the parent
            subprocess.os.close(slave)

            output = ""
            # Check for output from the process without blocking indefinitely
            try:
                # Read a small amount of data to see if there's a prompt
                initial_output = subprocess.os.read(master, 1024).decode('utf-8', errors='ignore')
                output += initial_output

                # Check for common password/interactive prompts
                if "password:" in initial_output.lower() or "continue? (y/n)" in initial_output.lower():
                    process.terminate() # Terminate the process
                    subprocess.os.close(master)
                    problem = f"The command '{command}' requires interactive input (e.g., a password). The system cannot provide this."
                    return {
                        "status": "error",
                        "error": "human_intervention_required",
                        "output": problem
                    }

                # If no prompt, read the rest of the output
                while True:
                    try:
                        data = subprocess.os.read(master, 1024)
                        if not data:
                            break
                        output += data.decode('utf-8', errors='ignore')
                    except OSError:
                        # This happens when the process has finished and the master is closed
                        break

            finally:
                subprocess.os.close(master)

            # Wait for the process to terminate and get the return code
            return_code = process.wait()
            # --- END OF NEW LOGIC ---

            if return_code != 0:
                log_info(f"Shell command failed with return code {return_code}")
                return {"status": "error", "error": output, "output": output}

            return {"status": "success", "output": output, "error": None}

        except Exception as e:
            log_info(f"A critical error occurred while executing shell command: {e}")
            return {"status": "error", "error": str(e), "output": None}