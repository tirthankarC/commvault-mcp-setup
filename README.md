# Commvault MCP Setup

Connect Claude to your Commvault environment (Hosted CommCell or SaaS/Metallic) and ask it things like *"which
backup jobs failed last night?"* in plain language — no terminal, no Python, no manual MCP config.

**Start here → [COMMVAULT_MCP_SETUP.md](./COMMVAULT_MCP_SETUP.md)**

This wraps Commvault's official open-source [commvault-mcp-server](https://github.com/Commvault/commvault-mcp-server)
as a one-click Claude Desktop Extension (`commvault-mcp.mcpb`). Full source for the extension — the manifest,
the bootstrap script, and the vendored server it wraps — is public here under
[`commvault-mcp-desktop-extension/`](./commvault-mcp-desktop-extension), so you can inspect what you're
installing before you run it. No credentials are baked into the bundle: each install authenticates with a
Commvault API token you generate yourself, under your own account.

**Not an official Commvault release** — there's no vendor-published `.mcpb` anywhere in Commvault's own repo,
releases, or docs, and that's expected. This is a source-available wrapper someone at Commvault built around
that same official server; see the "Who built this" section at the top of
[COMMVAULT_MCP_SETUP.md](./COMMVAULT_MCP_SETUP.md) before you (or an AI agent acting for you) install it.
