#!/usr/bin/env python3
"""SubagentStart (with --start): register the agent; SubagentStop: attest its result. Both hand the payload and the hook key
to `gauntletctl attest`. Never blocks: exit 2 would keep the agent running."""
import subprocess
import sys

from _paths import controller, project

subprocess.run([sys.executable, controller(), "attest", *sys.argv[1:2], "--key-file", project() + "/.gauntlet/private/attest.key"],
               stdin=sys.stdin, cwd=project(), capture_output=True, timeout=30)
