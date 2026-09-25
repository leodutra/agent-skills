#!/usr/bin/env python3
"""PreToolUse, Read|Glob|Grep|Bash: a reader sees its pair and nothing else. Other agents pass through."""
import os
import shlex

from _paths import (allow, binding, deny, glob_base, inside, payload, policy, project, read_targets, resolve, shell_base,
                    unresolved, write_targets)

ROLES = ("reader", "reader-alt")
FORBIDDEN = policy()["critic_blind"]["forbidden"]
REASON = "outside your working set"


def main():
    p = payload()
    if p.get("agent_type") not in ROLES:
        allow()
    root = project()
    pairs = os.path.join(root, ".gauntlet", "pairs")
    tool, ti, agent = p.get("tool_name"), p.get("tool_input", {}), p.get("agent_id")
    pair = binding(agent)
    home = os.path.join(pairs, pair) if pair else pairs

    if tool == "Bash":
        command = ti.get("command", "")
        if not pair:  # bound by a first command whose paths all lie in one pair, as a first Read binds (F15)
            base = shell_base(command, root)
            reals = read_targets(command, base) + ([base] if base != root else [])
            named = {os.path.relpath(r, pairs).split(os.sep)[0] for r in reals if inside(r, pairs) and r != pairs}
            if len(named) != 1 or not all(inside(r, os.path.join(pairs, *named)) for r in reals):
                deny(REASON, "BLIND_BLOCK", p, command)
            pair = binding(agent, named.pop())
            home = os.path.join(pairs, pair)
        # What it opens and what it writes, by the shell's rules (F39); a name the policy forbids anywhere at all
        if any(name in command for name in FORBIDDEN) or any(
                unresolved(t) or not inside(t, home) for t in read_targets(command, home) + write_targets(command, home)):
            deny(REASON, "BLIND_BLOCK", p, command)
        allow({**ti, "command": f"cd {shlex.quote(home)} && {command}"})

    target = ti.get("file_path") or ti.get("path") or "."
    if tool == "Glob":
        target = os.path.join(target, glob_base(ti.get("pattern", "")))
    real = resolve(target, root)
    if not inside(real, home) or real == pairs or any(name in real for name in FORBIDDEN):
        deny(REASON, "BLIND_BLOCK", p, target)
    if not pair:
        binding(agent, os.path.relpath(real, pairs).split(os.sep)[0])
    allow()


if __name__ == "__main__":
    main()
