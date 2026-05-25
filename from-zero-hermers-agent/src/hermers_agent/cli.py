from __future__ import annotations

import argparse
import json
import logging
from dataclasses import replace

from hermers_agent.agent import Agent
from hermers_agent.config import Config, load_config
from hermers_agent.logging_config import setup_logging
from hermers_agent.state import SessionStore
from hermers_agent.tools.registry import ToolRegistry, builtin_registry


logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hermers",
        description="From-zero Hermers Agent learning implementation",
    )
    subparsers = parser.add_subparsers(dest="command")

    chat = subparsers.add_parser("chat", help="Send one message to the agent")
    """
    nargs="+"   # 一个或多个
    nargs="*"   # 零个或多个
    nargs="?"   # 零个或一个
    nargs=2    
    """
    chat.add_argument("message", nargs="+", help="Message text")
    chat.add_argument("--session", help="Resume an existing session id")
    chat.add_argument("--model", help="Override the configured model for this turn")
    chat.add_argument("--no-tools", action="store_true", help="Disable tools for this turn")
    chat.add_argument("--toolset", action="append", help="Enable only this toolset; repeatable")
    chat.add_argument("--disable-toolset", action="append", default=[], help="Disable a configured toolset")

    tools = subparsers.add_parser("tools", help="List registered tools")
    tools.add_argument("--json", action="store_true", help="Print tool schemas as JSON")
    tools.add_argument("--toolset", action="append", help="Enable only this toolset; repeatable")
    tools.add_argument("--disable-toolset", action="append", default=[], help="Disable a configured toolset")

    subparsers.add_parser("config", help="Show resolved runtime config")

    sessions = subparsers.add_parser("sessions", help="List recent sessions")
    sessions.add_argument("--limit", type=int, default=10, help="Number of sessions to show")

    search = subparsers.add_parser("search", help="Search saved sessions")
    search.add_argument("query", help="Text to search for")
    search.add_argument("--limit", type=int, default=10, help="Number of matches to show")

    show = subparsers.add_parser("show", help="Show all messages in a session")
    show.add_argument("session_id", help="Session id to inspect")
    show.add_argument("--json", action="store_true", help="Print raw message JSON")

    subparsers.add_parser("logs", help="Show the agent log file path")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = load_config()
    setup_logging(config.home)
    store = SessionStore(config.database_path)

    if args.command == "chat":
        logger.info("chat command started session=%s", args.session or "<new>")
        chat_config = replace(config, model=args.model) if args.model else config
        enabled_toolsets = _resolve_toolsets(config, args)
        tools = ToolRegistry() if args.no_tools else builtin_registry(enabled_toolsets)
        agent = Agent(config=chat_config, tools=tools)
        history = store.get_messages(args.session) if args.session else []
        before_count = len(history)
        result = agent.run_conversation(" ".join(args.message), history=history)
        session_id = args.session or store.create_session(_title_from_message(args.message))
        store.append_messages(session_id, result.messages[before_count:])
        logger.info(
            "chat command completed session=%s saved_messages=%s",
            session_id,
            len(result.messages) - before_count,
        )
        print(result.final_response)
        print(f"[session: {session_id}]")
        return 0

    if args.command == "tools":
        registry = builtin_registry(_resolve_toolsets(config, args))
        if args.json:
            print(json.dumps(registry.schemas(), indent=2, ensure_ascii=False))
            return 0
        for tool in registry.list_tools():
            status = "available" if tool.available else f"unavailable: {tool.unavailable_reason}"
            print(f"{tool.name}\t{tool.toolset}\t{status}\t{tool.description}")
        return 0

    if args.command == "config":
        logger.info("config command")
        print(_format_config(config))
        return 0

    if args.command == "sessions":
        logger.info("sessions command limit=%s", args.limit)
        for session in store.list_sessions(limit=args.limit):
            print(
                f"{session.id}\t{session.message_count} messages\t"
                f"{session.updated_at}\t{session.title}"
            )
        return 0

    if args.command == "search":
        logger.info("search command query=%r limit=%s", args.query, args.limit)
        for session in store.search_sessions(args.query, limit=args.limit):
            preview = f"\t{session.preview}" if session.preview else ""
            print(
                f"{session.id}\t{session.message_count} messages\t"
                f"{session.updated_at}\t{session.title}{preview}"
            )
        return 0

    if args.command == "show":
        logger.info("show command session=%s json=%s", args.session_id, args.json)
        messages = store.get_messages(args.session_id)
        if args.json:
            print(json.dumps(messages, indent=2, ensure_ascii=False))
            return 0
        if not messages:
            print(f"No messages found for session: {args.session_id}")
            return 0
        for index, message in enumerate(messages, start=1):
            role = str(message.get("role", "unknown"))
            print(f"{index}. {role}")
            print(_format_message_content(message))
            print()
        return 0

    if args.command == "logs":
        print(config.log_path)
        return 0

    parser.print_help()
    return 0


def _title_from_message(parts: list[str]) -> str:
    title = " ".join(parts).strip()
    return title[:60] or "Untitled session"


def _format_message_content(message: dict) -> str:
    content = message.get("content")
    if content not in (None, ""):
        return str(content)
    if message.get("tool_calls"):
        return json.dumps(message["tool_calls"], indent=2, ensure_ascii=False)
    return ""


def _format_config(config: Config) -> str:
    rows = [
        ("home", str(config.home)),
        ("database_path", str(config.database_path)),
        ("log_path", str(config.log_path)),
        ("model", config.model),
        ("base_url", config.base_url),
        ("api_key", "<set>" if config.api_key else "<missing>"),
        ("max_iterations", str(config.max_iterations)),
        ("system_prompt", config.system_prompt),
        ("enabled_toolsets", ", ".join(config.enabled_toolsets)),
    ]
    return "\n".join(f"{key}: {value}" for key, value in rows)


def _resolve_toolsets(config: Config, args: argparse.Namespace) -> set[str]:
    toolsets = set(args.toolset or config.enabled_toolsets)
    for disabled in args.disable_toolset:
        toolsets.discard(disabled)
    return toolsets


if __name__ == "__main__":
    raise SystemExit(main())
