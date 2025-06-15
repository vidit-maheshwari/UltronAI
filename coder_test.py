# developer_test.py

from Teams.coder_team import developer_team_agent

def test_developer_team():
    print("🚀 Running Developer Team Agent...\n")

    user_prompt = (
        "Create a FastAPI app with an endpoint `/classify` that accepts POST requests "
        "with JSON text input and returns a dummy classification like 'positive' or 'negative'."
    )

    developer_team_agent.print_response(user_prompt, stream=True)


if __name__ == "__main__":
    test_developer_team()
