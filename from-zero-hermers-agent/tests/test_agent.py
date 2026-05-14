import copy
import json

from hermers_agent.agent import Agent
from hermers_agent.config import Config
from hermers_agent.llm import ModelResponse, ToolCall


def test_chat_uses_local_echo_model(tmp_path):
    agent = Agent(Config(home=tmp_path))

    assert agent.chat("hello") == "[local/echo] hello"


def test_agent_can_call_registered_tool(tmp_path):
    agent = Agent(Config(home=tmp_path))

    assert agent.chat("/tool echo hello") == "hello"


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def complete(self, *, model, messages, tools):
        self.calls.append(
            {
                "model": model,
                "messages": copy.deepcopy(messages),
                "tools": tools,
            }
        )
        return self.responses.pop(0)


def test_real_loop_returns_model_content(tmp_path):
    client = FakeClient([ModelResponse(content="hi from model", tool_calls=[])])
    agent = Agent(Config(home=tmp_path, model="test/model"), client=client)

    assert agent.chat("hello") == "hi from model"
    assert client.calls[0]["model"] == "test/model"


def test_real_loop_executes_tool_calls(tmp_path):
    client = FakeClient(
        [
            ModelResponse(
                content="",
                reasoning_content="I should call the echo tool.",
                tool_calls=[
                    ToolCall(id="call_1", name="echo", arguments={"text": "tool says hi"})
                ],
            ),
            ModelResponse(content="tool says hi", tool_calls=[]),
        ]
    )
    agent = Agent(Config(home=tmp_path, model="test/model"), client=client)

    assert agent.chat("please echo") == "tool says hi"
    second_call_messages = client.calls[1]["messages"]
    assert second_call_messages[-2]["reasoning_content"] == "I should call the echo tool."
    tool_call_arguments = second_call_messages[-2]["tool_calls"][0]["function"]["arguments"]
    assert json.loads(tool_call_arguments) == {"text": "tool says hi"}
    assert second_call_messages[-1]["role"] == "tool"
    assert second_call_messages[-1]["content"] == "tool says hi"
