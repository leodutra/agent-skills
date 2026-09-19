"""references/example-run.md is a run the real machine produced: the fixture folds without a rejection, the generator
still produces it, and every status line and metric the document quotes is what the controller prints."""
import json
import os
import pathlib
import re
import unittest

import make_example
from _util import SKILL, ctl

EVENTS = [json.loads(line) for line in pathlib.Path(SKILL, "tests", "fixtures", "example-events.jsonl").read_text().splitlines()]
DOC = pathlib.Path(SKILL, "references", "example-run.md").read_text()


class Example(unittest.TestCase):
    def test_the_log_folds_and_the_run_ends_in_a_win(self):  # AC-17.3
        state = ctl.fold(EVENTS)
        self.assertEqual(state["run"]["ended"], "win")
        self.assertEqual({p["state"] for p in ctl.live_pieces(state).values()}, {"PROMOTED", "CONFIRMED"})

    def test_the_generator_still_produces_this_log(self):
        real_open, produced = open, []

        def capture(path, mode="r", *a, **kw):
            if "example-events.jsonl" in str(path) and "w" in mode:
                class Sink:
                    def __enter__(self): return self
                    def __exit__(self, *exc): return False
                    def writelines(self, lines): produced.extend(json.loads(line) for line in lines)
                return Sink()
            return real_open(path, mode, *a, **kw)

        import builtins, contextlib, io
        builtins.open = capture
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                make_example.main()
        finally:
            builtins.open = real_open
        self.assertEqual(produced, EVENTS, "the machine changed: run tests/make_example.py and update the document")

    def test_every_status_line_in_the_document_is_the_controllers(self):  # AC-17.4, AC-14.2
        position = 0
        for i, e in enumerate(EVENTS):
            if e["event"] == "LEAD_TURN":
                line = ctl.status_line(ctl.fold(EVENTS[:i + 1]), at=e["ts"])
                found = DOC.find(line, position)
                self.assertNotEqual(found, -1, f"turn '{e['note']}': the document lacks or misorders: {line}")
                position = found + 1

    def test_the_metrics_block_is_the_controllers(self):  # AC-13.1, AC-16.1
        for line in ctl.metric_lines(ctl.metrics(EVENTS, ctl.fold(EVENTS))):
            self.assertIn(line, DOC)
        classes = ctl.metrics(EVENTS, ctl.fold(EVENTS))["by_class"]
        self.assertTrue(all(classes.values()), f"the example shows one failure of each class: {classes}")

    def test_the_run_shows_what_the_plan_says_it_shows(self):  # AC-5.1, AC-6.2, AC-10.3, AC-12.2
        names = [e["event"] for e in EVENTS]
        for name in ("REFERENCE_FROZEN", "REFERENCE_VERIFIED", "PLAN_COMMITTED", "FLOOR_FAIL", "VERDICT_INVALID", "NOT_REPRODUCED_ACCEPTED",
                     "GAP_REPEATED", "PIECE_BLOCKED", "BLOCKER_CLEARED", "PIECE_PARKED", "HUMAN_RESUMED", "CHAMPION_REPLACED", "CONVERGED",
                     "WAVE_COMPLETE", "SCOPE_FAILURE_FILED", "ARTIFACTS_COMMITTED", "PR_OPENED", "PR_MERGED", "RUN_ENDED"):
            self.assertIn(name, names)
        self.assertLess(names.index("PLAN_COMMITTED"), names.index("BUILDER_DONE"))  # the plan, before any builder returns
        self.assertTrue(any(e["event"] == "FLOOR_ADDED" and e.get("derived") and e.get("artifact") for e in EVENTS))  # a finding became a floor
        self.assertEqual(names.count("CRITIC_DISPATCHED"), names.count("CRITIC_RESULT"))  # one pair or swap per verdict
        rounds = [e for e in EVENTS if e["event"] == "BUILDER_DONE" and e.get("agent_id") == "a1f3"]
        self.assertEqual(len(rounds), 2)  # one builder, resumed across two rounds
        for needle in ("gauntletctl gate", "whole-r2-1.md: WINNER", "whole-r2-2.md: WINNER", "gauntletctl status --full", "gauntletctl commit --plan",
                       "permissions/allowlist.json", "- Reference manifest: reference/ms/MANIFEST", "- Workbench: .gauntlet/workbench.md",
                       "- Whole-gate verdicts: .gauntlet/verdicts/whole-r2-1.md, .gauntlet/verdicts/whole-r2-2.md", "converged against"):
            self.assertIn(needle, DOC)
        rerun = next(e["seq"] for e in EVENTS if e["event"] == "RERUN_OBSERVED" and e.get("piece") == "format")
        self.assertIn(f"rerun={rerun}", DOC)

    def test_the_pasted_prompt_is_the_template_filled_and_short_enough(self):  # AC-14.1, AC-NN.10
        prompt = re.search(r"```text\n(/goal .*?)```", DOC, re.S).group(1)
        self.assertLessEqual(len(prompt.split()), 270)
        self.assertIn("on a different model", prompt.splitlines()[0])
        self.assertIn("or 150 invocations or 24 hours are spent", prompt.splitlines()[0])
        template = re.search(r"```text\n(/goal .*?)```", pathlib.Path(SKILL, "SKILL.md").read_text(), re.S).group(1)
        fixed = [p for p in template.split("\n\n") if "[" not in p]
        for paragraph in fixed:
            self.assertIn(paragraph.strip(), prompt)


    def test_the_slash_command_is_the_template_too(self):  # C10
        command = pathlib.Path(SKILL, "..", "..", "slash-commands", "gauntlet-goal.md")
        if not command.exists():  # the skill folder is also mirrored on its own
            self.skipTest("not in the repository")
        text = command.read_text()
        template = re.search(r"```text\n(/goal .*?)```", pathlib.Path(SKILL, "SKILL.md").read_text(), re.S).group(1)
        for paragraph in [p for p in template.split("\n\n") if "[" not in p]:
            self.assertIn(paragraph.strip(), text)
        self.assertIn("on a different model", text)
        self.assertIn("or 150 invocations or 24 hours are spent", text)


if __name__ == "__main__":
    unittest.main()
