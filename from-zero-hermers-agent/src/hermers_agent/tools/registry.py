from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


ToolHandler = Callable[[dict], str]


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    handler: ToolHandler
    parameters: dict[str, Any]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(
        self,
        name: str,
        description: str,
        handler: ToolHandler,
        parameters: dict[str, Any] | None = None,
    ) -> None:
        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")
        self._tools[name] = Tool(
            name=name,
            description=description,
            handler=handler,
            parameters=parameters or {"type": "object", "properties": {}},
        )

    def list_tools(self) -> list[Tool]:
        return sorted(self._tools.values(), key=lambda tool: tool.name)

    def call(self, name: str, args: dict) -> str:
        tool = self._tools.get(name)
        if tool is None:
            available = ", ".join(tool.name for tool in self.list_tools()) or "none"
            return f"Unknown tool: {name}. Available tools: {available}"
        return tool.handler(args)

    def schemas(self) -> list[dict[str, Any]]:
        # 遍历工具列表，形成工具描述，作为送到大模型的参数之一
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self.list_tools()
        ]


def builtin_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        name="echo",
        description="Return the provided text unchanged.",
        handler=lambda args: str(args.get("text", "")),
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to return.",
                }
            },
            "required": ["text"],
        },
    )
    return registry
