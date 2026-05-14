from __future__ import annotations

import argparse

from hermers_agent.agent import Agent
from hermers_agent.config import load_config
from hermers_agent.state import SessionStore
from hermers_agent.tools.registry import builtin_registry


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

    subparsers.add_parser("tools", help="List registered tools")

    sessions = subparsers.add_parser("sessions", help="List recent sessions")
    sessions.add_argument("--limit", type=int, default=10, help="Number of sessions to show")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = load_config()
    registry = builtin_registry()
    store = SessionStore(config.database_path)

    if args.command == "chat":
        agent = Agent(config=config, tools=registry)
        history = store.get_messages(args.session) if args.session else []
        before_count = len(history)
        result = agent.run_conversation(" ".join(args.message), history=history)
        session_id = args.session or store.create_session(_title_from_message(args.message))
        store.append_messages(session_id, result.messages[before_count:])
        print(result.final_response)
        print(f"[session: {session_id}]")
        return 0

    if args.command == "tools":
        for tool in registry.list_tools():
            print(f"{tool.name}\t{tool.description}")
        return 0

    if args.command == "sessions":
        for session in store.list_sessions(limit=args.limit):
            print(
                f"{session.id}\t{session.message_count} messages\t"
                f"{session.updated_at}\t{session.title}"
            )
        return 0

    parser.print_help()
    return 0


def _title_from_message(parts: list[str]) -> str:
    title = " ".join(parts).strip()
    return title[:60] or "Untitled session"


if __name__ == "__main__":
    raise SystemExit(main())
