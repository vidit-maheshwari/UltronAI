# Agents/human_intervention_agent.py
# This is our safety net. When the system encounters an error it can't solve (like needing a password), it will call this agent to clearly explain the problem to you, the user.

from agno.utils.log import log_info

class HumanInterventionAgent:
    def request_help(self, problem: str) -> str:
        """Formats a clear help request for the user."""
        log_info("Requesting human intervention.")
        
        help_message = f"""
        =========================|| ATTENTION REQUIRED ||=========================
        
        The multi-agent system has encountered an issue it cannot resolve on its own.
        
        **Problem:**
        {problem}

        **Next Steps:**
        Please resolve this issue in your terminal, then restart the task.
        For example, you may need to install a missing tool or provide permissions.
        
        ========================================================================
        """
        return help_message