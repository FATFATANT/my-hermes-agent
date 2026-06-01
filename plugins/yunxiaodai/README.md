# Yunxiaodai Plugin

This plugin provides three Hermes tools for Yunxiaodai order intake:

- `yunxiaodai_query_amount`
- `yunxiaodai_submit_company`
- `yunxiaodai_apply_info`

The matching skill lives at:

```text
skills/business/yunxiaodai-order-intake/SKILL.md
```

## Local Configuration

The default API base URL is:

```text
http://158.4.90.21:8084
```

Override it in `~/.hermes/.env` when needed:

```text
YUNXIAODAI_API_BASE_URL=http://your-internal-host:8084
YUNXIAODAI_WEB_ORIGIN=http://your-internal-host:8087
```

The user must provide a Yunxiaodai login token before these tools operate. The
tools pass it as:

```text
token: <user-provided-token>
Cookie: token=<user-provided-token>
Origin: $YUNXIAODAI_WEB_ORIGIN
Referer: $YUNXIAODAI_WEB_ORIGIN/mloanstatic/
```

Do not hardcode tokens in this plugin or in `~/.hermes/.env`. Tokens should be
provided by the user for the current operation.

If your internal API requires extra signatures or request ids, add that logic in
`plugins/yunxiaodai/tools.py` inside `_headers()` or `_post()`.

## Bundled Usage

When this directory is inside the repository's `plugins/` directory, it is a
bundled backend plugin and loads automatically.

Use the toolset explicitly when you want to restrict a session to these tools:

```bash
hermes --toolsets yunxiaodai
```

## Internal Network Deployment

Copy these directories into the internal Hermes checkout:

```text
plugins/yunxiaodai/
skills/business/yunxiaodai-order-intake/
```

Then configure the internal host:

```text
YUNXIAODAI_API_BASE_URL=http://158.4.90.21:8084
YUNXIAODAI_WEB_ORIGIN=http://158.4.90.21:8087
```

For a user-installed plugin instead of a repository-bundled plugin, copy
`plugins/yunxiaodai/` to:

```text
~/.hermes/plugins/yunxiaodai/
```

Then enable it:

```bash
hermes plugins enable yunxiaodai
```

User-installed skills can be copied to:

```text
~/.hermes/skills/yunxiaodai-order-intake/SKILL.md
```

For production use, prefer the repository-bundled layout so code review,
versioning, and deployment are handled together.
