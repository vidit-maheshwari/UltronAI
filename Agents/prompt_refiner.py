    # prompt_refiner.py

from datetime import datetime, timedelta
import re

class PromptRefiner:
    def __init__(self):
        self.now = datetime.now()

    def refine(self, prompt: str) -> str:
        prompt = prompt.strip()

        # Replace vague time references
        prompt = self._normalize_dates(prompt)

        # Inject search context
        if "news" in prompt.lower() or "accident" in prompt.lower():
            prompt = (
                "You are an assistant with access to the web. "
                "Find recent, credible information about the following topic:\n"
                f"{prompt}\n"
                "Summarize your findings clearly with bullet points or headlines."
            )

        # Ensure fallback context
        if len(prompt.split()) < 5:
            prompt += "\nBe concise and factually accurate."

        return prompt

    def _normalize_dates(self, prompt: str) -> str:
        mappings = {
            "yesterday": self.now - timedelta(days=1),
            "2 days back": self.now - timedelta(days=2),
            "day before yesterday": self.now - timedelta(days=2),
        }

        for phrase, dt in mappings.items():
            if phrase in prompt.lower():
                prompt = re.sub(phrase, dt.strftime("%d %B %Y"), prompt, flags=re.IGNORECASE)

        return prompt
