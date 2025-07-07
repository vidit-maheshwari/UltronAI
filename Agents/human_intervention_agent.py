# Agents/human_intervention_agent.py

from agno.utils.log import log_info

class HumanInterventionAgent:
    """Handles situations where the agent system cannot proceed without user help."""
    def request_help(self, problem: str) -> str:
        """Formats a clear help request for the user and logs the event."""
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