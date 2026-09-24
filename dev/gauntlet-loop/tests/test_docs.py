"""Claims the method files make about the tooling, checked against the tooling."""
import inspect
import os
import pathlib
import re
import unittest

from _util import SKILL, ctl

REFS = pathlib.Path(SKILL, "references")
EVIDENCE = pathlib.Path(SKILL, "..", "..", "dev", "gauntlet-loop", "design", "harness-evidence.md")


class Docs(unittest.TestCase):
    def test_the_harness_file_does_not_say_detect_reads_folder_trust(self):
        s1 = next(line for line in EVIDENCE.read_text().splitlines() if line.startswith("| S1 |"))
        self.assertNotIn("`detect` reads the folder's trust", s1)
        self.assertIn("never reads the folder's trust", s1)
        self.assertNotIn("trust", inspect.getsource(ctl.detect).lower())  # and it does not

    def test_the_runbook_has_a_by_hand_path_inside_its_ceiling(self):
        text = (REFS / "running-the-loop.md").read_text()
        self.assertLessEqual(len(text.encode()), 10239)
        section = re.search(r"(?ms)^## By hand\n(.*?)(?=^## )", text)
        self.assertTrue(section, "no `## By hand` section")
        for needle in ("Tier 3", "coin", "mapping", "swapped", "different model", "ceiling", "unattested"):
            self.assertIn(needle, section.group(1))
        self.assertIn("By hand", text.split("## Round zero")[0])  # the opening points at it

    def test_a_builder_runs_its_required_suite_without_an_env_prefix(self):  # A4: auto mode refused the prefix, 2026-09-19
        text = (REFS / "running-the-loop.md").read_text()
        self.assertIn("else the working directory", text)  # the AUTHOR line: how a floor file finds ours
        self.assertIn("Required suite, from your worktree:", text)  # the BUILDER line

    def test_an_installed_controller_that_errors_stops_the_run(self):  # F11: bytesize-2 went by hand at Tier 3
        section = re.search(r"(?ms)^## By hand\n(.*?)(?=^## )", (REFS / "running-the-loop.md").read_text()).group(1)
        self.assertIn("never continue by hand", section)

    def test_a_builder_returns_its_directory_for_code(self):  # F17: bytesize-3's builder returned src/index.js
        text = pathlib.Path(SKILL, "agents", "editor.md").read_text()
        self.assertIn("your directory for code", text)
        self.assertIn("a single document", text)

    def test_the_lead_can_file_a_question(self):  # F23
        self.assertIn("QUESTION_FILED", (REFS / "running-the-loop.md").read_text())
        self.assertIn("`QUESTION_FILED` (note", (REFS / "controller.md").read_text())

    def test_the_runbook_spends_fewer_lead_calls(self):  # Stage E1, E3, E4
        text = (REFS / "running-the-loop.md").read_text()
        self.assertNotIn("After every event run `gauntletctl next`", text)
        self.assertIn("ends with its next lines", text)  # E1
        self.assertIn("`round`", text.split("## A round")[1].split("## ")[0])  # E3
        self.assertIn("parallel", text)  # E4

    def test_the_lead_loads_less(self):  # Stage E2
        text = (REFS / "running-the-loop.md").read_text()
        self.assertIn("`example-run.md` only when stuck", text)
        self.assertIn("never read the controller's or the hooks' source", text)
        harness = (REFS / "harness-claude-code.md").read_text()
        for evidence in ("## Spikes", "## Checks by hand", "| S1 |"):
            self.assertNotIn(evidence, harness)  # dated evidence is for humans, in dev/
        self.assertIn("| S14 |", EVIDENCE.read_text())

    def test_a_reader_is_told_how_its_first_command_binds_and_where_scratch_goes(self):  # F33
        for name in ("reader.md", "reader-alt.md"):
            text = pathlib.Path(SKILL, "agents", name).read_text()
            self.assertIn("full path in your first command", text)
            self.assertIn("never in a temp folder", text)
            self.assertNotIn("your shell already starts there", text)

    def test_a_critic_runs_only_what_the_pair_holds(self):  # F34: units-2 critics hunted for the hostile script
        coding = (REFS / "domains" / "coding.md").read_text()
        self.assertNotIn("the hostile-input script from a clean checkout", coding)
        self.assertIn("FLOORS/", coding)

    def test_the_freeze_is_never_offloaded(self):  # A9
        text = (REFS / "running-the-loop.md").read_text()
        self.assertNotIn("does the freeze", text)
        self.assertNotIn("or the `freeze` command", text)


if __name__ == "__main__":
    unittest.main()
