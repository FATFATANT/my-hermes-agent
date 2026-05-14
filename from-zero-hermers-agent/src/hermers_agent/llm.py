from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol


Message = dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ModelResponse:
    content: str
    tool_calls: list[ToolCall]
    reasoning_content: str = ""


class ChatClient(Protocol):
    def complete(
        self,
        *,
        model: str,
        messages: list[Message],
        tools: list[dict[str, Any]],
    ) -> ModelResponse:
        """Return one chat-completion response."""


class OpenAICompatibleClient:
    """Tiny stdlib OpenAI-compatible Chat Completions client.

    This intentionally implements only the subset we need for Phase 1:
    messages, tools, and assistant tool calls.
    """

    def __init__(self, base_url: str, api_key: str, timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def complete(
        self,
        *,
        model: str,
        messages: list[Message],
        tools: list[dict[str, Any]],
    ) -> ModelResponse:
        if not self.api_key:
            raise RuntimeError("Missing API key. Set OPENAI_API_KEY or config.yaml api_key.")

        body = {
            "model": model,
            "messages": messages,
        }
        if tools:
            body["tools"] = tools

        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Model request failed: HTTP {exc.code}: {detail}") from exc
        # 取0是因为大模型一般支持返回多个候选答案，我们取第一个
        message = raw["choices"][0]["message"]
        return _parse_message(message)


def _parse_message(message: dict[str, Any]) -> ModelResponse:
    tool_calls: list[ToolCall] = []
    for item in message.get("tool_calls") or []:
        function = item.get("function") or {}
        raw_args = function.get("arguments") or "{}"
        try:
            arguments = json.loads(raw_args)
        except json.JSONDecodeError:
            arguments = {"_raw": raw_args}
        tool_calls.append(
            ToolCall(
                id=str(item.get("id", "")),
                name=str(function.get("name", "")),
                arguments=arguments,
            )
        )

    return ModelResponse(
        content=message.get("content") or "",
        tool_calls=tool_calls,
        reasoning_content=message.get("reasoning_content") or "",
    )
