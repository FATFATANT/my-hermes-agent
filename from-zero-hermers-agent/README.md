# From-Zero Hermers Agent

This is a learning implementation of Hermes Agent, rebuilt incrementally from
scratch. The goal is not to copy files from the parent project, but to recreate
the architecture one small, runnable milestone at a time.

The directory intentionally starts tiny:

- a CLI entry point
- a minimal synchronous agent loop
- a tool registry
- one example tool
- tests for the first behavior

As we progress, each milestone should keep the project runnable.

## Quick Start

```bash
cd from-zero-hermers-agent
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[dev]"
hermers --help
hermers chat "hello"
hermers chat --model local/echo "hello"
hermers chat --no-tools "hello"
hermers chat --toolset files "/tool read_file {\"path\":\"README.md\"}"
hermers tools
hermers tools --json
hermers tools --disable-toolset files
hermers config
hermers sessions
hermers search hello
hermers show <session-id>
hermers logs
pytest
```

If you prefer not to install the console script yet:

```bash
python -m hermers_agent.cli chat "hello"
```

## Current Scope

Milestone 1 includes a real OpenAI-compatible chat loop while keeping
`local/echo` as the default offline mode.

To use a real model, create `~/.hermers/config.yaml`:

```yaml
model: gpt-4.1-mini
base_url: https://api.openai.com/v1
api_key: sk-...
max_iterations: 8
enabled_toolsets:
  - core
  - files
```

Or use environment variables:

```bash
export OPENAI_API_KEY=sk-...
export OPENAI_BASE_URL=https://api.openai.com/v1
hermers chat "Use the echo tool with text hello"
```

The loop now supports:

- OpenAI-compatible `/chat/completions`
- message history for one turn
- function-tool schemas
- assistant tool calls
- tool result messages
- max-iteration stopping
- SQLite-backed session history

Each `chat` command saves a session and prints its id:

```bash
hermers chat "hello"
# [session: ...]
```

Resume a session with:

```bash
hermers chat --session <session-id> "continue from there"
```

Override the model for one chat command:

```bash
hermers chat --model local/echo "hello"
```

Disable tools for one chat command:

```bash
hermers chat --no-tools "hello"
```

Limit tools for one chat command:

```bash
hermers chat --toolset files "/tool read_file {\"path\":\"README.md\"}"
hermers chat --disable-toolset files "/tool echo hello"
```

Messages that start with `/tool ` execute the named local tool directly, even
when the configured model is remote.

Show the resolved runtime config:

```bash
hermers config
```

List recent sessions:

```bash
hermers sessions
```

Search saved sessions:

```bash
hermers search "hello"
```

Show every message in a session:

```bash
hermers show <session-id>
hermers show <session-id> --json
```

Show the log file path:

```bash
hermers logs
```

Inspect tool schemas:

```bash
hermers tools
hermers tools --json
hermers tools --disable-toolset files
```

Built-in toolsets:

```text
core   echo
files  read_file, search_files
```

## Naming Note

This learning project uses `hermers` because the request used "hermers-agent".
If you want it to match the upstream name exactly later, we can rename the
package and command to `hermes`.
