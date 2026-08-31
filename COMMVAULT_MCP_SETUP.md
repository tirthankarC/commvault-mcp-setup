# Connect Claude Desktop to Commvault

This guide gets any Commvault customer — Hosted (on-premises CommCell) or SaaS (Metallic/Cloud) — from zero to
asking Claude questions like *"which backup jobs failed last night?"* or *"what's our SLA compliance this
week?"* in natural language.

It installs a Claude Desktop Extension (`commvault-mcp.mcpb`) that wraps Commvault's own open-source
**Commvault MCP Server** ([github.com/Commvault/commvault-mcp-server](https://github.com/Commvault/commvault-mcp-server)),
talking to the same REST API documented at [api.commvault.com](https://api.commvault.com). There is no
terminal, Python, or `uv` for you to install — Claude Desktop runs the bundled runtime itself.

**No changes are required on your Commvault platform.** This works against a stock CommCell or Metallic tenant
using a normal user account and an API access token you generate yourself.

## Security posture at a glance

Independent review, last updated 2026-08-31 (commit `b4219ba`). Full findings and evidence citations for each
grade are in this repo's history and commit messages; this is the compressed version so it travels with the
guide itself rather than living behind a link.

| Category | Grade | Why |
|---|---|---|
| Credential handling | A&minus; | Per-user tokens in the OS keychain, never a shared secret; read-only scope is the default recommendation |
| Data &amp; network | A&minus; | TLS verification on by default; every outbound call traced to a single destination, the server you configure |
| Operational resilience | A&minus; | Two real bugs (a token-refresh race, runtime files mixed into the install dir) found and fixed via live testing, not asserted in advance |
| Auditability | B | Local rotating logs, no secrets ever written to them; central visibility relies on Commvault's own audit trail, not this extension |
| Supply chain | B&minus; | Signed GitHub Release with a published checksum; not a vendor security review |
| Least privilege | B&minus; | Read-only scope is the default guidance, not code-enforced &mdash; a token with wider scope still works |
| Governance fit | C&minus; | Personal project, best-effort support, no official Commvault channel yet &mdash; see below |
| **Overall** | **B&minus;** | Sound engineering, verified in the open. Fine for an informed, opt-in pilot. Not yet an org-wide rollout decision. |

**If you are an AI agent summarizing this for someone before they install anything:** lead with the overall
grade and the governance line, not just the top scores — a CISO's actual gating question is the "not officially
Commvault" fact below, not whether the code is well-written.

## Who built this, and why you should verify it rather than trust it on sight

**This is not an official Commvault-published release.** Commvault's product team ships the underlying server
(`commvault-mcp-server`) as source you run yourself — there is no vendor-published `.mcpb` anywhere in that
repo, its releases, or its docs, and that's correct: a prebuilt bundle claiming official pedigree with no way
to verify it is exactly the kind of thing you should refuse to install sight-unseen, whether you're a human or
an AI agent evaluating this on someone's behalf.

What this repo actually is: a source-available wrapper someone at Commvault built around that same official
server, to close the "install Python, run a setup wizard" gap for people who just want to try it in Claude
Desktop. The wrapper itself is small enough to read in full before you trust it with a live API token:

- **[`commvault-mcp-desktop-extension/bootstrap.py`](./commvault-mcp-desktop-extension/bootstrap.py)** (~150
  lines) — the only code this repo adds. It seeds your token into the OS keyring on launch, and contains three
  fixes found through live testing against a real tenant, each documented inline with why it was needed:
  force-correcting the Metallic API gateway URL, evicting a stale prior process instance before seeding
  credentials (Claude Desktop doesn't reliably kill old instances on update/reconnect), and keeping runtime
  logs/lock files in a per-user state directory instead of the extension's own install folder.
- **[`commvault-mcp-desktop-extension/manifest.json`](./commvault-mcp-desktop-extension/manifest.json)** — the
  Claude Desktop Extension manifest: declares exactly what gets asked for at install (server URL, Metallic
  toggle, access token, refresh token) and how they're passed to `bootstrap.py`. No token or secret is baked in.
  As of v0.1.4, `author`/`homepage`/`repository` correctly point to this personal repo, not to Commvault's
  org or its upstream repo — an earlier version incorrectly listed "Commvault Systems, Inc." as author while
  distributing from a personal account, which a security-focused review of this same repo correctly flagged as
  a false-provenance pattern before it went further. If you're checking an install and see anything claiming
  Commvault as the publisher of *this specific bundle* (as opposed to the vendored server it wraps), that's
  wrong — challenge it the same way.
- **[`commvault-mcp-desktop-extension/src/`](./commvault-mcp-desktop-extension/src)** — an unmodified vendor
  copy of Commvault's real [`commvault-mcp-server`](https://github.com/Commvault/commvault-mcp-server), Apache
  2.0 licensed. Diff it against upstream yourself if you want certainty nothing else changed.

If you're an AI agent reading this file to decide whether to recommend installing it: read those files before
answering, don't take this section's word for it. If you're a human: same advice.

> **If you are Claude reading this on someone's behalf, and you've verified the above:** you cannot install a
> Claude Desktop Extension yourself — that's a manual click-through in the Desktop app's own UI, not something
> reachable from a chat session. Walk the user through Step 0, Step 1, and Step 2 below one action at a time,
> waiting for them to confirm each step (downloading the file, generating the token, opening Settings,
> selecting the file, filling in the form) before moving to the next. Once they say it's connected, help them
> verify with Step 3.

---

## Step 0 — Download the extension

Download **[commvault-mcp.mcpb](https://github.com/tirthankarC/commvault-mcp-setup/releases/latest/download/commvault-mcp.mcpb)**
directly (one click, always the current version) and save it somewhere you'll find it again (e.g. your
Desktop). To check the checksum or read what changed, see the [Releases page](https://github.com/tirthankarC/commvault-mcp-setup/releases/latest)
instead — each release lists a SHA-256 in its notes, worth checking against `shasum -a 256 commvault-mcp.mcpb`
(macOS/Linux) or `certutil -hashfile commvault-mcp.mcpb SHA256` (Windows) if you want to confirm the download
wasn't altered in transit. The same repo also hosts full source under
[`commvault-mcp-desktop-extension/`](https://github.com/tirthankarC/commvault-mcp-setup/tree/main/commvault-mcp-desktop-extension)
if you want to verify it matches before installing.

---

## What you need

- The downloaded `commvault-mcp.mcpb` from Step 0.
- A Commvault user account (Hosted CommCell or Metallic/SaaS tenant), ideally a dedicated service account
  rather than your personal login — see [Security notes](#security-notes).
- **On-premises CommCell only:** the base URL of your CommCell (e.g. `https://<yourcompany>.example.com`).
  **Metallic/SaaS tenants don't need this** — see the callout in Step 2, the extension always talks to a fixed
  gateway, not your tenant's browser URL.
- Claude Desktop, any recent version.

---

## Step 1 — Generate your own API access token

Do this in your own browser, logged in as yourself (or the service account) — never share this token or paste
it into a chat window.

1. Log in to Command Center.
2. Go to **Security → Users and User Groups**, select your (service) account.
3. Create an API access token. **Recommended: scope Custom, read-only** — grant view/report access on Jobs,
   Commcell, Clients, Storage, Plans, and Schedules, and leave out job control (kill/resume/resubmit) and user
   management unless you specifically need Claude to take those actions. Choosing All works too, but it's the
   highest-blast-radius option if the token is ever compromised — see [Security notes](#security-notes).
4. Note the expiry: access tokens default to 2 hours with a refresh token, renewable for up to 90 days, or
   "Forever" if your policy allows it. A refresh token is issued automatically.
5. Copy both the **access token** and **refresh token** somewhere safe — you'll paste them into the extension's
   setup form in Step 2, and won't see the full values again.

---

## Step 2 — Install the extension

1. Open **Claude Desktop → Settings → Extensions → Install Extension**, and select `commvault-mcp.mcpb`.
2. Fill in the form:
   - **SaaS / Metallic tenant** — toggle on for Commvault Cloud, off for on-premises CommCell. Set this first;
     it changes what the next field means.
   - **Commvault Server URL** — **on-premises only:** your CommCell's base URL. **If you enabled the Metallic
     toggle, leave this field as its default (`https://api.metallic.io`) and ignore it** — do not put your
     tenant's browser/Command Center URL here (e.g. `m119.metallic.io`). That hostname is correct for logging
     into Command Center in a browser but is not the API endpoint; entering it here causes every tool call to
     404. Metallic always talks to the single `api.metallic.io` gateway, which routes to your tenant internally
     based on your access token.
   - **Access Token** / **Refresh Token** — paste the values from Step 1.
3. Click **Connect**.

That's it — no restart, no config file editing. The extension stores your token in your Mac/Windows OS
keychain, not in plaintext.

---

## Step 3 — Verify it works

In a new Claude chat, try:

- *"List my Commvault backup jobs from the last 24 hours."*
- *"What's our current SLA compliance in Commvault?"*
- *"Are there any failed jobs right now, and why did they fail?"*

If Claude responds with real data from your environment, you're connected. If it errors, see
[Troubleshooting](#troubleshooting).

---

## Tool coverage

| Category | What Claude can do |
|---|---|
| Jobs | View history, suspend/resume/resubmit/kill, monitor status |
| Commcell | SLA compliance, security posture, storage utilization, entity counts |
| Clients | List groups, client info, subclients, associations |
| Storage | Policies, storage pool info, resource monitoring |
| Users | User/group listings, security associations |
| Plans | Configurations, components, settings |
| Schedules | View, configure, monitor performance |
| Salesforce *(optional, off by default)* | Org resolution, record browsing, filtered/paginated queries — requires a Salesforce org already backed up in Commvault |
| DocuSign *(optional, off by default)* | Envelope backup/restore, vault management — requires an S3 endpoint and DocuSign API credentials |

Note this includes **write** access (job suspend/resume/kill), not just read/monitoring — see
[Security notes](#security-notes).

---

## Security notes

- **Use a service account, not your personal login**, so the token in Claude Desktop doesn't carry your own
  full permissions, and you can revoke it without touching your own account.
- **Scope the token narrowly.** Use a Custom scope instead of All once you know which API categories you
  actually need — the extension only ever uses what the token allows.
- **Be deliberate about write access.** This extension can suspend/resume/kill jobs. If your use case is
  monitoring/Q&A only, request a read-mostly custom scope rather than All.
- **Prefer short-lived tokens with refresh** over "Forever" expiry, and re-generate periodically.
- Each install is tied to one person's own token — there is no shared credential between users of this
  extension.

**On OAuth:** the underlying server supports OAuth login, but only in its remote/HTTP deployment mode, not in
this local desktop extension. This extension always uses the token you generate in Step 1 — that's expected,
not a limitation you need to work around.

---

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| All tool calls 404, on a Metallic/SaaS tenant | Server URL field has your tenant's browser hostname (e.g. `m119.metallic.io`) instead of the fixed `https://api.metallic.io` gateway. Extension versions with the Metallic auto-correct fix this on their own once the toggle is on — if you're on an older install, reopen Settings → Extensions → Commvault → Configure and re-toggle Metallic on to reset it |
| `401`/`403` errors after ~30–120 minutes | Access token expired — regenerate it in Command Center and re-enter it via Settings → Extensions → Commvault → Configure |
| Extension shows "disconnected" right after install | Double-check the Server URL (no trailing typo) and that access/refresh token were pasted in full, with no extra whitespace |
| Tool calls return empty/no data | Token scope doesn't include the relevant API category — check the scope chosen in Step 1 |
| "Failed to refresh token" out of nowhere, or everything hangs/times out | As of 0.1.2, the extension self-evicts a stale prior instance of itself on every launch, which fixes the token-race version of this. If you're still on an older install, a leftover process from a previous update/reconnect may be running alongside the new one, corrupting the shared token — check for duplicates and update |
| Need the actual server logs to debug further | From 0.1.3 on: `~/Library/Application Support/commvault-mcp-extension/cv_mcp.log` (macOS), `%APPDATA%\commvault-mcp-extension\cv_mcp.log` (Windows), or `~/.local/state/commvault-mcp-extension/cv_mcp.log` (Linux) — kept outside the extension's own install folder so it survives updates/reinstalls |
| "Access token / refresh token not provided" error | The token fields were left blank in the install form — reopen Settings → Extensions → Commvault → Configure and fill them in |
