#!/usr/bin/env python3
"""Assemble the prompt template with each example's slot fills from SKILL.md and count the words; fail above 270."""
import os
import re
import sys

LIMIT = 270
skill = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "SKILL.md")
with open(skill) as f:
    text = f.read()
template = re.search(r"```text\n(/goal .*?)```", text, re.S).group(1)
examples = re.findall(r"^\*\*(\w[\w ]*)\.\*\*.*?\n\n((?:- [A-Z]+: .*\n)+)", text, re.M)
prompts = {"template": template}
for name, fills in examples:
    slots = dict(re.findall(r"([A-Z]+): `([^`]*)`", fills))
    prompts[name] = re.sub(r"\[([A-Z]+)\]", lambda m: slots.get(m.group(1), m.group(0)), template)
    left = re.findall(r"\[[A-Z]+\]", prompts[name])
    if left:
        sys.exit(f"FAIL  {name}: unfilled {left}")
worst = 0
for name, prompt in prompts.items():
    n = len(prompt.split())
    worst = max(worst, n)
    print(f"{'FAIL' if n > LIMIT else 'ok'}  {n} words  {name}")
sys.exit(0 if len(examples) >= 2 and worst <= LIMIT else 1)
