# Incremental Roadmap

The north star is feature parity with the parent Hermes Agent project. The path
below is designed so each step has a small, testable result.

## Phase 0: Skeleton

- CLI entry point: `hermers`
- Minimal config loader
- Minimal `Agent.chat()`
- Tool registry and one built-in tool
- Basic tests

## Phase 1: Real Model Loop

- [x] Add OpenAI-compatible chat completions client
- [x] Add provider config from env/config file
- [x] Add message history
- [x] Add tool-call parsing and dispatch
- [x] Add max-iteration budget
- [ ] Add streaming responses
- [x] Add multi-turn persisted history

Reference in parent project:

- `run_agent.py`
- `model_tools.py`
- `tools/registry.py`
- `toolsets.py`

## Phase 2: Sessions and State

- [x] SQLite session store
- [x] Save and resume conversations
- [x] Session search
- [x] Basic logging

Reference in parent project:

- `hermes_state.py`
- `hermes_logging.py`
- `hermes_constants.py`

## Phase 3: CLI Experience

- Rich output
- Slash commands
- Model selection
- Tool configuration
- Prompt history and autocomplete

Reference in parent project:

- `cli.py`
- `hermes_cli/main.py`
- `hermes_cli/commands.py`

## Phase 4: Tool System

- Toolsets
- Requirement checks
- Tool schemas
- Terminal tool
- File/search tools
- Browser/MCP hooks later

Reference in parent project:

- `tools/`
- `tools/registry.py`
- `model_tools.py`

## Phase 5: Dashboard

- FastAPI backend
- React/Vite frontend
- Config and env pages
- Session pages

Reference in parent project:

- `hermes_cli/web_server.py`
- `web/src/`

## Phase 6: TUI and Embedded Chat

- Ink TUI
- Python JSON-RPC gateway
- PTY bridge
- Dashboard-embedded terminal chat

Reference in parent project:

- `ui-tui/src/`
- `tui_gateway/server.py`
- `hermes_cli/pty_bridge.py`

## Phase 7: Messaging Gateway

- Platform-neutral message event model
- Gateway runner
- Telegram or webhook adapter first
- Active-session guards and interruption

Reference in parent project:

- `gateway/run.py`
- `gateway/platforms/base.py`
- `gateway/platforms/telegram.py`

## Phase 8: Skills, Plugins, Memory

- Skill loader
- Plugin manager
- Memory provider interface
- Built-in memory provider

Reference in parent project:

- `agent/skill_commands.py`
- `hermes_cli/plugins.py`
- `agent/memory_manager.py`
- `plugins/memory/`
