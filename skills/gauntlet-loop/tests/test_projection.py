"""What the lead and the user read is controller output: status, next, the workbench, the gate, metrics, commit, promote."""
import json
import os
import pathlib
import subprocess

from _util import Repo, ctl


class Run(Repo):
    installed = True

    def setUp(self):
        super().setUp()
        self.ok("init", "--invocations", "150", "--hours", "24", "--goal", "a duration library",
                "--bar", "beats vercel/ms blind; floor: suite green", "--critic-bar", "a duration library; floor: errors name the input",
                "--invariant", "never touch the payments code")
        self.write("upstream/index.js", "export const parse = () => 1\n")
        self.ok("freeze", self.root + "/upstream", self.root + "/reference/ms")
        self.write(".gauntlet/staging/prompt.md", "The bar: a duration parser.\n")
        self.ok("event", "SPLIT_DECIDED", "pieces=2")

    def open(self, pid, *flags):
        self.ok("piece", "open", pid, "--referent", "reference/ms", *flags)
        self.ok("pair", pid, "--prepare", "--reference", "reference/ms", "--prompt", ".gauntlet/staging/prompt.md")

    def built(self, pid):
        with ctl.transaction() as tx:
            tx.emit("BUILDER_DONE", "fact", "attest", piece=pid, artifact=f".gauntlet/wt/{pid}", agent_id="b-" + pid)
        self.write(f".gauntlet/wt/{pid}/src/{pid}.js", "export default 2\n")

    def verdict(self, pid, winner, gap=None):
        state = ctl.load()
        attempt_id, attempt = next((k, a) for k, a in state["attempts"].items() if a["status"] == "open" and a["piece"] == pid)
        agent = attempt["expected_type"]
        path = self.write(f".gauntlet/verdicts/{attempt['pair']}.md", f"PAIR: {attempt['pair']}\nEVIDENCE:\n- `x`\nWINNER: A\nGAP: {gap}\n")
        with ctl.transaction() as tx:
            tx.emit("CRITIC_RESULT", "fact", "attest", piece=pid, attempt_id=attempt_id, agent_type=agent, valid=True,
                    model=state["readers"][agent], winner=winner, gap=gap, artifact=os.path.relpath(path, self.root))

    def win(self, pid, built=True):
        if built:
            self.built(pid)
        self.ok("floors", pid)
        self.ok("pair", pid)
        self.verdict(pid, "ours")
        self.ok("swap", pid)
        self.verdict(pid, "ours")


class Status(Run):
    def test_the_status_line_is_verbatim_and_counts_lead_turns(self):  # AC-17.4, FR-14.3
        self.open("parse")
        self.open("format")
        self.assertEqual(self.ok("status").strip(),
                         "confirmed 0/2 pieces, whole: no | parked: 0 | blocked: 0 | spent: 2/150 inv, 0.0/24 h | tier: 2 | policy v1")
        self.win("parse")
        self.ok("event", "PARK_REQUESTED", "piece=format", "reason=needs a migration", "class=execution")
        self.assertEqual(self.ok("status").strip(),
                         "confirmed 1/1 pieces, whole: no | parked: 1 | blocked: 0 | spent: 4/150 inv, 0.0/24 h | ended: nothing-left")
        self.assertEqual(ctl.load()["run"]["lead_turns"], 2)

    def test_full_is_the_resume_view(self):  # FR-6.11
        self.open("parse")
        self.built("parse")
        full = self.ok("status", "--full")
        for needle in ("parse", "ACTIVE", "round 1", "b-parse", "floors parse", "never touch the payments code"):
            self.assertIn(needle, full)


class Next(Run):
    def test_names_what_is_mechanical_and_what_the_lead_owes(self):  # FR-17.4
        self.assertIn("piece open", self.ok("next"))
        self.open("parse")
        self.assertIn("commit --plan", self.ok("next"))
        self.built("parse")
        self.assertIn("mechanical  gauntletctl floors parse", self.ok("next"))
        self.ok("floors", "parse")
        self.assertIn("mechanical  gauntletctl pair parse", self.ok("next"))
        self.ok("pair", "parse")
        self.assertIn("waiting", self.ok("next"))
        self.verdict("parse", "reference", gap="prints fractional units")
        out = self.ok("next")
        self.assertIn("judgment", out)
        self.assertIn("GAP_SAME_AS_LAST", out)
        self.assertIn("GAP_ROUTED", out)
        self.ok("event", "GAP_SAME_AS_LAST", "piece=parse")
        self.assertIn("piece split parse", self.ok("next"))  # rung one: split


class Workbench(Run):
    def test_is_regenerated_on_every_event_and_lists_parked_first(self):  # FR-6.11, FR-4.5
        self.open("parse")
        self.open("format", "--champion-challenger")
        self.ok("floor", "add", "heldout", "--cmd", "true", "--derived")
        self.ok("event", "PARK_REQUESTED", "piece=format", "reason=needs a migration", "class=execution")
        text = pathlib.Path(self.root, ".gauntlet/workbench.md").read_text()
        for needle in ("Bar: beats vercel/ms blind", "Critic's bar: a duration library", "Tier: 2 enforced policy",
                       "Envelope: 150 invocations, 24 hours - local 90, escalation 37, gate 23", "never touch the payments code",
                       "DERIVED: heldout", "| parse | ACTIVE | reference/ms |", "champion-challenger", "needs a migration", "(execution)"):
            self.assertIn(needle, text)
        self.assertLess(text.index("## Parked"), text.index("| Piece |"))
        self.assertNotIn("A=", text)  # which side is ours is never in the workbench


class GateAndMetrics(Run):
    def test_gate_prints_the_two_verdict_files_and_their_winner_lines(self):  # FR-10.3
        self.open("parse")
        self.open("format")
        self.win("parse")
        self.win("format")
        self.ok("wave", "parse", "format", "--merge", "abc123")
        self.assertEqual({p["state"] for p in ctl.load()["pieces"].values()}, {"INTEGRATED"})
        self.ok("piece", "open", "whole", "--referent", "reference/ms", "--kind", "whole")
        self.ok("pair", "whole", "--prepare", "--reference", "reference/ms", "--prompt", ".gauntlet/staging/prompt.md")
        self.assertEqual(self.run_ctl("gate")[0], 2)  # not yet
        self.assertIn("gauntletctl floors whole", self.ok("next"))  # the whole is the merge: nothing builds it
        self.win("whole", built=False)
        lines = self.ok("gate").strip().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(all(".gauntlet/verdicts/whole-r1-" in line and line.endswith("WINNER: A") for line in lines))
        self.assertIn("ended: win", self.ok("status"))

    def test_metrics_come_from_the_log(self):  # FR-13.1, FR-16.3
        self.open("parse")
        self.open("format")
        self.built("parse")
        self.ok("floor", "add", "heldout", "--cmd", "exit 1")
        self.run_ctl("floors", "parse")  # red
        self.ok("event", "GAP_ROUTED", "piece=parse", "class=artifact")
        self.ok("floor", "amend", "heldout", "--cmd", "true")
        self.win("parse")
        m = json.loads(self.ok("metrics", "--json"))
        self.assertEqual((m["rounds_per_confirmed_piece"], m["red_floor_share"], m["confirmation_flip_rate"]), (2.0, 0.5, 0.0))
        self.assertEqual(m["by_class"], {"artifact": 1, "evaluation": 1, "execution": 0, "scope": 0})  # the red floor once, not again when routed
        self.assertEqual((m["spend"]["gate"], m["parked_pieces"], m["invocations_per_confirmed_piece"]), ("0/23", 0, 5.0))
        self.assertIn("rounds per confirmed piece", self.ok("metrics"))


class Report(Run):
    METRICS = ("rounds_per_confirmed_piece", "red_floor_share", "confirmation_flip_rate", "discarded_verdict_rate",
               "not_reproduced_accepted_rate", "parked_pieces", "escalations_per_piece", "share_of_escalations_from_spend",
               "invocations_per_confirmed_piece", "lead_turns_per_confirmed_piece", "controller_operations_per_confirmed_piece",
               "worker_minutes_per_confirmed_piece", "tokens_per_confirmed_piece", "spend", "unused_reserve", "ceiling_hit",
               "by_class", "rounds_per_confirmed_piece_after_split", "fresh_builder_gap_closed_within_two_rounds",
               "variant_escalations_whose_winner_confirmed", "converged_pieces_reopened", "whole_gate_loss_rate",
               "coherence_pieces", "rounds_to_confirm_coherence")

    def test_metrics_emits_every_named_metric(self):  # FR-13.1, FR-M.3
        self.open("parse")
        m = json.loads(self.ok("metrics", "--json"))
        self.assertEqual([k for k in self.METRICS if k not in m], [])
        self.assertEqual(m["tokens_per_confirmed_piece"], "n/a")

    def test_tokens_are_read_from_the_transcript_the_stop_hook_names(self):  # S8
        transcript = self.write("transcript.jsonl", "\n".join(json.dumps(
            {"type": "assistant", "message": {"model": "claude-x", "usage": {"input_tokens": 10, "output_tokens": n, "cache_read_input_tokens": 5}}}) for n in (100, 200)))
        self.assertEqual(ctl.transcript_tokens(transcript), 330)
        self.assertEqual(ctl.transcript_tokens("/no/such/file"), None)

    def test_the_report_puts_conflicts_and_parked_pieces_first_and_fills_every_field(self):  # FR-4.5, FR-13.2, AC-13.1
        self.open("parse")
        self.open("format")
        self.win("parse")
        self.ok("event", "PARK_REQUESTED", "piece=format", "reason=needs a migration", "class=execution")
        self.ok("event", "SCOPE_FAILURE_FILED", "note=the goal asked for one entry point and two")
        notes = self.write(".gauntlet/staging/notes.md", "format is below the bar: its long form still says `1 days`.\n")
        self.ok("report", "--notes", ".gauntlet/staging/notes.md")
        text = pathlib.Path(self.root, ".gauntlet/report.md").read_text()
        workbench = pathlib.Path(self.root, ".gauntlet/workbench.md").read_text()
        for words in ("isolated", "cannot reach"):  # AC-1.3: Tier 2 is enforced policy, never isolation
            self.assertNotIn(words, text + workbench + self.ok("status"))
        order = [text.index(h) for h in ("## Parked", "## Result", "## Pieces", "## Gap log", "## Intent draft", "## Metrics", "## Still below the bar")]
        self.assertEqual(order, sorted(order))
        for needle in ("ended: nothing-left", "Tier: 2 enforced policy", "sandbox off", "needs a migration", "one entry point and two",
                       "1 days", "confirmation flip rate", "local 4/90", *[k.replace("_", " ") for k in self.METRICS]):
            self.assertIn(needle, text)


class CommitPromote(Run):
    def test_plan_commit_stages_the_committed_set_and_nothing_else(self):  # FR-5.4, FR-12.2
        self.open("parse")
        self.ok("commit", "--plan")
        files = self.git("show", "--name-only", "--format=", "HEAD").split()
        self.assertEqual(sorted(files), [".gauntlet/events.jsonl", ".gauntlet/plan.md", ".gauntlet/workbench.md", "reference/ms/MANIFEST"])
        self.assertTrue(ctl.load()["run"]["plan_committed"])
        self.assertEqual(json.loads(self.git("show", "HEAD:.gauntlet/events.jsonl").splitlines()[-1])["event"], "PLAN_COMMITTED")

    def test_commit_refuses_on_a_secret(self):  # FR-15.4
        self.open("parse")
        self.write(".gauntlet/verdicts/parse-r1-1.md", "EVIDENCE:\n- config sets api_key = 'sk-fixture-0123456789abcdef0123'\n")
        code, _, err = self.run_ctl("commit")
        self.assertEqual((code, self.names()[-1]), (3, "SCAN_FAILED"))

    def test_promote_opens_the_pr_and_only_the_remote_promotes(self):  # FR-12.3
        self.open("parse")
        self.open("format")
        self.win("parse")
        self.win("format")
        self.ok("wave", "parse", "format", "--merge", "abc123")
        calls = []

        def fake(argv, **kw):
            calls.append(argv)
            out = "https://github.com/o/r/pull/7\n" if argv[:3] == ["gh", "pr", "create"] else '{"state": "MERGED"}' if argv[:3] == ["gh", "pr", "view"] else ""
            return subprocess.CompletedProcess(argv, 0, out, "")

        run, ctl.sh = ctl.sh, fake
        self.addCleanup(setattr, ctl, "sh", run)
        self.assertEqual(self.run_ctl("promote")[0], 2)  # nothing committed yet
        self.ok("commit")
        self.ok("promote")
        body = next(a for a in calls if a[:3] == ["gh", "pr", "create"])
        text = " ".join(body)
        for needle in ("reference/ms/MANIFEST", ".gauntlet/workbench.md", "tier 2"):
            self.assertIn(needle, text)
        self.assertEqual(self.names()[-1], "PR_OPENED")
        self.assertEqual(self.run_ctl("event", "PR_MERGED", "piece=parse")[0], 2)  # never from the lead
        self.ok("status")
        self.assertEqual({p["state"] for p in ctl.load()["pieces"].values()}, {"PROMOTED"})

    def test_resume_is_logged_with_its_actor(self):  # C8
        self.open("parse")
        self.ok("event", "PARK_REQUESTED", "piece=parse", "reason=needs a migration", "class=execution")
        self.assertEqual(self.run_ctl("resume", "parse")[0], 2)
        self.ok("resume", "parse", "--actor", "leo")
        self.assertEqual((self.events()[-1]["actor"], ctl.load()["pieces"]["parse"]["state"]), ("leo", "ACTIVE"))
