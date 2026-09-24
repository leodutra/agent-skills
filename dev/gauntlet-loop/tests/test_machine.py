"""The store, init, and the state machine: every rejected transition has a test before the code that rejects it."""
import json
import os
import pathlib
import stat
import subprocess
import unittest

from _util import Repo, ctl


class Store(Repo):
    installed = True

    def test_init_writes_the_run_and_nothing_a_plain_git_add_could_stage(self):
        self.ok("init", "--invocations", "150", "--hours", "24", "--bar", "beats vercel/ms", "--invariant", "never touch payments")
        (started,) = self.events()
        self.assertEqual((started["seq"], started["event"], started["kind"], started["policy"], started["tier"]),
                         (1, "RUN_STARTED", "fact", "v1", 2))
        self.assertEqual(started["readers"], {"reader": "fable", "reader-alt": "opus"})
        mode = stat.S_IMODE(os.stat(os.path.join(self.root, ".gauntlet/private", "secret")).st_mode)
        self.assertEqual(mode, 0o600)
        self.assertFalse(os.path.exists(os.path.join(self.root, ".gauntlet/private/attest.key")))  # F9: the start hook makes it
        self.git("add", ".")
        self.assertEqual(self.git("status", "--porcelain"), "")  # .gauntlet/.gitignore holds one line, `*`

    def test_an_unreadable_file_is_a_refusal_that_names_it(self):  # F10: bytesize-2 printed a traceback
        self.ok("init")
        log = os.path.join(self.root, ".gauntlet/events.jsonl")
        os.chmod(log, 0)
        try:
            code, _, err = self.run_ctl("status")
        finally:
            os.chmod(log, 0o644)
        self.assertEqual(code, 3)
        self.assertIn(".gauntlet/events.jsonl", err)
        self.assertIn("harness-claude-code.md", err)

    def test_a_worktree_is_never_mistaken_for_the_project(self):  # F30: the units lead ran the controller from one
        self.ok("init")
        wt = os.path.join(self.root, ".gauntlet/wt/parse/src")
        os.makedirs(wt)
        os.environ["CLAUDE_PROJECT_DIR"] = wt
        self.assertEqual(ctl.root(), self.root)
        hooks = ctl.HERE.replace(os.path.join("bin"), "hooks") if ctl.HERE.endswith("bin") else ctl.HERE
        import sys
        sys.path.insert(0, hooks)
        try:
            import _paths
            self.assertEqual(_paths.project(), self.root)
        finally:
            sys.path.remove(hooks)
        self.ok("status")
        self.assertEqual(self.names()[-1], "LEAD_TURN")  # recorded in the project's own log

    def test_what_the_audit_cut_is_gone(self):  # D5: an unread field, a redundant subcommand
        with self.assertRaises(SystemExit):  # no such subcommand: every transaction already rewrites the file
            self.run_ctl("workbench")
        for field in ("write_mode_default", "bootstrap"):
            self.assertNotIn(field, ctl.POLICY["envelope"])

    def test_a_second_init_is_rejected(self):
        self.ok("init")
        self.assertEqual(self.run_ctl("init")[0], 2)

    def test_init_refuses_equal_or_missing_reader_pins(self):  # AC-17.9
        alt = pathlib.Path(self.root, ".claude/agents/reader-alt.md")
        alt.write_text(alt.read_text().replace("model: opus", "model: fable"))
        self.assertEqual(self.run_ctl("init")[0], 3)
        alt.unlink()
        self.assertEqual(self.run_ctl("init")[0], 3)
        self.assertEqual(self.events(), [])

    def test_state_is_the_fold_of_the_log_and_the_cache_is_rebuilt(self):
        self.ok("init")
        self.ok("log-block", "BLIND_BLOCK", '{"agent_id": "a"}')
        cache = pathlib.Path(self.root, ".gauntlet/state.json")
        self.assertEqual(json.loads(cache.read_text()), ctl.load())
        cache.unlink()
        self.assertEqual(ctl.load()["blocks"], 1)
        self.assertEqual([e["seq"] for e in self.events()], [1, 2])

    def test_the_policy_is_pinned_for_the_run_and_has_no_truth_condition(self):  # FR-17.5
        self.ok("init")
        self.assertFalse({"critics", "critic_count", "confirm", "confirmation_required", "blind", "win", "strength"} & set(ctl.POLICY))
        version, ctl.POLICY["version"] = ctl.POLICY["version"], "v2"
        self.addCleanup(ctl.POLICY.__setitem__, "version", version)
        self.assertEqual(self.run_ctl("event", "SPLIT_DECIDED", "pieces=2")[0], 3)
        self.assertEqual(self.names(), ["RUN_STARTED"])

    def test_an_unknown_event_never_reaches_the_log(self):
        self.ok("init")
        with self.assertRaises(ctl.Rejected):
            with ctl.transaction() as tx:
                tx.emit("MADE_UP", "fact", "test")
        self.assertEqual(self.names(), ["RUN_STARTED"])


class Sim:
    """The machine in memory: the same Tx the CLI uses, with no files behind it."""

    def __init__(self, mode="reference", frozen=True):
        self.tx = ctl.Tx([])
        self.fact("RUN_STARTED", run="g-test", policy="v1", tier=2, containment={}, attestation="tier-2",
                  readers={"reader": "fable", "reader-alt": "opus"}, envelope={"E": 150, "T_hours": 24})
        if frozen:
            self.fact("REFERENCE_FROZEN", artifact="reference/ms")
            self.fact("PIECE_OPENED", piece="parse", piece_kind="piece", referent="reference/ms", mode=mode, worktree=".gauntlet/wt/parse")

    def fact(self, name, **fields):
        return self.tx.emit(name, "fact", "test", **fields)

    def judgment(self, name, **fields):
        return self.tx.emit(name, "judgment", "event", actor="lead", **fields)

    @property
    def piece(self):
        return self.tx.state["pieces"]["parse"]

    def names(self):
        return [e["event"] for e in self.tx.new if e["event"] != "RUN_ENDED"]  # a one-piece run ends when its piece does

    def build_and_pass(self):
        self.fact("BUILDER_DONE", piece="parse", artifact=".gauntlet/wt/parse")
        self.fact("FLOOR_PASS", piece="parse")

    def verdict(self, order, winner=None, gap=None, agent_type=None, shape="pairwise", valid=True, model=None):
        agent_type = agent_type or ("reader" if order == "first" else "reader-alt")
        attempt = f"at{len(self.tx.new)}"
        self.fact("CRITIC_DISPATCHED", piece="parse", attempt_id=attempt, pair_id=attempt, shape=shape, order=order,
                  expected_type="reader" if order == "first" else "reader-alt")
        return self.fact("CRITIC_RESULT", piece="parse", attempt_id=attempt, agent_type=agent_type, valid=valid,
                         model=model or self.tx.state["readers"][agent_type], winner=winner, gap=gap, shape=shape)

    def win(self):
        self.build_and_pass()
        self.verdict("first", "ours")
        self.verdict("swapped", "ours")


class Machine(unittest.TestCase):
    def rejected(self, sim, name, kind="fact", **fields):
        before = len(sim.tx.new)
        with self.assertRaises(ctl.Rejected):
            sim.tx.emit(name, kind, "test", **fields)
        self.assertEqual(len(sim.tx.new), before)

    def test_no_piece_before_the_reference_is_frozen(self):  # AC-NN.1
        sim = Sim(frozen=False)
        self.rejected(sim, "PIECE_OPENED", piece="parse", referent="reference/ms", mode="reference")

    def test_a_piece_needs_a_referent(self):  # FR-2.1
        sim = Sim()
        self.rejected(sim, "PIECE_OPENED", piece="format", referent=None, mode="reference")
        self.rejected(sim, "PIECE_OPENED", piece="format", referent=None, mode="champion-challenger")

    def test_the_minimal_path_to_confirmed(self):
        sim = Sim()
        sim.win()
        self.assertEqual(sim.piece["state"], "CONFIRMED")
        self.assertEqual([n for n in sim.names() if n.endswith("_WIN")], ["CRITIC_WIN", "CONFIRMATION_WIN"])

    def test_no_pair_on_a_red_or_missing_floor(self):  # FR-NN.4
        sim = Sim()
        sim.fact("BUILDER_DONE", piece="parse", artifact="x")
        self.rejected(sim, "CRITIC_DISPATCHED", piece="parse", attempt_id="a", pair_id="a", shape="pairwise", order="first", expected_type="reader")
        sim.fact("FLOOR_FAIL", piece="parse", **{"class": "artifact"})
        self.rejected(sim, "CRITIC_DISPATCHED", piece="parse", attempt_id="a", pair_id="a", shape="pairwise", order="first", expected_type="reader")

    def test_no_confirmed_without_a_confirmation_win(self):
        sim = Sim()
        sim.build_and_pass()
        self.rejected(sim, "CONFIRMATION_WIN", piece="parse", attempt_id="x", model="opus", agent_type="reader-alt")
        sim.verdict("first", "ours")
        self.assertEqual(sim.piece["state"], "AWAITING_CONFIRMATION")
        self.rejected(sim, "WAVE_COMPLETE", piece="parse", artifact="abc123")

    def test_confirmation_needs_the_other_reader_on_another_model(self):  # AC-NN.5, FR-17.13
        sim = Sim()
        sim.build_and_pass()
        sim.verdict("first", "ours")
        with self.assertRaises(ctl.Rejected):
            sim.verdict("swapped", "ours", agent_type="reader-alt", model="fable")  # same model id as the first critic
        sim = Sim()
        sim.build_and_pass()
        sim.verdict("first", "ours")
        sim.verdict("swapped", "ours", agent_type="reader")  # a confirmation attested from `reader`
        self.assertEqual((sim.names()[-1], sim.piece["state"]), ("VERDICT_INVALID", "AWAITING_CONFIRMATION"))

    def test_a_loss_is_not_confirmed_and_a_lost_confirmation_reopens(self):
        sim = Sim()
        sim.build_and_pass()
        sim.verdict("first", "reference", gap="prints fractional units")
        self.assertEqual((sim.names()[-1], sim.piece["state"], sim.piece["last_gap"]), ("CRITIC_LOSS", "ACTIVE", "prints fractional units"))
        sim.judgment("GAP_ROUTED", piece="parse", **{"class": "artifact"})
        sim.build_and_pass()
        sim.verdict("first", "ours")
        sim.verdict("swapped", "reference", gap="long form says 2 hour")
        self.assertEqual((sim.names()[-1], sim.piece["state"]), ("CONFIRMATION_LOSS", "ACTIVE"))

    def test_promotion_only_from_integrated(self):
        sim = Sim()
        self.rejected(sim, "PR_MERGED", piece="parse", artifact="pr/1")  # ACTIVE -> PROMOTED
        sim.win()
        self.rejected(sim, "PR_MERGED", piece="parse", artifact="pr/1")  # CONFIRMED -> PROMOTED without INTEGRATED
        sim.fact("WAVE_COMPLETE", piece="parse", artifact="abc123")
        sim.fact("PR_MERGED", piece="parse", artifact="pr/1")
        self.assertEqual(sim.piece["state"], "PROMOTED")

    def test_parked_leaves_only_by_a_human(self):  # AC-4.2
        sim = Sim()
        sim.judgment("PARK_REQUESTED", piece="parse", reason="needs a migration", **{"class": "execution"})
        self.assertEqual((sim.names()[-1], sim.piece["state"]), ("PIECE_PARKED", "PARKED"))
        for name in ("BUILDER_DONE", "FLOOR_PASS", "FLOOR_FAIL", "CRITIC_WIN", "CRITIC_LOSS", "CONFIRMATION_WIN", "GAP_REPEATED",
                     "WAVE_COMPLETE", "PR_MERGED", "PIECE_BLOCKED", "BLOCKER_CLEARED", "PIECE_PARKED", "LEASE_EXPIRED"):
            self.rejected(sim, name, piece="parse", artifact="x", attempt_id="x", model="opus", agent_type="reader-alt")
        self.rejected(sim, "HUMAN_RESUMED", piece="parse")  # no actor named
        sim.tx.emit("HUMAN_RESUMED", "fact", "resume", piece="parse", actor="leo")
        self.assertEqual(sim.piece["state"], "ACTIVE")

    def test_blocked_clears_or_parks(self):
        sim = Sim()
        sim.judgment("BLOCK_REQUESTED", piece="parse", reason="no isolation for reference code")
        self.assertEqual((sim.names()[-1], sim.piece["state"]), ("PIECE_BLOCKED", "BLOCKED"))
        self.rejected(sim, "BUILDER_DONE", piece="parse", artifact="x")
        sim.judgment("BLOCKER_CLEARED", piece="parse", note="sandbox enabled")
        self.assertEqual(sim.piece["state"], "ACTIVE")

    def test_a_repeated_gap_climbs_the_ladder_and_then_parks(self):
        sim = Sim()
        for rung in (1, 2, 3):
            sim.judgment("GAP_SAME_AS_LAST", piece="parse")
            self.assertEqual((sim.names()[-1], sim.piece["rung"], sim.piece["state"]), ("GAP_REPEATED", rung, "ACTIVE"))
        sim.judgment("GAP_SAME_AS_LAST", piece="parse")
        self.assertEqual((sim.names()[-1], sim.piece["state"]), ("PIECE_PARKED", "PARKED"))

    def test_variants_are_staged_two_first_and_a_third_only_after(self):  # FR-6.3
        sim = Sim()
        self.rejected(sim, "VARIANT_APPROACHES_SELECTED", kind="judgment", piece="parse", approaches="table|regex|parser-combinator")
        sim.judgment("VARIANT_APPROACHES_SELECTED", piece="parse", approaches="table|regex")
        self.rejected(sim, "VARIANT_APPROACHES_SELECTED", kind="judgment", piece="parse", approaches="a|b")
        sim.judgment("VARIANT_APPROACHES_SELECTED", piece="parse", approaches="parser-combinator")
        self.assertEqual(sim.piece["variants"], ["table", "regex", "parser-combinator"])

    def test_not_reproduced_must_name_an_observed_rerun(self):  # FR-5.3
        sim = Sim()
        sim.build_and_pass()
        sim.verdict("first", "reference", gap="returns 0 for abc")
        self.rejected(sim, "NOT_REPRODUCED_ACCEPTED", kind="judgment", piece="parse", rerun=999)
        seq = sim.fact("RERUN_OBSERVED", piece="parse", note="node run.mjs b abc", artifact="exit 1")["seq"]
        sim.judgment("NOT_REPRODUCED_ACCEPTED", piece="parse", rerun=seq)
        self.assertEqual((sim.names()[-1], sim.tx.new[-1]["reason"], sim.piece["last_gap"]), ("VERDICT_INVALID", "not-reproduced", None))

    def test_champion_challenger_from_open_to_confirmed(self):  # A1, C13
        sim = Sim(mode="champion-challenger")
        sim.build_and_pass()  # the first green attempt is the champion, unjudged
        self.assertEqual(sim.piece["champion"], 1)
        sim.fact("BUILDER_DONE", piece="parse", artifact="x")
        sim.fact("FLOOR_PASS", piece="parse")
        sim.verdict("first", "ours")
        sim.verdict("swapped", "ours")
        self.assertEqual((sim.names()[-2:], sim.piece["state"], sim.piece["champion"]), (["CONFIRMATION_WIN", "CHAMPION_REPLACED"], "ACTIVE", 2))
        with self.assertRaises(ctl.Rejected):
            sim.verdict("first", shape="gap-only")  # no gap-only check before two challenger losses in a row
        for _ in range(2):
            sim.fact("BUILDER_DONE", piece="parse", artifact="x")
            sim.fact("FLOOR_PASS", piece="parse")
            sim.verdict("first", "reference", gap="still slower")
        self.assertEqual(sim.piece["challenger_losses"], 2)
        sim.verdict("first", shape="gap-only", gap=None)
        self.assertEqual(sim.piece["state"], "AWAITING_CONFIRMATION")
        sim.verdict("swapped", shape="gap-only", gap=None)
        self.assertEqual((sim.names()[-1], sim.piece["state"], sim.piece["converged"]), ("CONVERGED", "CONFIRMED", True))

    def test_a_named_gap_from_either_reader_reopens_the_piece(self):
        sim = Sim(mode="champion-challenger")
        sim.build_and_pass()
        sim.piece["challenger_losses"] = 2
        sim.verdict("first", shape="gap-only", gap=None)
        sim.verdict("swapped", shape="gap-only", gap="no retry on a dropped connection")
        self.assertEqual((sim.piece["state"], sim.piece["last_gap"]), ("ACTIVE", "no retry on a dropped connection"))

    def test_converged_is_rejected_outside_its_mode_or_without_both_readers(self):
        sim = Sim()
        sim.build_and_pass()
        self.rejected(sim, "CONVERGED", piece="parse")  # a reference-mode piece
        sim = Sim(mode="champion-challenger")
        sim.build_and_pass()
        self.rejected(sim, "CONVERGED", piece="parse")  # no gap-only verdict at all
        sim.piece["challenger_losses"] = 2
        sim.verdict("first", shape="gap-only", gap=None)
        self.rejected(sim, "CONVERGED", piece="parse")  # the second one is missing
        sim.verdict("swapped", shape="gap-only", gap=None, agent_type="reader")  # the second one came from `reader`
        self.assertEqual((sim.names()[-1], sim.piece["state"]), ("VERDICT_INVALID", "AWAITING_CONFIRMATION"))


class EventCommand(Repo):
    installed = True

    def setUp(self):
        super().setUp()
        self.ok("init", "--invocations", "150", "--hours", "24")

    def test_every_fact_name_is_rejected(self):  # AC-17.2, AC-17.6
        for name in sorted(ctl.FACTS):
            code, _, err = self.run_ctl("event", name, "piece=parse")
            self.assertEqual(code, 2, name)
            self.assertIn("judgment", err)
        self.assertEqual(self.names(), ["RUN_STARTED"])

    def test_a_question_for_the_user_is_filed_where_they_look(self):  # F23: the units lead had nowhere to put five
        self.ok("event", "QUESTION_FILED", "note=Is a KB 1000 or 1024 bytes? Assumed 1024 (DERIVED)")
        self.write("upstream/index.js")
        self.ok("freeze", os.path.join(self.root, "upstream"), os.path.join(self.root, "reference/ms"))
        self.ok("event", "SPLIT_DECIDED", "pieces=1")
        self.ok("piece", "open", "parse", "--referent", "reference/ms")
        self.ok("event", "QUESTION_FILED", "piece=parse", "note=Throw or return null on bad input? Assumed throw")
        self.assertEqual(ctl.load()["open_questions"], ["Is a KB 1000 or 1024 bytes? Assumed 1024 (DERIVED)",
                                                        "parse: Throw or return null on bad input? Assumed throw"])
        self.assertEqual(ctl.load()["pieces"]["parse"]["state"], "ACTIVE")  # a question moves nothing
        self.assertIn("parse: Throw or return null", pathlib.Path(self.root, ".gauntlet/workbench.md").read_text())
        self.assertEqual(self.run_ctl("event", "QUESTION_FILED")[0], 2)  # no note
        self.ok("report")
        report = pathlib.Path(self.root, ".gauntlet/report.md").read_text()
        self.assertIn("## Open questions for the user", report)
        self.assertIn("Is a KB 1000 or 1024 bytes?", report)

    def test_judgments_need_their_fields(self):
        self.assertEqual(self.run_ctl("event", "PARK_REQUESTED", "piece=parse")[0], 2)  # no reason, no class
        self.assertEqual(self.run_ctl("event", "GAP_ROUTED", "piece=parse", "class=taste")[0], 2)  # not a class

    def test_referent_and_mode_are_judgments_recorded_before_the_piece_opens(self):  # spec 8.4.1 as amended (A13)
        self.write("upstream/index.js")
        self.ok("freeze", os.path.join(self.root, "upstream"), os.path.join(self.root, "reference/ms"))
        self.ok("event", "SPLIT_DECIDED", "pieces=2")
        self.assertEqual(self.run_ctl("event", "MODE_SELECTED", "piece=parse", "mode=tournament")[0], 2)  # not a mode
        self.ok("event", "REFERENT_SELECTED", "piece=parse", "referent=reference/ms")
        self.ok("event", "MODE_SELECTED", "piece=parse", "mode=champion-challenger")
        self.ok("piece", "open", "parse")  # no flags: the recorded judgments are what it opens with
        piece = ctl.load()["pieces"]["parse"]
        self.assertEqual((piece["referent"], piece["mode"]), ("reference/ms", "champion-challenger"))
        for late in (("REFERENT_SELECTED", "referent=reference/other"), ("MODE_SELECTED", "mode=reference")):
            code, _, err = self.run_ctl("event", late[0], "piece=parse", late[1])
            self.assertEqual((code, "new run" in err), (2, True), late)  # a piece's bar does not move under its verdicts

    def test_piece_open_makes_the_worktree_and_split_retires_the_parent(self):
        self.assertEqual(self.run_ctl("piece", "open", "parse", "--referent", "reference/ms")[0], 2)  # nothing frozen
        self.write("upstream/index.js")
        self.ok("freeze", os.path.join(self.root, "upstream"), os.path.join(self.root, "reference/ms"))
        self.ok("event", "SPLIT_DECIDED", "pieces=2")
        self.write("config/.env.production", "DB_PASSWORD=hunter2hunter2\n")
        self.write("src/app.js")
        self.git("add", "-A")
        self.git("commit", "-qm", "an env file somebody checked in")
        self.ok("piece", "open", "parse", "--referent", "reference/ms")
        self.assertTrue(os.path.isdir(os.path.join(self.root, ".gauntlet/wt/parse")))
        wt = os.path.join(self.root, ".gauntlet/wt/parse")
        self.assertTrue(os.path.exists(os.path.join(wt, "src/app.js")))
        self.assertFalse(os.path.exists(os.path.join(wt, "config/.env.production")))  # FR-15.3: not inherited
        self.assertEqual(subprocess.run(["git", "-C", wt, "status", "--porcelain"], capture_output=True, text=True).stdout, "")
        self.ok("piece", "split", "parse", "parse-units", "parse-errors")
        state = ctl.load()
        self.assertTrue(state["pieces"]["parse"]["superseded"])
        self.assertEqual([state["pieces"][p]["state"] for p in ("parse-units", "parse-errors")], ["ACTIVE", "ACTIVE"])
        self.assertEqual(self.run_ctl("event", "GAP_ROUTED", "piece=parse", "class=artifact")[0], 2)  # the parent is gone


class Floors(Repo):
    installed = True

    def setUp(self):
        super().setUp()
        self.ok("init", "--invocations", "150", "--hours", "24")
        self.write("upstream/index.js")
        self.ok("freeze", os.path.join(self.root, "upstream"), os.path.join(self.root, "reference/ms"))
        self.ok("event", "SPLIT_DECIDED", "pieces=1")
        self.ok("piece", "open", "parse", "--referent", "reference/ms")
        with ctl.transaction() as tx:
            tx.emit("BUILDER_DONE", "fact", "test", piece="parse", artifact=".gauntlet/wt/parse")

    def test_add_copies_the_staged_file_into_the_protected_tree(self):  # A3
        self.write(".gauntlet/staging/edge.test.mjs", "// a held-out case\n")
        self.ok("floor", "add", "heldout", "--cmd", "true", "--from", ".gauntlet/staging/edge.test.mjs", "--to", "heldout/edge.test.mjs", "--derived")
        self.assertTrue(os.path.exists(os.path.join(self.root, "heldout/edge.test.mjs")))
        self.assertEqual(ctl.load()["floors"]["heldout"], {"cmd": "true", "derived": True, "piece": None, "needs_reference": False, "path": "heldout/edge.test.mjs"})
        self.assertEqual(self.run_ctl("floor", "add", "heldout", "--cmd", "true")[0], 2)  # it exists: amend it
        self.assertEqual(self.run_ctl("floor", "add", "x", "--cmd", "true", "--from", "src/app.js", "--to", "heldout/x.mjs")[0], 2)  # not staged
        self.assertEqual(self.run_ctl("floor", "add", "y", "--cmd", "true", "--from", ".gauntlet/staging/edge.test.mjs", "--to", "src/y.mjs")[0], 2)  # not a floor tree
        self.assertIn("DERIVED", self.ok("floor", "list"))

    def test_floors_writes_outputs_and_records_pass_or_fail(self):
        self.ok("floor", "add", "required", "--cmd", "echo 24 passed")
        self.ok("floors", "parse")
        self.assertEqual(self.names()[-1], "FLOOR_PASS")
        out = pathlib.Path(self.root, ".gauntlet/floors/parse/r1/required.txt").read_text()
        self.assertIn("exit 0\n24 passed", out)
        self.ok("floor", "add", "heldout", "--cmd", "echo 9/12; exit 1")
        self.assertEqual(self.run_ctl("floors", "parse")[0], 2)
        failed = self.events()[-1]
        self.assertEqual((failed["event"], failed["class"], failed["note"]), ("FLOOR_FAIL", "artifact", "heldout"))
        self.assertEqual(self.run_ctl("pair", "parse")[0], 2)  # a red floor ends the round

    def test_a_floor_that_executes_the_reference_blocks_without_isolation(self):  # AC-15.4, second half
        self.ok("floor", "add", "ref-suite", "--cmd", "echo ran", "--needs-reference")
        self.assertEqual(self.run_ctl("floors", "parse")[0], 3)
        blocked = self.events()[-1]
        self.assertEqual((blocked["event"], blocked["class"], ctl.load()["pieces"]["parse"]["state"]), ("PIECE_BLOCKED", "execution", "BLOCKED"))
        self.ok("event", "BLOCKER_CLEARED", "piece=parse", "note=sandbox enabled")
        detect, probe = ctl.detect, ctl.probe_escapes
        ctl.detect, ctl.probe_escapes = (lambda: {**detect(), "isolated": True}), (lambda: False)
        self.addCleanup(setattr, ctl, "detect", detect)
        self.addCleanup(setattr, ctl, "probe_escapes", probe)
        self.ok("floors", "parse")
        self.assertEqual(self.names()[-1], "FLOOR_PASS")

    def test_amend_logs_old_and_new_and_marks_confirmed_pieces(self):
        self.ok("floor", "add", "required", "--cmd", "true")
        self.ok("floors", "parse")
        with ctl.transaction() as tx:
            for order, agent in (("first", "reader"), ("swapped", "reader-alt")):
                tx.emit("CRITIC_DISPATCHED", "fact", "t", piece="parse", attempt_id=order, pair_id=order, shape="pairwise", order=order, expected_type=agent)
                tx.emit("CRITIC_RESULT", "fact", "t", piece="parse", attempt_id=order, agent_type=agent, valid=True, model=tx.state["readers"][agent], winner="ours")
        self.ok("floor", "amend", "required", "--cmd", "false")
        amended = self.events()[-1]
        self.assertEqual((amended["event"], amended["old"], amended["new"], amended["class"]), ("FLOOR_AMENDED", "true", "false", "evaluation"))
        self.assertTrue(ctl.load()["pieces"]["parse"]["needs_floors"])
        self.assertEqual(self.run_ctl("floors", "parse")[0], 2)
        self.assertEqual(ctl.load()["pieces"]["parse"]["state"], "ACTIVE")  # a red one loses its confirmation

    def test_rerun_records_what_it_observed(self):
        self.ok("rerun", "parse", "echo 1.5h")
        observed = self.events()[-1]
        self.assertEqual((observed["event"], observed["note"], observed["exit"]), ("RERUN_OBSERVED", "echo 1.5h", 0))
        self.assertIn("1.5h", pathlib.Path(self.root, observed["artifact"]).read_text())
