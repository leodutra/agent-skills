#!/usr/bin/env python3
"""SubagentStart: hand the payload to `gauntletctl attest --start`. Never blocks: a hook's exit 2 would."""
import subprocess
import sys

from _paths import controller, project

subprocess.run([sys.executable, controller(), "attest", "--start", "--key-file", project() + "/.gauntlet/private/attest.key"],
               stdin=sys.stdin, cwd=project(), capture_output=True, timeout=30)
