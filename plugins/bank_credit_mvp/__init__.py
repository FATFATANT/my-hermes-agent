"""Bank credit workflow MVP plugin.

The dashboard portion is discovered independently by Hermes dashboard. These
tool registrations let the agent inspect and advance the same workflow state
from chat once the plugin is enabled in config.
"""

from __future__ import annotations

from plugins.bank_credit_mvp.tools import TOOLS


def register(ctx) -> None:
    for name, schema, handler in TOOLS:
        ctx.register_tool(
            name=name,
            toolset="bank_credit",
            schema=schema,
            handler=handler,
        )
