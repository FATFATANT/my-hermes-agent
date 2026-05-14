from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


ToolHandler = Callable[[dict], str]


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    handler: ToolHandler


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, name: str, description: str, handler: ToolHandler) -> None:
        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")
        self._tools[name] = Tool(name=name, description=description, handler=handler)

    def list_tools(self) -> list[Tool]:
        return sorted(self._tools.values(), key=lambda tool: tool.name)

    def call(self, name: str, args: dict) -> str:
        tool = self._tools.get(name)
        if tool is None:
            available = ", ".join(tool.name for tool in self.list_tools()) or "none"
            return f"Unknown tool: {name}. Available tools: {available}"
        return tool.handler(args)


def builtin_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        name="echo",
        description="Return the provided text unchanged.",
        handler=lambda args: str(args.get("text", "")),
    )
    return registry
