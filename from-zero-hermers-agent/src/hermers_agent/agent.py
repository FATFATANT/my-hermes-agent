from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from hermers_agent.config import Config
from hermers_agent.llm import ChatClient, Message, OpenAICompatibleClient
from hermers_agent.tools.registry import ToolRegistry, builtin_registry


@dataclass
class ChatResult:
    final_response: str
    messages: list[Message]


class Agent:
    """Minimal synchronous agent.

    Phase 1 keeps local echo mode, but adds a real OpenAI-compatible loop when
    the configured model is not `local/echo`.
    """

    def __init__(
        self,
        config: Config,
        tools: ToolRegistry | None = None,
        client: ChatClient | None = None,
    ):
        self.config = config
        self.tools = tools or builtin_registry()
        self.client = client or OpenAICompatibleClient(
            base_url=config.base_url,
            api_key=config.api_key,
        )

    def chat(self, message: str) -> str:
        return self.run_conversation(message).final_response

    def run_conversation(self, user_message: str) -> ChatResult:
        messages: list[Message] = [
            {"role": "system", "content": self.config.system_prompt},
            {"role": "user", "content": user_message},
        ]
        if self.config.model == "local/echo":
            response = self._call_local_model(user_message)
            messages.append({"role": "assistant", "content": response})
            return ChatResult(final_response=response, messages=messages)

        for _ in range(self.config.max_iterations):
            response = self.client.complete(
                model=self.config.model,
                messages=messages,
                tools=self.tools.schemas(),
            )
            # 解析大模型原始响应，转换为一条消息记录，以dict形式记录
            assistant_message = self._assistant_message(
                response.content,
                response.tool_calls,
                reasoning_content=response.reasoning_content,
            )
            messages.append(assistant_message)

            if not response.tool_calls:
                return ChatResult(final_response=response.content, messages=messages)

            for tool_call in response.tool_calls:
                tool_result = self.tools.call(tool_call.name, tool_call.arguments)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.name,
                        "content": tool_result,
                    }
                )

        return ChatResult(
            final_response=f"Stopped after {self.config.max_iterations} iterations.",
            messages=messages,
        )

    def _call_local_model(self, user_message: str) -> str:
        if user_message.startswith("/tool "):
            return self._run_tool_command(user_message.removeprefix("/tool ").strip())
        return f"[{self.config.model}] {user_message}"

    def _run_tool_command(self, command: str) -> str:
        name, _, arg_text = command.partition(" ")
        if not name:
            return "Usage: /tool <name> [text]"
        return self.tools.call(name, {"text": arg_text})

    def _assistant_message(
        self,
        content: str,
        tool_calls: list[Any],
        reasoning_content: str = "",
    ) -> Message:
        message: Message = {"role": "assistant", "content": content}
        if reasoning_content:
            message["reasoning_content"] = reasoning_content
        if tool_calls:
            message["tool_calls"] = [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.name,
                        "arguments": json.dumps(tool_call.arguments),  # 将大模型返回的工具调用参数转json，并在后续对话再传回去
                    },
                }
                for tool_call in tool_calls
            ]
        return message
