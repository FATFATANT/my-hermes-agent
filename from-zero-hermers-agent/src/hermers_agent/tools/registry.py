from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


ToolHandler = Callable[[dict], str]
RequirementCheck = Callable[[], bool]


@dataclass(frozen=True)
class Tool:
    name: str
    toolset: str
    description: str
    handler: ToolHandler
    parameters: dict[str, Any]
    available: bool = True
    unavailable_reason: str = ""


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(
        self,
        name: str,
        toolset: str,
        description: str,
        handler: ToolHandler,
        parameters: dict[str, Any] | None = None,
        check_fn: RequirementCheck | None = None,
        unavailable_reason: str = "Requirement check failed.",
    ) -> None:
        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")
        available = check_fn() if check_fn else True
        self._tools[name] = Tool(
            name=name,
            toolset=toolset,
            description=description,
            handler=handler,
            parameters=parameters or {"type": "object", "properties": {}},
            available=available,
            unavailable_reason="" if available else unavailable_reason,
        )

    def list_tools(self, include_unavailable: bool = True) -> list[Tool]:
        tools = self._tools.values()
        if not include_unavailable:
            tools = [tool for tool in tools if tool.available]
        return sorted(tools, key=lambda tool: tool.name)

    def call(self, name: str, args: dict) -> str:
        tool = self._tools.get(name)
        if tool is None:
            available = ", ".join(tool.name for tool in self.list_tools()) or "none"
            return f"Unknown tool: {name}. Available tools: {available}"
        if not tool.available:
            return f"Tool unavailable: {name}. {tool.unavailable_reason}"
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
            for tool in self.list_tools(include_unavailable=False)
        ]


def builtin_registry(enabled_toolsets: set[str] | None = None) -> ToolRegistry:
    enabled_toolsets = enabled_toolsets or {"core", "files"}
    registry = ToolRegistry()
    if "core" in enabled_toolsets:
        registry.register(
            name="echo",
            toolset="core",
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
    if "files" in enabled_toolsets:
        registry.register(
            name="read_file",
            toolset="files",
            description="Read a UTF-8 text file from the current workspace.",
            handler=read_file_tool,
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative or absolute path to read.",
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum characters to return.",
                    },
                },
                "required": ["path"],
            },
        )
        registry.register(
            name="search_files",
            toolset="files",
            description="Search text files under a directory.",
            handler=search_files_tool,
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Text to search for.",
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory or file to search.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum matching lines to return.",
                    },
                },
                "required": ["query"],
            },
        )
    return registry


def read_file_tool(args: dict) -> str:
    path_value = str(args.get("path", "")).strip()
    if not path_value:
        return "Missing required argument: path"

    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists():
        return f"File not found: {path}"
    if not path.is_file():
        return f"Not a file: {path}"

    max_chars = int(args.get("max_chars") or 8000)
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > max_chars:
        return text[:max_chars] + f"\n...[truncated {len(text) - max_chars} chars]"
    return text


def search_files_tool(args: dict) -> str:
    query = str(args.get("query", ""))
    if not query:
        return "Missing required argument: query"

    path_value = str(args.get("path") or ".").strip()
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists():
        return f"Path not found: {path}"

    limit = int(args.get("limit") or 20)
    matches: list[str] = []
    candidates = [path] if path.is_file() else _iter_text_files(path)
    for candidate in candidates:
        try:
            lines = candidate.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line_number, line in enumerate(lines, start=1):
            if query in line:
                display_path = _display_path(candidate)
                matches.append(f"{display_path}:{line_number}: {line}")
                if len(matches) >= limit:
                    return "\n".join(matches)
    if matches:
        return "\n".join(matches)
    return f"No matches for {query!r} under {_display_path(path)}"


def _iter_text_files(path: Path) -> list[Path]:
    ignored_dirs = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}
    files: list[Path] = []
    for candidate in path.rglob("*"):
        if any(part in ignored_dirs for part in candidate.parts):
            continue
        if candidate.is_file():
            files.append(candidate)
    return files


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)
