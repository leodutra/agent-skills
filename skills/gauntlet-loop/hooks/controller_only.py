#!/usr/bin/env python3
"""PreToolUse, Read|Glob|Grep|Edit|Write|Bash, every agent and the lead: state, the log, private storage, pairs, verdicts,
the workbench, the installed controller and the role definitions are written by the controller and nobody else, and
private storage is read by it alone. A permission deny would do the reading half, but the harness merges those into the
sandbox, where they would mask the files from the sandboxed controller too (F9). A run that wants a helper script is
BLOCKED; it never writes tooling."""
import os
import re

from _paths import (ALONE, allow, controller_alone, deny, glob_base, inside, path_tokens, payload, policy, project, resolve,
                    shell_base, unresolved, write_targets)

C = policy()["controller_only"]  # trees and files nobody writes; `open` is where builders and authors do
REASON = ("controller-only: run state and the run's tooling change only through gauntletctl. If you need a fact recorded, "
          "there is a command for it; if you need tooling that does not exist, mark the piece BLOCKED.")
PRIVATE = "controller-only: .gauntlet/private/ is read by the controller alone; ask it (`gauntletctl status --full`, `next`)."
SOURCE = ("controller-only: during a run the lead never reads the controller's or the hooks' source; it would ride in every "
          "later call. The interface is `next`, `--help` and a refusal's reason.")
READERS = r"\b(cat|sed|head|tail|less|more|bat|nl|awk|grep|rg|wc|strings)\b[^|;&]*"


def live():
    """A run is going: its log exists and has no end yet."""
    try:
        with open(os.path.join(project(), ".gauntlet", "events.jsonl")) as f:
            return '"RUN_ENDED"' not in f.read()
    except OSError:
        return False


def tooling(real, root):
    return inside(real, os.path.join(root, C["trees"][1]))


def protected(real, root, agent_type=None):
    # a reader may leave a scratch script inside its pair (critic_blind confines it to its own); swap never reads it
    mine = C["open"] + (C["reader_open"] if agent_type in ("reader", "reader-alt") else [])
    if any(inside(real, os.path.join(root, o)) for o in mine):
        return False
    return any(inside(real, os.path.join(root, t)) for t in C["trees"]) or real in [os.path.join(root, f) for f in C["files"]]


def unreadable(real, root):
    """Private storage: the mapping, the run secret, the attestation key. No tool reads it; the controller does (F9)."""
    return any(inside(real, os.path.join(root, t)) for t in C["unreadable"])


def main():
    p = payload()
    root = project()
    ti = p.get("tool_input", {})
    if p.get("tool_name") in ("Read", "Glob", "Grep"):
        target = ti.get("file_path") or ti.get("path") or "."
        if p.get("tool_name") == "Glob":
            target = os.path.join(target, glob_base(ti.get("pattern", "")))
        if unreadable(resolve(target, root), root):
            deny(PRIVATE, "BOUNDARY_BLOCK", p, target)
        if not p.get("agent_type") and tooling(resolve(target, root), root) and live():  # the lead's context (F44)
            deny(SOURCE, "BOUNDARY_BLOCK", p, target)
        allow()
    if p.get("tool_name") != "Bash":
        target = ti.get("file_path", "")
        if protected(resolve(target, root), root, p.get("agent_type")):
            deny(REASON, "BOUNDARY_BLOCK", p, target)
        allow()
    command = ti.get("command", "")
    if re.search(r"gauntletctl\S*\s+attest\b", command):
        deny("controller-only: attest is the harness's hook and never a tool call.", "BOUNDARY_BLOCK", p, command)
    if controller_alone(command):
        allow()
    if not p.get("agent_type") and re.search(READERS + re.escape(C["trees"][1]), command) and live():  # F44
        deny(SOURCE, "BOUNDARY_BLOCK", p, command)
    base = shell_base(command, root)
    if any(unreadable(resolve(token, base), root) for token in path_tokens(command, base)):
        deny(PRIVATE, "BOUNDARY_BLOCK", p, command)
    reason = REASON + (ALONE if "gauntletctl" in command else "")
    if re.search(r"\bgit\b(\s+-C\s+\S+)?\s+add\b", command):  # staging a piece's own worktree is fine (F26)
        gauntlet, worktrees = os.path.join(root, ".gauntlet"), os.path.join(root, ".gauntlet", "wt")
        run_files = [r for r in (resolve(t, base) for t in path_tokens(command, base)) if inside(r, gauntlet) and not inside(r, worktrees)]
        if re.search(r"\s(-f|--force)\b", command) or run_files:
            deny("controller-only: run artifacts are staged by `gauntletctl commit`, after its secret scan.", "BOUNDARY_BLOCK", p, command)
    guarded = lambda t: protected(resolve(t, base), root, p.get("agent_type"))
    targets = write_targets(command, base)
    # a target named through a variable could be anything, so every path the command names is held to it
    if any(guarded(t) for t in targets) or (any(unresolved(t) for t in targets) and any(guarded(t) for t in path_tokens(command, base))):
        deny(reason, "BOUNDARY_BLOCK", p, command)
    allow()


if __name__ == "__main__":
    main()
