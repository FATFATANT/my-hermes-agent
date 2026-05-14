from hermers_agent.agent import Agent
from hermers_agent.config import Config


def test_chat_uses_local_echo_model(tmp_path):
    agent = Agent(Config(home=tmp_path))

    assert agent.chat("hello") == "[local/echo] hello"


def test_agent_can_call_registered_tool(tmp_path):
    agent = Agent(Config(home=tmp_path))

    assert agent.chat("/tool echo hello") == "hello"
