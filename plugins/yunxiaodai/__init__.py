"""Yunxiaodai order-intake plugin tools."""

from __future__ import annotations

from plugins.yunxiaodai.tools import (
    APPLY_INFO_SCHEMA,
    QUERY_AMOUNT_SCHEMA,
    SUBMIT_COMPANY_SCHEMA,
    check_yunxiaodai_available,
    handle_apply_info,
    handle_query_amount,
    handle_submit_company,
)

_TOOLS = (
    ("yunxiaodai_query_amount", QUERY_AMOUNT_SCHEMA, handle_query_amount, "💰"),
    ("yunxiaodai_submit_company", SUBMIT_COMPANY_SCHEMA, handle_submit_company, "🏢"),
    ("yunxiaodai_apply_info", APPLY_INFO_SCHEMA, handle_apply_info, "📄"),
)


def register(ctx) -> None:
    """Register Yunxiaodai tools with Hermes."""
    for name, schema, handler, emoji in _TOOLS:
        ctx.register_tool(
            name=name,
            toolset="yunxiaodai",
            schema=schema,
            handler=handler,
            check_fn=check_yunxiaodai_available,
            emoji=emoji,
        )
