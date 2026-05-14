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
hermers tools
pytest
```

If you prefer not to install the console script yet:

```bash
python -m hermers_agent.cli chat "hello"
```

## Current Scope

Milestone 0 is a local echo agent with a registry-backed tool system. It does
not call an LLM yet. That is deliberate: we first want the control flow to be
obvious before adding provider adapters, streaming, persistence, gateway
platforms, and the dashboard.

## Naming Note

This learning project uses `hermers` because the request used "hermers-agent".
If you want it to match the upstream name exactly later, we can rename the
package and command to `hermes`.
