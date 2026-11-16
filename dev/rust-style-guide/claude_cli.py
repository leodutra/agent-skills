"""One lean `claude -p` call, shared by bench.py and rules.py: no settings, no MCP, no session kept,
only the tools named. It spends the user's claude.ai usage, and the sandbox blocks the API."""
import json
import subprocess


def claude(prompt, cwd, system=None, tools="", extra=(), replace_system=False, model="sonnet", dry_run=False):
    cmd = ["claude", "-p", prompt, "--tools", tools, "--setting-sources", "", "--strict-mcp-config",
           "--no-session-persistence", "--model", model, "--output-format", "json", *extra]
    if system: cmd += ["--system-prompt" if replace_system else "--append-system-prompt", system]
    if dry_run: return {"result": "", "usage": {}, "dry_run": " ".join(cmd[:2] + cmd[3:])[:300]}
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=1800)
    try:
        out = json.loads(p.stdout)
    except ValueError as exc:
        raise RuntimeError(f"claude returned non-JSON (exit {p.returncode}): {(p.stdout + p.stderr)[-1000:]}") from exc
    if p.returncode or out.get("is_error") or out.get("terminal_reason") == "api_error":
        reason = out.get("api_error") or out.get("error") or out.get("result") or p.stderr
        raise RuntimeError(f"claude failed (exit {p.returncode}): {str(reason)[:500]}")
    return out
