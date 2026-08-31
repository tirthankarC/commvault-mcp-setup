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

## Status, and the path to this becoming official

This is a pilot, not a pitch you have to accept wholesale. Concretely, that means:

- **It's opt-in and per-person.** Nobody is pushed this — you decide to try it, with your own token, revocable
  by you at any time in Command Center. Nothing here changes if you don't install it.
- **Default setup is read-only.** [Step 1 of the guide](./COMMVAULT_MCP_SETUP.md#step-1--generate-your-own-api-access-token)
  now recommends a Custom, view-only token scope by default — job control and user management are opt-in, not
  the starting point. A misused or leaked token under the recommended scope can look at your environment; it
  can't change anything in it.
- **The blast radius is bounded by what you already trust.** Every action this extension takes runs through
  Commvault's own API, under your own account, subject to your own RBAC. It doesn't introduce a new trust
  boundary so much as it puts your existing one behind a chat interface.
- **Trying it doesn't require Commvault's sign-off, and it also doesn't substitute for it.** The honest reason
  this hasn't gone through an official channel yet is that there isn't a published Commvault MCP certification
  or extension-marketplace process for it to go through — not that it was submitted and rejected. If Commvault
  publishes one, this should go through it; until then, this repo is the closest thing available, offered
  transparently as exactly that: unofficial, source-available, and reviewed in the open (see the
  [security scorecard findings](./COMMVAULT_MCP_SETUP.md) referenced in commit history) rather than asserted
  as safe.

If you're evaluating this for a team rather than yourself: the read-only default and per-user tokens mean a
small pilot with a few opted-in people carries materially less risk than a blanket rollout — you don't need to
wait for an official release to learn whether this is useful, only to decide how far to take it before one
exists.

## Maintainer &amp; support

Built and maintained by [Tirthankar Chatterjee](https://github.com/tirthankarC), best-effort, as a personal
project — not a Commvault-supported product and not covered by any SLA. Issues and PRs are welcome via
[GitHub Issues](https://github.com/tirthankarC/commvault-mcp-setup/issues). If you're relying on this for more
than a personal pilot, treat the lack of a formal support commitment as a real constraint, not a formality —
see [Governance &amp; Distribution Fit](./COMMVAULT_MCP_SETUP.md) for what that gap means in practice.
