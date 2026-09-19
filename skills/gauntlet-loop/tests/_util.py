"""Shared by the controller tests: the controller and installer loaded as modules, and a temporary git repository."""
import importlib.machinery
import importlib.util
import io
import json
import os
import pathlib
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

SKILL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def load(name, path):
    loader = importlib.machinery.SourceFileLoader(name, path)
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


ctl = load("gauntletctl", os.path.join(SKILL, "bin", "gauntletctl"))
installer = load("claude_code", os.path.join(SKILL, "install", "claude_code.py"))


class Repo(unittest.TestCase):
    """A temporary git repository the controller treats as the project."""

    installed = False

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = os.path.realpath(self.tmp.name)
        self.root = os.path.join(self.base, "repo")
        os.makedirs(self.root)
        os.environ["CLAUDE_PROJECT_DIR"] = self.root
        self.addCleanup(os.environ.pop, "CLAUDE_PROJECT_DIR", None)
        self.git("init", "-q", "-b", "main")
        if self.installed:
            self.install_and_commit()

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *argv):
        return subprocess.run(["git", "-C", self.root, "-c", "user.email=t@t", "-c", "user.name=t", *argv],
                              check=True, capture_output=True, text=True).stdout

    def install_and_commit(self):
        installer.install(self.root)
        self.git("add", "-A")
        self.git("commit", "-qm", "install")

    def run_ctl(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = ctl.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def ok(self, *argv):
        code, out, err = self.run_ctl(*argv)
        self.assertEqual(code, 0, err)
        return out

    def settings(self, name, data):
        path = pathlib.Path(self.root, ".claude", name)
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(data))

    def write(self, rel, text="x\n"):
        path = pathlib.Path(self.root, rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return str(path)

    def events(self):
        return ctl.read_events()

    def names(self):
        return [e["event"] for e in self.events()]
