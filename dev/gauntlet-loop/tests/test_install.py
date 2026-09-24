"""The installer: idempotent, manifest verifies, an edited hook fails verification."""
import filecmp
import importlib.util
import json
import os
import pathlib
import shutil
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(HERE, "..", "..", "..", "skills", "gauntlet-loop")
spec = importlib.util.spec_from_file_location("claude_code", os.path.join(SKILL, "install", "claude_code.py"))
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class Install(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = os.path.realpath(self.tmp.name)
        os.makedirs(os.path.join(self.repo, ".claude"))
        pathlib.Path(self.repo, ".claude", "settings.json").write_text(json.dumps(
            {"permissions": {"allow": ["Bash(npm test)"]}, "hooks": {"PreToolUse": [
                {"matcher": "Bash", "hooks": [{"type": "command", "command": "their-own-hook"}]}]}}))

    def tearDown(self):
        self.tmp.cleanup()

    def test_second_run_changes_nothing_and_keeps_what_was_there(self):
        installer.install(self.repo)
        first = os.path.join(self.tmp.name + "-first")
        shutil.copytree(self.repo, first)
        self.addCleanup(shutil.rmtree, first)
        installer.install(self.repo)
        diff = filecmp.dircmp(first, self.repo)
        self.assertEqual((diff.left_only, diff.right_only, diff.diff_files), ([], [], []))
        settings = json.loads(pathlib.Path(self.repo, ".claude", "settings.json").read_text())
        self.assertEqual(settings["permissions"]["allow"][0], "Bash(npm test)")  # theirs kept, ours added after
        # F9: a permission deny on the controller's own files becomes a sandbox mask the sandboxed controller cannot read through
        self.assertEqual([d for d in settings["permissions"]["deny"] if ".gauntlet" in d], [])
        self.assertIn("Read(**/.env*)", settings["permissions"]["deny"])
        guarded = [g["matcher"] for g in settings["hooks"]["PreToolUse"] for h in g["hooks"] if "controller_only.py" in str(h.get("args"))]
        self.assertEqual(guarded, ["Read|Glob|Grep|Edit|Write|Bash"])
        self.assertNotIn("enabled", settings["sandbox"])  # the sandbox switch is the operator's
        self.assertNotIn("excludedCommands", settings["sandbox"])
        commands = [h.get("command") for g in settings["hooks"]["PreToolUse"] for h in g["hooks"]]
        self.assertIn("their-own-hook", commands)
        self.assertEqual(commands.count("python3"), len(installer.HOOKS["PreToolUse"]))
        shell = [h["args"][0].split("/")[-1] for g in settings["hooks"]["PreToolUse"] if "Bash" in g["matcher"] for h in g["hooks"] if h.get("args")]
        self.assertIn("author_scope.py", shell)  # an author's shell writes are checked, not only its file tools
        self.assertEqual([g["matcher"] for g in settings["hooks"]["SubagentStop"]], ["reader|reader-alt|editor|editor-fast|author"])
        start = [h["args"] for g in settings["hooks"]["SubagentStart"] for h in g["hooks"]]  # D5: one script, both hooks
        self.assertEqual([a[0].split("/")[-1] for a in start] + [a[-1] for a in start], ["attest.py", "--start"])
        self.assertFalse(os.path.exists(os.path.join(self.repo, installer.DEST, "register.py")))

    def test_manifest_verifies_until_a_hook_is_edited(self):  # D5: `detect` is the one check, the installer has none
        import subprocess, sys
        installer.install(self.repo)
        detect = lambda: json.loads(subprocess.run([sys.executable, os.path.join(self.repo, installer.DEST, "gauntletctl"), "detect"],
                                                   capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": self.repo}).stdout)
        self.assertEqual((detect()["manifest_verifies"], detect()["changed"]), (True, []))
        for name in ("gauntletctl", "critic_blind.py", "_paths.py"):
            self.assertTrue(os.path.exists(os.path.join(self.repo, installer.DEST, name)))
        hook = pathlib.Path(self.repo, installer.DEST, "critic_blind.py")
        hook.write_text(hook.read_text() + "\n# allow everything\n")
        self.assertEqual(detect()["changed"], [installer.DEST + "/critic_blind.py"])
        self.assertFalse(hasattr(installer, "verify"))

    def test_a_fresh_clone_reaches_tier_2_from_the_harness_files_steps_alone(self):  # AC-7.2
        import subprocess, sys
        git = lambda *a: subprocess.run(["git", "-C", self.repo, "-c", "user.email=t@t", "-c", "user.name=t", *a], check=True, capture_output=True)
        git("init", "-q", "-b", "main")
        subprocess.run([sys.executable, os.path.join(SKILL, "install", "claude_code.py"), self.repo], check=True, capture_output=True)  # step 1
        git("add", "-A")
        git("commit", "-qm", "gauntlet: install")  # step 4
        ctl = [sys.executable, os.path.join(self.repo, installer.DEST, "gauntletctl")]
        env = {**os.environ, "CLAUDE_PROJECT_DIR": self.repo}
        facts = json.loads(subprocess.run(ctl + ["detect"], capture_output=True, text=True, env=env).stdout)  # step 5
        self.assertEqual((facts["tier"], facts["changed"], facts["unwired"]), (2, [], []))
        self.assertEqual(subprocess.run(ctl + ["init"], capture_output=True, env=env).returncode, 0)
        status = subprocess.run(ctl + ["status"], capture_output=True, text=True, env=env).stdout
        self.assertIn("tier: 2", status)
        # Seen in the first real run: a hook's first execution left __pycache__ beside it, git status was no longer
        # clean, and the next `detect` said tier 3. Run every wired hook as the harness does, then look again.
        settings = json.loads(pathlib.Path(self.repo, ".claude", "settings.json").read_text())
        payload = json.dumps({"tool_name": "Read", "tool_input": {"file_path": "x"}, "agent_type": "editor", "agent_id": "a"})
        clean = {k: v for k, v in env.items() if k != "PYTHONDONTWRITEBYTECODE"}
        for group in settings["hooks"]["PreToolUse"]:
            for h in (h for h in group["hooks"] if h.get("args")):
                argv = [h["command"]] + [a.replace("${CLAUDE_PROJECT_DIR}", self.repo) for a in h["args"]]
                subprocess.run(argv, input=payload, capture_output=True, text=True, env=clean, cwd=self.repo)
        facts = json.loads(subprocess.run(ctl + ["detect"], capture_output=True, text=True, env=env).stdout)
        self.assertEqual((facts["tier"], facts["checked_in"]), (2, True))

    def test_the_two_reader_definitions_differ_in_name_and_model_only(self):
        a = pathlib.Path(SKILL, "agents", "reader.md").read_text().splitlines()
        b = pathlib.Path(SKILL, "agents", "reader-alt.md").read_text().splitlines()
        changed = [(x, y) for x, y in zip(a, b, strict=True) if x != y]
        self.assertEqual([x.split(":")[0] for x, _ in changed], ["name", "model"])


if __name__ == "__main__":
    unittest.main()
