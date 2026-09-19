#!/usr/bin/env python3
"""PreToolUse, Edit|Write|Bash, every agent and the lead: state, the log, private storage, pairs, verdicts, the
workbench, the installed controller and the role definitions are written by the controller and nobody else. A run
that wants a helper script is BLOCKED; it never writes tooling."""
import os
import re

from _paths import WRITES, allow, deny, inside, path_tokens, payload, project, resolve, shell_base

OPEN = (".gauntlet/wt", ".gauntlet/staging")  # builders and authors write here
ROLES = ("reader.md", "reader-alt.md", "editor.md", "editor-fast.md", "author.md")
REASON = ("controller-only: run state and the run's tooling change only through gauntletctl. If you need a fact recorded, "
          "there is a command for it; if you need tooling that does not exist, mark the piece BLOCKED.")


def protected(real, root, agent_type=None):
    if inside(real, os.path.join(root, ".gauntlet")):
        # a reader may leave a scratch script inside its pair (critic_blind confines it to its own); swap never reads it
        mine = OPEN + ((".gauntlet/pairs",) if agent_type in ("reader", "reader-alt") else ())
        return not any(inside(real, os.path.join(root, o)) for o in mine)
    if inside(real, os.path.join(root, ".claude", "hooks", "gauntlet")):
        return True
    return os.path.dirname(real) == os.path.join(root, ".claude", "agents") and os.path.basename(real) in ROLES


def main():
    p = payload()
    root = project()
    ti = p.get("tool_input", {})
    if p.get("tool_name") != "Bash":
        target = ti.get("file_path", "")
        if protected(resolve(target, root), root, p.get("agent_type")):
            deny(REASON, "BOUNDARY_BLOCK", p, target)
        allow()
    command = ti.get("command", "")
    if re.search(r"gauntletctl\S*\s+attest\b", command):
        deny("controller-only: attest is the harness's hook and never a tool call.", "BOUNDARY_BLOCK", p, command)
    if re.search(r"gauntletctl\S*\s+\w", command) and not re.search(r"&&|\|\||[;|<>`]|\$\(", command):
        allow()  # the controller alone on the line; a compound command gets the checks below
    staging = re.search(r"\bgit\s+add\b", command)
    if staging and (re.search(r"\s(-f|--force)\b", command) or ".gauntlet" in command):
        deny("controller-only: run artifacts are staged by `gauntletctl commit`, after its secret scan.", "BOUNDARY_BLOCK", p, command)
    if WRITES.search(command):
        base = shell_base(command, root)
        if any(protected(resolve(token, base), root, p.get("agent_type")) for token in path_tokens(command)):
            deny(REASON, "BOUNDARY_BLOCK", p, command)
    allow()


if __name__ == "__main__":
    main()
