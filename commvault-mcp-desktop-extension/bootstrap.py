"""
Claude Desktop extension entry point for the Commvault MCP Server.

Claude Desktop collects this bundle's user_config fields (Commvault server
URL, deployment type, and the user's own access/refresh token pair) and
injects them as environment variables before launching this process, per
manifest.json's server.mcp_config.env block.

The vendored server (src/) only ever reads credentials from the OS keyring
(see src/auth/auth_service.py) -- it never accepts them via environment
variable or CLI flag, and it exits immediately if the keyring is empty.
This wrapper bridges the two: it seeds the keyring from the injected
env vars on every launch (uv starts a fresh process each time, so the
keyring must be (re)seeded every run, not just the first), then hands off
to the unmodified server.

src/ is an unmodified vendor copy of github.com/Commvault/commvault-mcp-server
so it can be refreshed from upstream without touching this file.

Mutable runtime state (the log file, the eviction lock file) is kept in a
per-user state directory, never in ${__dirname} -- Claude Desktop owns
${__dirname} (it's the extension's install location) and may wipe or
replace it on update/reinstall, so anything we want to persist or debug
across those events has to live somewhere Desktop doesn't manage.
"""

import os
import signal
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import keyring

from src.utils import get_keyring_service_name


def _state_dir() -> str:
    """
    Cross-platform per-user directory for this extension's own runtime
    files, distinct from ${__dirname}. Created on first use.
    """
    name = "commvault-mcp-extension"
    if sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    elif sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    else:
        base = os.environ.get("XDG_STATE_HOME") or os.path.join(os.path.expanduser("~"), ".local", "state")
    path = os.path.join(base, name)
    os.makedirs(path, exist_ok=True)
    return path


_STATE_DIR = _state_dir()
_LOCK_FILE = os.path.join(_STATE_DIR, "bootstrap.pid")


def _seed_keyring_from_user_config() -> None:
    access_token = os.environ.pop("CV_ACCESS_TOKEN", "").strip()
    refresh_token = os.environ.pop("CV_REFRESH_TOKEN", "").strip()

    if not access_token or not refresh_token:
        print(
            "ERROR: Commvault access token / refresh token not provided. "
            "Set them in the extension's configuration (Claude Desktop > "
            "Settings > Extensions > Commvault).",
            file=sys.stderr,
        )
        sys.exit(1)

    service_name = get_keyring_service_name()
    keyring.set_password(service_name, "access_token", access_token)
    keyring.set_password(service_name, "refresh_token", refresh_token)


def _looks_like_our_process(pid: int) -> bool:
    """
    Guard against PID reuse: only ever act on `pid` as a stale instance of
    this extension if its command line still actually says so. A PID can be
    recycled by the OS for an unrelated process once the original exits, so
    checking liveness alone is not enough before sending it a signal.
    """
    try:
        out = subprocess.run(
            ["ps", "-p", str(pid), "-o", "command="],
            capture_output=True, text=True, timeout=5,
        ).stdout
    except Exception:
        return False
    return "bootstrap.py" in out


def _evict_stale_instance() -> None:
    """
    Claude Desktop does not reliably terminate a prior instance of this
    extension's subprocess when it launches a new one -- observed directly:
    an extension update and a later reconnect both left the previous
    `uv run bootstrap.py` process running for hours, racing the new
    instance for the same OS keyring slot. Credentials live in the OS
    keyring, not in per-process memory, so two live instances silently
    corrupt each other: one instance's successful token refresh rotates
    the refresh token server-side, invalidating the copy the other
    instance still has cached, which then surfaces as a confusing "Failed
    to refresh token" error that looks like credential expiry but is
    actually this concurrency bug.

    Since a .mcpb manifest gives an extension no hook to ask a prior
    instance of itself to shut down, we self-police instead: on startup,
    evict anything recorded in our own lock file before seeding the
    keyring, so at most one instance of this extension is ever live no
    matter what Desktop's own process lifecycle does.
    """
    if os.path.exists(_LOCK_FILE):
        try:
            with open(_LOCK_FILE) as f:
                old_pid = int(f.read().strip())
        except (ValueError, OSError):
            old_pid = None

        if old_pid and old_pid != os.getpid() and _looks_like_our_process(old_pid):
            try:
                os.kill(old_pid, signal.SIGTERM)
                print(f"Terminated a stale prior instance (PID {old_pid}).", file=sys.stderr)
                time.sleep(1)
            except ProcessLookupError:
                pass  # already gone

    with open(_LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))


def _normalize_metallic_server_url() -> None:
    """
    Mirror upstream setup.py's prompt_update_env(): for a Metallic/SaaS
    tenant, CC_SERVER_URL is always the fixed multi-tenant gateway
    https://api.metallic.io, which routes internally based on the auth
    token -- never the tenant's own webserver pod hostname (e.g.
    m119.metallic.io) shown in the browser address bar when logged into
    Command Center. That pod hostname is correct for the web console but
    wrong for the REST API: the on-prem code path in cv_api_client.py
    appends /commandcenter/api/ to CC_SERVER_URL, which the pod hostname
    does not serve, producing 404s on every call.
    """
    if os.environ.get("IS_METALLIC", "false").lower() == "true":
        os.environ["CC_SERVER_URL"] = "https://api.metallic.io"


def main() -> None:
    # MCP_TRANSPORT_MODE is fixed to stdio for the desktop extension -- this
    # process is launched and owned by Claude Desktop as a subprocess, so
    # remote/HTTP transport does not apply here.
    os.environ["MCP_TRANSPORT_MODE"] = "stdio"

    _evict_stale_instance()
    _normalize_metallic_server_url()
    _seed_keyring_from_user_config()

    # src/logger.py opens "cv_mcp.log" as a path relative to the process's
    # CWD, and we don't own that file to add a config override without
    # touching the vendored source. Chdir into the state dir first so the
    # log lands there instead of in Desktop's install directory -- this
    # runs after sys.path was already anchored to ${__dirname} above, and
    # before src.server (and everything it imports, including src.logger)
    # is loaded for the first time, so the relative path resolves here.
    os.chdir(_STATE_DIR)

    from src.server import run_server

    run_server()


if __name__ == "__main__":
    main()
