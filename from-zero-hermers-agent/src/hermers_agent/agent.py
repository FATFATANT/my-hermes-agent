from __future__ import annotations

from dataclasses import dataclass

from hermers_agent.config import Config
from hermers_agent.tools.registry import ToolRegistry, builtin_registry


@dataclass
class ChatResult:
    final_response: str


class Agent:
    """Minimal synchronous agent.

    The first milestone uses a local echo model so the control flow remains
    visible. Later phases will replace `_call_model` with provider adapters and
    tool-call handling.
    """

    def __init__(self, config: Config, tools: ToolRegistry | None = None):
        self.config = config
        self.tools = tools or builtin_registry()

    def chat(self, message: str) -> str:
        return self.run_conversation(message).final_response

    def run_conversation(self, user_message: str) -> ChatResult:
        response = self._call_model(user_message)
        return ChatResult(final_response=response)

    def _call_model(self, user_message: str) -> str:
        if user_message.startswith("/tool "):
            return self._run_tool_command(user_message.removeprefix("/tool ").strip())
        return f"[{self.config.model}] {user_message}"

    def _run_tool_command(self, command: str) -> str:
        name, _, arg_text = command.partition(" ")
        if not name:
            return "Usage: /tool <name> [text]"
        return self.tools.call(name, {"text": arg_text})
