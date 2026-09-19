"""Claims the method files make about the tooling, checked against the tooling."""
import inspect
import os
import pathlib
import re
import unittest

from _util import SKILL, ctl

REFS = pathlib.Path(SKILL, "references")


class Docs(unittest.TestCase):
    def test_the_harness_file_does_not_say_detect_reads_folder_trust(self):
        s1 = next(line for line in (REFS / "harness-claude-code.md").read_text().splitlines() if line.startswith("| S1 |"))
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


if __name__ == "__main__":
    unittest.main()
