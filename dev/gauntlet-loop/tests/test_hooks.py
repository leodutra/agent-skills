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
        self.denied(self.hook("Bash", {"command": "node <<'EOF'\nrequire('fs').readFileSync('../../private/secret')\nEOF"}))
        loop = """for s in a b; do node -e "import('./$s/index.js').then(m=>console.log(m.x))" 2>&1; done"""
        self.assertIn("updatedInput", self.hook("Bash", {"command": loop}))  # seen in a live run: a reader loops over both sides

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

    def test_shell_writes_are_denied_and_shell_reads_are_not(self):
        self.assertEqual(self.hook("Bash", {"command": "echo x > heldout/x.mjs"}, agent_type=None).get("permissionDecision"), "deny")
        self.assertEqual(self.hook("Bash", {"command": "rm -rf reference/"}, agent_type=None).get("permissionDecision"), "deny")
        self.assertEqual(self.hook("Bash", {"command": "node --test heldout/"}, agent_type=None), {})
        self.assertEqual(self.hook("Bash", {"command": "rm -rf docs/reference"}, agent_type=None), {})
        for command in ("rm -rf heldout", "cd heldout && rm x.mjs", "cd heldout && echo x > new.mjs"):  # a bare word is a path too
            self.assertEqual(self.hook("Bash", {"command": command}, agent_type=None).get("permissionDecision"), "deny", command)
        self.assertEqual(self.hook("Bash", {"command": "rm -rf src && echo heldout > note.txt"}, agent_type=None).get("permissionDecision"), "deny")  # coarse, by design
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

    def test_a_chained_controller_call_is_told_to_stand_alone(self):  # F12: seen in bytesize-2
        out = self.hook("Bash", {"command": "rmdir .gauntlet/staging/x; ls -la .gauntlet/; .claude/hooks/gauntlet/gauntletctl init 2>&1 | tail -2"})
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
                        "cd src && touch app.js", "tee ../outside.txt < heldout/x.mjs"):
            self.assertEqual(hook(command).get("permissionDecision"), "deny", command)
        for command in ("echo x > heldout/new.mjs", "mkdir -p .gauntlet/staging && cp heldout/x.mjs .gauntlet/staging/t.mjs",
                        "node --test heldout/ 2>&1", "cat src/secret.txt", "git clone https://example.com/a/b reference/b",
                        "python3 .claude/hooks/gauntlet/gauntletctl freeze https://example.com/a/b reference/b", "touch heldout/new.mjs",
                        "cd heldout && touch new.mjs"):
            self.assertEqual(hook(command), {}, command)
        self.assertEqual(hook("echo x > src/app.js", agent_type="editor"), {})  # other agents pass through


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
