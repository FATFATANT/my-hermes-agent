from __future__ import annotations

import argparse

from hermers_agent.agent import Agent
from hermers_agent.config import load_config
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

    subparsers.add_parser("tools", help="List registered tools")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = load_config()
    registry = builtin_registry()

    if args.command == "chat":
        agent = Agent(config=config, tools=registry)
        print(agent.chat(" ".join(args.message)))
        return 0

    if args.command == "tools":
        for tool in registry.list_tools():
            print(f"{tool.name}\t{tool.description}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
