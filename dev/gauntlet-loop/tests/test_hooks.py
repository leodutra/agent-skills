"""Deny hooks, run the way the harness runs them: payload on stdin, decision on stdout."""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(HERE, "..", "..", "..", "skills", "gauntlet-loop")


def run_hook(name, project, tool, tool_input, agent_type="reader", agent_id="a1", hooks=None):
    payload = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input,
               "agent_id": agent_id, "agent_type": agent_type, "cwd": project}
    out = subprocess.run([sys.executable, os.path.join(hooks or os.path.join(SKILL, "hooks"), name)], input=json.dumps(payload),
                         capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": project})
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)["hookSpecificOutput"] if out.stdout.strip() else {}


def events(project):
    path = os.path.join(project, ".gauntlet", "events.jsonl")
    return [json.loads(line) for line in pathlib.Path(path).read_text().splitlines()] if os.path.exists(path) else []


class Project(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self.tmp.name)
        for d in (".gauntlet/pairs/parse/a", ".gauntlet/pairs/format/a", ".gauntlet/private", "heldout", "src",
                  ".gauntlet/wt/parse/src", ".gauntlet/wt/parse/tests/required", ".gauntlet/wt/format/src"):
            os.makedirs(os.path.join(self.root, d))
        for f in (".gauntlet/pairs/parse/PROMPT.md", ".gauntlet/pairs/parse/a/index.js", ".gauntlet/state.json",
                  ".gauntlet/workbench.md", "heldout/x.mjs", "src/secret.txt"):
            pathlib.Path(self.root, f).write_text("x")

    def tearDown(self):
        self.tmp.cleanup()

    def path(self, rel):
        return os.path.join(self.root, rel)


class CriticBlind(Project):
    def hook(self, tool, tool_input, **kw):
        return run_hook("critic_blind.py", self.root, tool, tool_input, **kw)

    def denied(self, out):
        self.assertEqual(out.get("permissionDecision"), "deny")
        self.assertEqual(out.get("permissionDecisionReason"), "outside your working set")

    def test_allows_inside_the_pair_and_binds(self):
        self.assertEqual(self.hook("Read", {"file_path": self.path(".gauntlet/pairs/parse/PROMPT.md")}), {})
        self.denied(self.hook("Read", {"file_path": self.path(".gauntlet/pairs/format/a")}))  # another piece's pair

    def test_denies_the_workbench_and_logs_the_block(self):
        self.denied(self.hook("Read", {"file_path": self.path(".gauntlet/workbench.md")}))
        (event,) = events(self.root)
        self.assertEqual((event["seq"], event["event"], event["kind"], event["source"], event["agent_type"]),
                         (1, "BLIND_BLOCK", "fact", "hook", "reader"))

    def test_denies_grep_and_glob_outside(self):
        self.denied(self.hook("Grep", {"pattern": "x", "path": self.path("src")}))
        self.denied(self.hook("Grep", {"pattern": "x"}))  # no path means the project root
        self.denied(self.hook("Glob", {"pattern": "../../**/*.json", "path": self.path(".gauntlet/pairs/parse")}))
        self.denied(self.hook("Glob", {"pattern": "*", "path": self.path(".gauntlet/pairs")}))  # the pairs root itself

    def test_denies_escapes_by_dotdot_and_symlink(self):
        self.denied(self.hook("Read", {"file_path": self.path(".gauntlet/pairs/parse/../../state.json")}))
        os.symlink(self.path("src"), self.path(".gauntlet/pairs/parse/link"))
        self.denied(self.hook("Read", {"file_path": self.path(".gauntlet/pairs/parse/link/secret.txt")}))

    def test_shell_is_rewritten_into_the_pair_and_string_matched(self):
        self.denied(self.hook("Bash", {"command": "ls"}))  # nothing opened yet: no pair to run in
        self.hook("Read", {"file_path": self.path(".gauntlet/pairs/parse/PROMPT.md")})
        out = self.hook("Bash", {"command": "node a/index.js 2>/dev/null"})
        self.assertEqual(out["updatedInput"]["command"],
                         f"cd {self.path('.gauntlet/pairs/parse')} && node a/index.js 2>/dev/null")
        for command in ("cat ../../state.json", "cat ../format/a/x", "cat /etc/passwd", "cat $HOME/.netrc",
                        "grep -r x heldout/", "cat CLAUDE.md", "cat $(echo /etc/passwd)", "cat ${HOME}/x"):
            self.denied(self.hook("Bash", {"command": command}))
        driver = "node --input-type=module <<'EOF'\nfor (const c of ['2h']) { const m = await import(`./a/index.js`); console.log(`${c} -> ${m.x}`) }\nEOF"
        self.assertIn("updatedInput", self.hook("Bash", {"command": driver}))  # seen live: a reader's heredoc test driver
        from _util import installer  # noqa: F401  (the hooks' shared helpers, loaded the way the tests load the skill)
        import importlib.util
        spec = importlib.util.spec_from_file_location("_paths", os.path.join(SKILL, "hooks", "_paths.py"))
        paths = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(paths)
        self.assertEqual(paths.write_targets(driver, self.root), [])  # F39: a template literal in a heredoc body writes nothing
        self.denied(self.hook("Bash", {"command": "node <<'EOF'\nrequire('fs').readFileSync('../../private/secret')\nEOF"}))
        loop = """for s in a b; do node -e "import('./$s/index.js').then(m=>console.log(m.x))" 2>&1; done"""
        self.assertIn("updatedInput", self.hook("Bash", {"command": loop}))  # seen in a live run: a reader loops over both sides

    def test_a_first_shell_command_inside_one_pair_binds_the_reader(self):  # F15: both readers lost a turn in bytesize-3
        pair = self.path(".gauntlet/pairs/parse")
        out = self.hook("Bash", {"command": f"cat {pair}/PAIR_ID && echo ---- && cat {pair}/PROMPT.md"})
        self.assertEqual(out["updatedInput"]["command"], f"cd {pair} && cat {pair}/PAIR_ID && echo ---- && cat {pair}/PROMPT.md")
        self.denied(self.hook("Read", {"file_path": self.path(".gauntlet/pairs/format/a")}))  # bound to parse now
        out = self.hook("Bash", {"command": f"cd {pair} && cat PAIR_ID"}, agent_id="a2")
        self.assertIn("updatedInput", out)
        for command in ("cat PAIR_ID", f"cat {pair}/PAIR_ID {self.path('.gauntlet/pairs/format/a')}", f"cat {pair}/../../state.json"):
            self.denied(self.hook("Bash", {"command": command}, agent_id="a3"))  # nothing to bind to, two pairs, an escape

    def test_a_variable_the_command_sets_is_judged_where_it_points(self):  # F31: nine false blocks in units-2
        pair = self.path(".gauntlet/pairs/parse")
        for command in (f"D={pair}; cat $D/PROMPT.md; cat $D/a/index.js",
                        f"cd {pair} && for f in a/index.js PROMPT.md; do echo \"== $f\"; cat $f; done",
                        f'cd {pair} && for f in a/*; do cat "$f"; done', f"D={pair}; for f in $D/a/*; do echo \"-- $f\"; cat $f; done",
                        f"D={pair}; cat $D/adapter.mjs; for f in $D/a/*; do echo \"-- $f\"; cat $f; done; ls $D/a",
                        f"for s in a b; do f={pair}/$s/x.md; wc -w < $f; done"):  # F39: a value that names the loop's variable
            self.assertIn("updatedInput", self.hook("Bash", {"command": command}), command)
        for command in (f"D={pair}/../..; cat $D/state.json", "cat $UNKNOWN/x", f"cd {pair} && for f in ../../state.json; do cat $f; done"):
            self.denied(self.hook("Bash", {"command": command}))

    def test_text_tools_on_the_pair_pass(self):  # F39: 28 false blocks in units-docs, every one a critic reading its own pair
        pair = self.path(".gauntlet/pairs/parse")
        self.hook("Read", {"file_path": f"{pair}/PROMPT.md"})
        fence = "`" * 3
        for command in (
                """echo "--- word totals ---" && wc -w a/x.md b/x.md && sed -n '120p' a/x.md | grep -o 'range: "[9]*' | tr -d 'range: "' | awk '{print length($0)}'""",
                """python3 -c "print('A:195 1e40/1024**5 =', repr(1e40/1024**5)); print(1048575 /1024**2)\"""",
                "grep -c $'\\xef\\xbd\\x9c' b/x.md; grep -n 'B/KB\\|`pb`' b/x.md",
                "awk '/^" + fence + "js/{f=1;next}/^" + fence + "/{f=0}f && /^(parse|format)\\(/ && !/\\/\\/ (throws)/{print \"A:\"NR\": \"$0}' a/x.md; echo \"A-done\"",
                "grep -n '^parse(' a/x.md | grep -v '// ->' | grep -v -c '//'",
                f"cd {pair} && for s in a b; do printf \"%s total=%s prose=%s\\n\" $s \"$(wc -w < $s/x.md)\" \"$(awk '/^{fence}/{{f=!f;next}} !f' $s/x.md | wc -w)\"; done",
                f"cd {pair} && cat > strike.txt <<'EOF'\n# struck words per span\nA 3 2 / 7\nEOF",
                "awk '{s[$1]+=$3} END{printf \"A struck %d / 789\\n\", s[\"A\"]}' <<'EOF'\nA 3 2\nA 7-9 18 / x\nEOF",
                'echo "A struck: $((2+18+4)) / 789"',
                "grep -n -A 3 -E '^(size|duration)' a/x.md",
                'grep -nE "import|require" a/x.md; grep -niE "throw|error" a/x.md; echo "hits=$?"'):
            self.assertIn("updatedInput", self.hook("Bash", {"command": command}), command)

    def test_an_escape_through_a_text_tool_is_still_denied(self):  # F39: what the parser knows it also holds
        self.hook("Read", {"file_path": self.path(".gauntlet/pairs/parse/PROMPT.md")})
        secret = "../../../src/secret.txt"
        for command in (f"echo `cat {secret}`", f'echo "$(cat {secret})"', f"grep -f {secret} a/x", f"awk -f {secret} a/x",
                        "python3 -c \"print(open('/etc/passwd').read())\"", "grep -r x /", "find / -name x", f"cat < {secret}",
                        "echo hi > ../../wt/parse/src/x.js", f"sh <<'EOF'\ncat {secret}\nEOF", f"cat <<EOF\n$(cat {secret})\nEOF",
                        f"grep -e x {secret}", f"sed -n 1p {secret}", "ls ../format", "cat $(ls ../format)"):
            self.denied(self.hook("Bash", {"command": command}))

    def test_other_agents_pass_through(self):
        self.assertEqual(self.hook("Read", {"file_path": self.path("src/secret.txt")}, agent_type="editor"), {})
        self.assertEqual(self.hook("Read", {"file_path": self.path("src/secret.txt")}, agent_type=None), {})


class BuilderBoundary(Project):
    def hook(self, tool, tool_input, **kw):
        return run_hook("builder_boundary.py", self.root, tool, tool_input, **{"agent_type": "editor", **kw})

    def denied(self, out, rule):
        self.assertEqual(out.get("permissionDecision"), "deny")
        self.assertIn(rule, out["permissionDecisionReason"])
        self.assertIn("BLOCKED:", out["permissionDecisionReason"])

    def test_edits_stay_inside_the_bound_worktree(self):
        self.assertEqual(self.hook("Write", {"file_path": self.path(".gauntlet/wt/parse/src/parse.ts")}), {})
        self.assertEqual(self.hook("Edit", {"file_path": self.path(".gauntlet/wt/parse/src/parse.ts")}), {})
        self.denied(self.hook("Edit", {"file_path": self.path(".gauntlet/wt/format/src/format.ts")}), "outside")
        self.denied(self.hook("Write", {"file_path": self.path("src/app.js")}), "outside")
        self.assertEqual(events(self.root)[0]["event"], "BOUNDARY_BLOCK")

    def test_floors_secrets_and_migrations_inside_the_worktree(self):
        for rel, rule in ((".gauntlet/wt/parse/tests/required/a.test.ts", "tests/required"),
                          (".gauntlet/wt/parse/migrations/001.sql", "migrations"),
                          (".gauntlet/wt/parse/.env.local", "secrets"),
                          (".gauntlet/wt/parse/.github/workflows/ci.yml", ".github/workflows")):
            self.denied(self.hook("Write", {"file_path": self.path(rel)}), rule)
        self.assertEqual(self.hook("Write", {"file_path": self.path(".gauntlet/wt/parse/docs/reference/api.md")}), {})

    def test_held_out_material_and_run_state_are_unreadable(self):
        self.denied(self.hook("Read", {"file_path": self.path("heldout/x.mjs")}), "held-out")
        self.denied(self.hook("Bash", {"command": "cat heldout/x.mjs"}), "held-out")
        self.denied(self.hook("Read", {"file_path": self.path(".gauntlet/workbench.md")}), "run state")
        self.assertEqual(self.hook("Read", {"file_path": self.path("src/secret.txt")}), {})
        for command in ("git show HEAD:heldout/x.mjs", "git cat-file -p main:heldout/x.mjs"):  # A6: a revision path
            self.denied(self.hook("Bash", {"command": command}), "held-out")
        self.assertEqual(self.hook("Bash", {"command": "git show HEAD:src/app.js && curl -s https://example.com/a:b"}), {})

    def test_shell_commands(self):
        for command, rule in (("git push origin main", "push"), ("npm publish", "publish"), ("npm install left-pad", "install"),
                              ("npx prisma migrate deploy", "deploy"), ("rm -rf ../../../src", "outside")):
            self.denied(self.hook("Bash", {"command": command}), rule)
        self.hook("Write", {"file_path": self.path(".gauntlet/wt/parse/src/parse.ts")})
        self.assertEqual(self.hook("Bash", {"command": "cd .gauntlet/wt/parse && npm test && rm -rf dist/"}), {})
        self.denied(self.hook("Bash", {"command": "cd .gauntlet/wt/parse && rm -rf ../format/src"}), "run state")  # another piece's worktree

    def test_a_greater_than_inside_a_quoted_script_is_not_a_redirect(self):  # A2: denied live in bytesize, 2026-09-19
        self.hook("Write", {"file_path": self.path(".gauntlet/wt/parse/src/parse.ts")})
        probe = ("node --input-type=module -e \"\nimport { parse } from '" + self.path(".gauntlet/wt/parse/src/index.js") + "';\n"
                 "for (const h of ['1'.repeat(1e6), 'kb']) console.log(JSON.stringify(typeof h === 'string' && h.length > 50 ? "
                 "h.slice(0, 12) + '...' : String(h)), '->', parse(h));\n\"")
        self.assertEqual(self.hook("Bash", {"command": probe}), {})
        self.assertEqual(self.hook("Bash", {"command": "echo \"a > b\" && node -e 'console.log(1 > 0)'"}), {})
        self.denied(self.hook("Bash", {"command": "node -e 'x' > ../../../src/out.txt"}), "outside")  # a real redirect still is
        heredoc = "cat > .gauntlet/wt/parse/src/x.js <<'EOF'\nimport a from './a.js'\nconsole.log(a > 1)\nEOF"
        self.assertEqual(self.hook("Bash", {"command": heredoc}), {})  # a here-document body is data, not shell
        self.denied(self.hook("Bash", {"command": "cat > src/x.js <<'EOF'\n1\nEOF"}), "outside")

    def test_the_harness_scratchpad_is_writable_and_nothing_else_outside(self):  # F24: bytes parked over check.mjs
        self.hook("Write", {"file_path": self.path(".gauntlet/wt/parse/src/parse.ts")})
        scratch = "/tmp/claude-1000/-home-leo-Work-units/860117bb/scratchpad/check.mjs"
        self.assertEqual(self.hook("Write", {"file_path": scratch}), {})
        self.assertEqual(self.hook("Bash", {"command": f"mkdir -p {scratch.rsplit('/', 1)[0]} && cat > {scratch} <<'EOF'\n1\nEOF"}), {})
        for command in ("S=/tmp/claude-1000/-home-leo-Work-units-2/c2f4/scratchpad; mkdir -p $S/cjs && cat > $S/cjs/index.js <<'EOF'\n1\nEOF",
                        "cat > $TMPDIR/hostile.mjs <<'EOF'\n1\nEOF", "echo x > /tmp/claude-1000/elsewhere/check.mjs"):
            self.assertEqual(self.hook("Bash", {"command": command}), {}, command)  # F31, F32: the harness's temp dir, named or not
        self.denied(self.hook("Write", {"file_path": self.path("src/inside-the-project.js")}), "outside")  # never the project itself
        out = self.hook("Write", {"file_path": os.path.expanduser("~/gauntlet-elsewhere/check.mjs")})
        self.denied(out, "outside")
        self.assertIn("inside", out["permissionDecisionReason"])  # keep it inside the worktree; BLOCKED only for real need
        self.assertNotIn("Do not retry", out["permissionDecisionReason"])

    def test_a_script_argument_is_not_a_write_target(self):  # F14, the builder side
        self.hook("Write", {"file_path": self.path(".gauntlet/wt/parse/src/parse.ts")})
        self.assertEqual(self.hook("Bash", {"command": "cd .gauntlet/wt/parse && sed -e 's/a/b/' src/parse.ts > src/out.ts 2>&1"}), {})
        self.denied(self.hook("Bash", {"command": "cd .gauntlet/wt/parse && sed -e 's/a/b/' src/parse.ts > ../format/x.ts"}), "run state")
        self.denied(self.hook("Bash", {"command": "f=../../src; cp .gauntlet/wt/parse/src/parse.ts $f/"}), "outside")
        self.assertEqual(self.hook("Bash", {"command": "cd .gauntlet/wt/parse && find . -name '*.tmp' -delete"}), {})
        self.denied(self.hook("Bash", {"command": "cd .gauntlet/wt/parse && find ../../../src -name x -delete"}), "outside")

    def test_other_agents_pass_through(self):
        self.assertEqual(self.hook("Write", {"file_path": self.path("src/app.js")}, agent_type="author"), {})


class ProtectFloors(Project):
    def hook(self, tool, tool_input, **kw):
        return run_hook("protect_floors.py", self.root, tool, tool_input, **kw)

    def test_everyone_but_the_author_is_denied(self):
        for agent_type in ("editor", "reader", None):  # None is the lead
            out = self.hook("Edit", {"file_path": self.path("heldout/x.mjs")}, agent_type=agent_type)
            self.assertEqual(out.get("permissionDecision"), "deny")
        self.assertEqual(self.hook("Write", {"file_path": self.path("heldout/new.mjs")}, agent_type="author"), {})
        self.assertEqual(self.hook("Edit", {"file_path": self.path(".gauntlet/wt/parse/tests/required/a.ts")},
                                   agent_type=None).get("permissionDecision"), "deny")

    def test_the_author_is_exempt_in_round_zero_only(self):  # FR-3.3, A3
        state = pathlib.Path(self.root, ".gauntlet/state.json")
        state.write_text(json.dumps({"run": {"plan_committed": False}}))
        self.assertEqual(self.hook("Write", {"file_path": self.path("heldout/new.mjs")}, agent_type="author"), {})
        state.write_text(json.dumps({"run": {"plan_committed": True}}))
        out = self.hook("Write", {"file_path": self.path("heldout/new.mjs")}, agent_type="author")
        self.assertEqual(out.get("permissionDecision"), "deny")
        self.assertIn("floor add", out["permissionDecisionReason"])
        self.assertEqual(self.hook("Bash", {"command": "python3 .claude/hooks/gauntlet/gauntletctl floor add h --cmd true --from .gauntlet/staging/t.mjs --to heldout/t.mjs"}, agent_type=None), {})

    def test_the_controller_alone_on_its_line_passes(self):  # F13: bytesize-3's freeze-verify was denied, 2026-09-23
        verify = '.claude/hooks/gauntlet/gauntletctl freeze-verify reference/bytes --cmd "npm install --no-audit" --cmd "npm test"'
        for command in (verify, "python3 " + verify):
            self.assertEqual(self.hook("Bash", {"command": command}, agent_type=None), {}, command)
        self.assertEqual(self.hook("Bash", {"command": verify + " 2>&1 | tail -30; echo done"}, agent_type=None), {})  # D5: chained, harmless
        out = self.hook("Bash", {"command": verify + " | tee heldout/log.txt"}, agent_type=None)
        self.assertEqual(out.get("permissionDecision"), "deny")  # chained and writing a floor tree: checked, and told why
        self.assertIn("alone on its line", out["permissionDecisionReason"])

    def test_shell_writes_are_denied_and_shell_reads_are_not(self):
        self.assertEqual(self.hook("Bash", {"command": "echo x > heldout/x.mjs"}, agent_type=None).get("permissionDecision"), "deny")
        self.assertEqual(self.hook("Bash", {"command": "rm -rf reference/"}, agent_type=None).get("permissionDecision"), "deny")
        self.assertEqual(self.hook("Bash", {"command": "node --test heldout/"}, agent_type=None), {})
        self.assertEqual(self.hook("Bash", {"command": "rm -rf docs/reference"}, agent_type=None), {})
        for command in ("rm -rf heldout", "cd heldout && rm x.mjs", "cd heldout && echo x > new.mjs"):  # a bare word is a path too
            self.assertEqual(self.hook("Bash", {"command": command}, agent_type=None).get("permissionDecision"), "deny", command)
        self.assertEqual(self.hook("Bash", {"command": "rm -rf src && echo heldout > note.txt"}, agent_type=None), {})  # D5: what is written, not every word
        for command in ("f=heldout/x.mjs; echo x > $f", "chmod 777 heldout/x.mjs", "sed -i -e 's/a/b/' heldout/x.mjs"):
            self.assertEqual(self.hook("Bash", {"command": command}, agent_type=None).get("permissionDecision"), "deny", command)
        self.assertEqual(self.hook("Bash", {"command": "rm -rf src dist a=b 2>&1"}, agent_type=None), {})
        for command in ("cat > heldout/x.mjs <<'EOF'\nexport default 1\nEOF", "echo 'x' >> heldout/x.mjs"):  # A2: still writes
            self.assertEqual(self.hook("Bash", {"command": command}, agent_type=None).get("permissionDecision"), "deny", command)
        self.assertEqual(self.hook("Bash", {"command": "node -e \"console.log(2 > 1)\" heldout/x.mjs"}, agent_type=None), {})


class ControllerOnly(Project):
    def hook(self, tool, tool_input, **kw):
        return run_hook("controller_only.py", self.root, tool, tool_input, **{"agent_type": None, **kw})

    def test_state_log_private_storage_and_tooling_are_the_controllers(self):  # FR-17.3
        for rel in (".gauntlet/state.json", ".gauntlet/events.jsonl", ".gauntlet/private/mapping/x.json", ".gauntlet/workbench.md",
                    ".gauntlet/verdicts/parse-r1-1.md", ".claude/hooks/gauntlet/gauntletctl", ".claude/hooks/gauntlet/policy/v1.json",
                    ".claude/agents/reader.md"):
            self.assertEqual(self.hook("Write", {"file_path": self.path(rel)}).get("permissionDecision"), "deny", rel)
        for rel in (".gauntlet/staging/t.mjs", ".gauntlet/wt/parse/src/a.js", "src/app.js", ".claude/agents/my-own.md"):
            self.assertEqual(self.hook("Write", {"file_path": self.path(rel)}), {}, rel)

    def test_private_storage_is_unreadable_by_every_tool(self):  # F9: a hook, not a permission deny, so the sandbox masks nothing
        private = self.path(".gauntlet/private/mapping/x.json")
        for agent_type in (None, "author", "editor", "editor-fast"):
            self.assertEqual(self.hook("Read", {"file_path": private}, agent_type=agent_type).get("permissionDecision"), "deny", agent_type)
        for tool, tool_input in (("Grep", {"pattern": "a", "path": self.path(".gauntlet/private")}),
                                 ("Glob", {"pattern": ".gauntlet/private/**", "path": self.root}),
                                 ("Bash", {"command": "cat .gauntlet/private/secret"})):
            self.assertEqual(self.hook(tool, tool_input).get("permissionDecision"), "deny", tool)
        for tool, tool_input in (("Read", {"file_path": self.path(".gauntlet/workbench.md")}),
                                 ("Read", {"file_path": self.path(".gauntlet/state.json")}),
                                 ("Bash", {"command": "python3 .claude/hooks/gauntlet/gauntletctl pair parse"})):
            self.assertEqual(self.hook(tool, tool_input), {}, tool_input)

    def test_quoted_arguments_do_not_make_the_controller_chained(self):  # F21: the units lead's freeze-verify, 2026-09-24
        verify = ('.claude/hooks/gauntlet/gauntletctl freeze-verify reference/bytes'
                  ' --cmd \'npm install --no-audit --cache "$TMPDIR/npm-cache"\''
                  ' --cmd \'node ../../bench/hostile.mjs . ; echo "hostile exit $?"\''
                  ' --cmd "node run.mjs a | tee out.txt"')
        for hook in ("controller_only.py", "protect_floors.py"):
            self.assertEqual(run_hook(hook, self.root, "Bash", {"command": verify}, agent_type=None), {}, hook)
        for command in (".claude/hooks/gauntlet/gauntletctl status; rm .gauntlet/state.json",
                        ".claude/hooks/gauntlet/gauntletctl status | tee .gauntlet/x",
                        '.claude/hooks/gauntlet/gauntletctl pair parse --ours "$(rm -rf .gauntlet/state.json)"'):
            self.assertEqual(self.hook("Bash", {"command": command}).get("permissionDecision"), "deny", command)

    def test_one_matcher_still_sees_indirect_and_permission_writes(self):  # D5: write_targets for every write rule
        for command in ("f=.gauntlet/state.json; echo x > $f", "chmod 000 .gauntlet/state.json", "sed -i s/a/b/ .claude/agents/reader.md",
                        "sed -i.bak -e 1d .gauntlet/events.jsonl"):
            self.assertEqual(self.hook("Bash", {"command": command}).get("permissionDecision"), "deny", command)
        self.assertEqual(self.hook("Bash", {"command": "echo .gauntlet/state.json > notes.txt"}), {})  # a word, not a target
        for command in ("find .gauntlet -name '*.json' -delete", "find .gauntlet -name x | xargs rm", "sudo rm .gauntlet/state.json",
                        "A=1 rm .gauntlet/state.json", "cp -t .gauntlet/ notes.txt", "mv --target-directory=.gauntlet notes.txt"):
            self.assertEqual(self.hook("Bash", {"command": command}).get("permissionDecision"), "deny", command)  # writes a verb hides
        self.assertEqual(self.hook("Bash", {"command": "find src -name '*.tmp' | xargs rm -f"}), {})

    def test_committing_a_pieces_worktree_is_allowed(self):  # F26: the units lead could not stage bytes for its merge
        wt = self.path(".gauntlet/wt/parse")
        for command in (f'cd {wt} && git status --short && git add src/bytes.js && git commit -q -m "feat: bytes"',
                        f"git -C {wt} add -A", "cd .gauntlet/wt/parse && git add ."):
            self.assertEqual(self.hook("Bash", {"command": command}), {}, command)
        for command in (f"cd {wt} && git add -f ../../private/secret", "git add .gauntlet/workbench.md",
                        f"cd {wt} && git add ../../verdicts/x.md"):
            self.assertEqual(self.hook("Bash", {"command": command}).get("permissionDecision"), "deny", command)

    def test_a_chained_controller_call_is_told_to_stand_alone(self):  # F12: seen in bytesize-2
        harmless = "rmdir .gauntlet/staging/x; ls -la .gauntlet/; .claude/hooks/gauntlet/gauntletctl init 2>&1 | tail -2"
        self.assertEqual(self.hook("Bash", {"command": harmless}), {})  # D5: it writes nothing guarded
        out = self.hook("Bash", {"command": "rmdir .gauntlet/staging/x; .claude/hooks/gauntlet/gauntletctl init | tee .gauntlet/state.json"})
        self.assertEqual(out.get("permissionDecision"), "deny")
        self.assertIn("alone on its line", out["permissionDecisionReason"])

    def test_shell(self):
        for command in ("echo '{}' >> .gauntlet/events.jsonl", "rm .gauntlet/state.json", "git add -f .gauntlet/private",
                        "git add .gauntlet/workbench.md", "python3 .claude/hooks/gauntlet/gauntletctl attest < payload.json",
                        "sed -i s/opus/fable/ .claude/agents/reader-alt.md", "git add --force .",
                        "python3 .claude/hooks/gauntlet/gauntletctl status && rm .gauntlet/state.json"):
            self.assertEqual(self.hook("Bash", {"command": command}).get("permissionDecision"), "deny", command)
        self.assertEqual(self.hook("Bash", {"command": "cat > .gauntlet/pairs/parse/_probe.mjs <<'X'\n1\nX"}, agent_type="reader"), {})
        for command in ("find .gauntlet -maxdepth 3 2>&1", "cat .gauntlet/workbench.md 2>/dev/null",
                        "node -e \"fs.readFileSync('.gauntlet/workbench.md'); [1].map(x=>x)\"",
                        "python3 .claude/hooks/gauntlet/gauntletctl commit --plan", "python3 .claude/hooks/gauntlet/gauntletctl status",
                        "git add src/app.js", "cat .gauntlet/workbench.md", "git commit -m wip"):
            self.assertEqual(self.hook("Bash", {"command": command}), {}, command)


class AuthorScope(Project):
    def test_author_writes_check_files_only(self):
        hook = lambda path, **kw: run_hook("author_scope.py", self.root, "Write", {"file_path": self.path(path)}, **kw)
        self.assertEqual(hook("heldout/new.mjs", agent_type="author"), {})
        self.assertEqual(hook(".gauntlet/staging/t.mjs", agent_type="author"), {})
        self.assertEqual(hook("src/app.js", agent_type="author").get("permissionDecision"), "deny")
        self.assertEqual(hook("src/app.js", agent_type="editor"), {})

    def test_an_authors_shell_writes_are_held_to_the_same_trees(self):
        hook = lambda command, **kw: run_hook("author_scope.py", self.root, "Bash", {"command": command}, **{"agent_type": "author", **kw})
        for command in ("echo x > src/app.js", "cp heldout/x.mjs src/x.mjs", "rm -rf src", "git clone https://example.com/a/b src/b",
                        "cd src && touch app.js", "tee ~/gauntlet-outside.txt < heldout/x.mjs"):
            self.assertEqual(hook(command).get("permissionDecision"), "deny", command)
        for command in ("echo x > heldout/new.mjs", "mkdir -p .gauntlet/staging && cp heldout/x.mjs .gauntlet/staging/t.mjs",
                        "node --test heldout/ 2>&1", "cat src/secret.txt", "git clone https://example.com/a/b reference/b",
                        "python3 .claude/hooks/gauntlet/gauntletctl freeze https://example.com/a/b reference/b", "touch heldout/new.mjs",
                        "cd heldout && touch new.mjs"):
            self.assertEqual(hook(command), {}, command)
        self.assertEqual(hook("echo x > src/app.js", agent_type="editor"), {})  # other agents pass through

    def test_the_author_may_use_the_harness_scratchpad(self):  # F24: the units author, twice
        scratch = "/tmp/claude-1000/-home-leo-Work-units/860117bb/scratchpad/impl/src/index.js"
        self.assertEqual(run_hook("author_scope.py", self.root, "Write", {"file_path": scratch}, agent_type="author"), {})
        self.assertEqual(run_hook("author_scope.py", self.root, "Bash", {"command": f"echo x > {scratch}"}, agent_type="author"), {})

    def test_only_what_a_command_writes_must_stay_inside(self):  # F14: six author commands denied in bytesize-3
        hook = lambda command: run_hook("author_scope.py", self.root, "Bash", {"command": command}, agent_type="author")
        for command in ("""sed -e "60s/decimalPlaces: 4 }/decimalPlaces: 4, unit: 'kb' }/" heldout/x.mjs > .gauntlet/staging/x.mjs && diff heldout/x.mjs .gauntlet/staging/x.mjs""",
                        "sed -e 's/^var b = require(.b.);$/var b = 1;/' src/secret.txt > reference/anon/Readme.md && cp src/secret.txt heldout/x.mjs reference/anon/",
                        "mkdir -p reference/anon 2>/dev/null && cat src/secret.txt 2>&1 > reference/anon/a.js"):
            self.assertEqual(hook(command), {}, command)
        self.assertEqual(hook("A=reference/anon && mkdir -p $A/test"), {})  # F31: a variable it sets is judged where it points
        scratch = "/tmp/claude-1000/-home-leo-Work-units-2/c2f4/scratchpad"
        self.assertEqual(hook(f"S={scratch}; mkdir -p $S/cjs && cd $S/cjs && cat > index.js <<'EOF'\n1\nEOF"), {})  # a cd mid-chain moves the writes
        self.assertEqual(hook("mkdir -p heldout/x && cd src && touch app.js").get("permissionDecision"), "deny")
        for command in ("mkdir -p $UNSET/test", "A=src && mkdir -p $A/x", "echo x > $(pwd)/../out", "sed -i 's/a/b/' src/secret.txt",
                        "cp heldout/x.mjs src/", "mv reference/x src/x", "rm -f heldout/x.mjs src/secret.txt"):
            self.assertEqual(hook(command).get("permissionDecision"), "deny", command)


class PolicyDriven(Project):
    """Phase 9h: no hook carries a path list of its own; each reads the pinned policy installed beside it."""

    def hooks_with(self, edit):
        dest = os.path.join(tempfile.mkdtemp(dir=self.root), "hooks")
        shutil.copytree(os.path.join(SKILL, "hooks"), dest, ignore=shutil.ignore_patterns("__pycache__"))
        policy = json.loads(pathlib.Path(SKILL, "policy", "v1.json").read_text())
        edit(policy)
        os.makedirs(os.path.join(dest, "policy"))
        pathlib.Path(dest, "policy", "v1.json").write_text(json.dumps(policy))
        return dest

    def test_critic_blind_reads_its_forbidden_names_from_the_policy(self):
        target = {"file_path": self.path(".gauntlet/pairs/parse/a/index.js")}
        self.assertEqual(run_hook("critic_blind.py", self.root, "Read", target), {})
        hooks = self.hooks_with(lambda p: p["critic_blind"]["forbidden"].append("index.js"))
        self.assertEqual(run_hook("critic_blind.py", self.root, "Read", target, hooks=hooks).get("permissionDecision"), "deny")

    def test_author_scope_reads_its_trees_from_the_policy(self):
        target = {"file_path": self.path("fixtures/case.json")}
        self.assertEqual(run_hook("author_scope.py", self.root, "Write", target, agent_type="author").get("permissionDecision"), "deny")
        hooks = self.hooks_with(lambda p: p["floor_trees"].append("fixtures"))
        self.assertEqual(run_hook("author_scope.py", self.root, "Write", target, agent_type="author", hooks=hooks), {})
        hooks2 = self.hooks_with(lambda p: p["author_scope"].update(beyond_floor_trees=[]))
        staged = {"file_path": self.path(".gauntlet/staging/t.mjs")}
        self.assertEqual(run_hook("author_scope.py", self.root, "Write", staged, agent_type="author", hooks=hooks2).get("permissionDecision"), "deny")

    def test_controller_only_reads_what_is_protected_and_what_is_open_from_the_policy(self):
        scratch, mine = {"file_path": self.path(".gauntlet/scratch/x")}, {"file_path": self.path(".claude/agents/my-own.md")}
        self.assertEqual(run_hook("controller_only.py", self.root, "Write", scratch, agent_type=None).get("permissionDecision"), "deny")
        hooks = self.hooks_with(lambda p: (p["controller_only"]["open"].append(".gauntlet/scratch"),
                                           p["controller_only"]["files"].append(".claude/agents/my-own.md")))
        self.assertEqual(run_hook("controller_only.py", self.root, "Write", scratch, agent_type=None, hooks=hooks), {})
        self.assertEqual(run_hook("controller_only.py", self.root, "Write", mine, agent_type=None, hooks=hooks).get("permissionDecision"), "deny")


class LogBlock(Project):
    def ctl(self, *argv):
        return subprocess.run([sys.executable, os.path.join(SKILL, "bin", "gauntletctl"), *argv], capture_output=True,
                              text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": self.root})

    def test_takes_block_events_only(self):
        self.assertEqual(self.ctl("log-block", "BOUNDARY_BLOCK", '{"agent_id": "a"}').returncode, 0)
        self.assertEqual(self.ctl("log-block", "CONFIRMATION_WIN", '{"piece": "parse"}').returncode, 2)
        self.assertEqual(self.ctl("log-block", "BLIND_BLOCK", "not json").returncode, 2)
        self.assertEqual([e["seq"] for e in events(self.root)], [1])


if __name__ == "__main__":
    unittest.main()
