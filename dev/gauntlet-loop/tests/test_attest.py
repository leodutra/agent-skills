"""attest: a verdict stands only when the harness's stop hook delivered it for a registered, unattested agent of the
expected type, naming the open attempt's pair. The lead can route a critic; it cannot manufacture a result."""
import io
import json
import os
import pathlib
import sys

from _util import HERE, Repo, ctl

VERDICTS = pathlib.Path(HERE, "fixtures", "verdicts")


class AttestRepo(Repo):
    installed = True
    tier1 = False

    def setUp(self):
        super().setUp()
        if self.tier1:
            detect = ctl.detect
            ctl.detect = lambda: {**detect(), "attestation": "tier-1"}
            self.addCleanup(setattr, ctl, "detect", detect)
        self.ok("init", "--invocations", "150", "--hours", "24")
        self.write("upstream/index.js", "export const parse = () => 1\n")
        self.ok("freeze", os.path.join(self.root, "upstream"), os.path.join(self.root, "reference/ms"))
        self.write(".gauntlet/staging/prompt.md", "The bar: a duration parser.\n")
        self.ok("event", "SPLIT_DECIDED", "pieces=1")
        self.ok("piece", "open", "parse", "--referent", "reference/ms")
        self.ok("pair", "parse", "--prepare", "--reference", "reference/ms", "--prompt", ".gauntlet/staging/prompt.md")
        self.write(".gauntlet/wt/parse/src/parse.js", "export const parse = () => 2\n")
        self.write(".gauntlet/private/bindings/b1", "parse")  # builder_boundary wrote this on the builder's first edit

    def hook(self, payload, *flags):
        stdin, sys.stdin = sys.stdin, io.StringIO(json.dumps(payload))
        try:
            return self.run_ctl("attest", *flags)
        finally:
            sys.stdin = stdin

    def key(self):
        return ["--key-file", os.path.join(self.root, ".gauntlet/private/attest.key")] if self.tier1 else []

    def start(self, agent_id, agent_type):
        return self.hook({"hook_event_name": "SubagentStart", "agent_id": agent_id, "agent_type": agent_type}, "--start", *self.key())

    def stop(self, agent_id, agent_type, message, key=True, handback=None):
        """handback: the text the agent returned through the harness's handback tool, written to its transcript (A1)."""
        payload = {"hook_event_name": "SubagentStop", "agent_id": agent_id, "agent_type": agent_type,
                   "last_assistant_message": message}
        if handback is not None:
            path = pathlib.Path(self.base, f"{agent_id}.jsonl")
            lines = [{"message": {"role": "assistant", "content": [{"type": "text", "text": "Opening the pair."}]}},
                     {"message": {"role": "assistant", "content": [
                         {"type": "tool_use", "name": ctl.HARNESS["handback_tool"], "input": {"message": handback}}]}},
                     {"message": {"role": "assistant", "content": [{"type": "text", "text": message}]}}]
            path.write_text("".join(json.dumps(line) + "\n" for line in lines))
            payload["agent_transcript_path"] = str(path)
        return self.hook(payload, *(self.key() if key else []))

    def built(self, line=".gauntlet/wt/parse"):
        self.start("b1", "editor")
        self.stop("b1", "editor", line)

    def green_pair(self):
        self.built()
        self.ok("floors", "parse")
        self.ok("pair", "parse")
        return self.pair_id()

    def pair_id(self):
        return pathlib.Path(self.root, ".gauntlet/pairs/parse/PAIR_ID").read_text().strip()

    def label(self, side):
        mapping = json.loads(pathlib.Path(self.root, ".gauntlet/private/mapping", self.pair_id() + ".json").read_text())
        return "A" if mapping["a"] == side else "B"

    def verdict(self, name, winner="A", pair=None):
        return (VERDICTS / f"{name}.txt").read_text().format(pair=pair or self.pair_id(), winner=winner)

    piece = property(lambda self: ctl.load()["pieces"]["parse"])


class Readers(AttestRepo):
    def test_a_matching_verdict_becomes_a_win_or_a_loss_through_the_mapping(self):  # AC-17.7
        self.green_pair()
        self.start("r1", "reader")
        self.stop("r1", "reader", self.verdict("valid", self.label("reference")))
        loss = self.events()[-1]
        self.assertEqual((loss["event"], loss["class"], loss["model"], self.piece["state"]), ("CRITIC_LOSS", "artifact", "fable", "ACTIVE"))
        self.assertIn("fractional units", loss["gap"])
        filed = pathlib.Path(self.root, ".gauntlet/verdicts/parse-r1-1.md").read_text()
        self.assertIn("EVIDENCE:", filed)

        self.ok("event", "GAP_ROUTED", "piece=parse", "class=artifact")
        self.green_pair()
        self.start("r2", "reader")
        self.stop("r2", "reader", self.verdict("valid", self.label("ours")))
        self.assertEqual((self.names()[-1], self.piece["state"]), ("CRITIC_WIN", "AWAITING_CONFIRMATION"))
        self.ok("swap", "parse")
        self.start("r3", "reader-alt")
        self.stop("r3", "reader-alt", self.verdict("valid", self.label("ours")))
        won, ended = self.events()[-2:]
        self.assertEqual((won["event"], won["model"], self.piece["state"]), ("CONFIRMATION_WIN", "opus", "CONFIRMED"))
        self.assertEqual((ended["event"], ended["reason"]), ("RUN_ENDED", "win"))  # one piece: its win is the whole gate

    def test_lead_tokens_come_from_the_transcript_the_start_hook_names(self):  # A8, FR-13.1
        lead = pathlib.Path(self.base, "lead.jsonl")
        lead.write_text("".join(json.dumps({"message": {"role": "assistant", "usage": {"input_tokens": n, "output_tokens": 10}}}) + "\n"
                                for n in (100, 200)))
        self.green_pair()
        for agent_id, agent_type in (("r1", "reader"), ("r2", "reader-alt")):
            self.hook({"hook_event_name": "SubagentStart", "agent_id": agent_id, "agent_type": agent_type,
                       "transcript_path": str(lead)}, "--start")
            self.stop(agent_id, agent_type, self.verdict("valid", self.label("ours")))
            if agent_type == "reader":
                self.ok("swap", "parse")
        self.assertEqual(self.piece["state"], "CONFIRMED")
        self.assertEqual(ctl.metrics(ctl.read_events(), ctl.load())["lead_tokens_per_confirmed_piece"], 320)

    def test_tokens_count_each_message_once_and_leave_out_cache_reads(self):  # F19: 23.8 million lead tokens in bytesize-3
        path = pathlib.Path(self.base, "t.jsonl")
        usage = {"input_tokens": 5, "cache_creation_input_tokens": 100, "cache_read_input_tokens": 9000, "output_tokens": 20}
        lines = [{"message": {"id": "m1", "role": "assistant", "usage": usage}}] * 3  # one message, three content lines
        lines += [{"message": {"id": "m2", "role": "assistant", "usage": {**usage, "output_tokens": 30}}}]
        lines += [{"message": {"id": "m3", "role": "assistant", "usage": {**usage, "output_tokens": n}}} for n in (7, 400, 1218)]
        path.write_text("".join(json.dumps(line) + "\n" for line in lines))
        # F27: a subagent's message streams over several lines and its usage grows; the last line holds the final count
        self.assertEqual(ctl.transcript_usage(str(path))["tokens"], 125 + 135 + (105 + 1218))

    def test_a_confirmation_attested_from_reader_is_rejected(self):  # AC-17.7, FR-17.13
        self.green_pair()
        self.start("r1", "reader")
        self.stop("r1", "reader", self.verdict("valid", self.label("ours")))
        self.ok("swap", "parse")
        self.start("r2", "reader")
        self.stop("r2", "reader", self.verdict("valid", self.label("ours")))
        self.assertEqual((self.names()[-1], self.piece["state"]), ("VERDICT_INVALID", "AWAITING_CONFIRMATION"))

    def test_unregistered_unknown_and_closed_are_invalid(self):  # AC-17.7
        self.green_pair()
        self.stop("ghost", "reader", self.verdict("valid"))  # never registered by SubagentStart
        self.assertEqual((self.names()[-1], self.events()[-1]["reason"]), ("VERDICT_INVALID", "agent was never registered by the start hook"))
        self.start("r1", "reader")
        self.stop("r1", "reader", self.verdict("valid", pair="parse-r9-beef"))  # an attempt nobody opened
        self.assertEqual((self.names()[-1], self.piece["state"]), ("VERDICT_INVALID", "ACTIVE"))
        self.start("r2", "reader")
        self.stop("r2", "reader", self.verdict("valid", self.label("reference")))
        self.start("r3", "reader")
        self.stop("r3", "reader", self.verdict("valid", self.label("ours")))  # that attempt is closed
        self.assertEqual((self.names()[-1], self.piece["state"]), ("VERDICT_INVALID", "ACTIVE"))

    def test_shape(self):  # FR-NN.3
        for name, reason in (("no-citation", "cites nothing"), ("winner-first", "WINNER before EVIDENCE")):
            self.green_pair() if not os.path.exists(os.path.join(self.root, ".gauntlet/pairs/parse")) else self.ok("pair", "parse")
            self.start(name, "reader")
            self.stop(name, "reader", self.verdict(name))
            invalid = self.events()[-1]
            self.assertEqual(invalid["event"], "VERDICT_INVALID")
            self.assertIn(reason, invalid["reason"])
        self.ok("pair", "parse")
        self.start("hedger", "reader")
        self.stop("hedger", "reader", self.verdict("hedge"))
        self.assertEqual(self.names()[-1], "CRITIC_LOSS")  # no ties: a hedge is a loss

    def test_a_verdict_handed_back_through_the_tool_is_the_verdict(self):  # A1: seen on 2.1.277, S11 overturned
        self.green_pair()
        self.start("r1", "reader")
        chatter = "I've already delivered the verdict through the hand-off, so there is nothing further to add."
        self.stop("r1", "reader", chatter, handback=self.verdict("valid", self.label("ours")))
        self.assertEqual((self.names()[-1], self.piece["state"]), ("CRITIC_WIN", "AWAITING_CONFIRMATION"))
        self.assertIn("EVIDENCE:", pathlib.Path(self.root, ".gauntlet/verdicts/parse-r1-1.md").read_text())

    def test_a_quoted_secret_is_redacted_before_the_verdict_is_filed(self):  # FR-15.4
        self.green_pair()
        self.start("r1", "reader")
        self.stop("r1", "reader", self.verdict("secret", self.label("reference")))
        filed = pathlib.Path(self.root, ".gauntlet/verdicts/parse-r1-1.md").read_text()
        self.assertEqual(("sk-fixture" in filed, "[redacted]" in filed), (False, True))

    def test_a_forged_attestation_collides_with_the_genuine_stop(self):  # AC-17.8, Tier 2
        self.green_pair()
        self.start("r1", "reader")
        self.stop("r1", "reader", self.verdict("valid", self.label("ours")))  # forged by the lead while r1 still runs
        self.assertEqual(self.piece["state"], "AWAITING_CONFIRMATION")
        self.ok("swap", "parse")
        self.stop("r1", "reader", self.verdict("valid", self.label("reference")))  # the genuine stop fires
        conflict = self.events()[-1]
        state = ctl.load()
        self.assertEqual((conflict["event"], state["pieces"]["parse"]["state"]), ("ATTEST_CONFLICT", "ACTIVE"))
        self.assertTrue({e["seq"] for e in self.events() if e["event"] in ("CRITIC_RESULT", "CRITIC_WIN")} <= set(state["voided"]))
        self.assertEqual(state["conflicts"][0]["agent_id"], "r1")
        # The forged result, its win and the swap that followed are out of the fold; the first attempt is void.
        self.assertEqual([a["status"] for a in state["attempts"].values()], ["void"])
        self.start("r9", "reader-alt")
        self.stop("r9", "reader-alt", self.verdict("valid", self.label("ours")))  # the confirmation pair is tainted too
        self.assertEqual((self.names()[-1], self.piece["state"]), ("VERDICT_INVALID", "ACTIVE"))
        self.ok("report")  # the report lists the conflict first
        text = pathlib.Path(self.root, ".gauntlet/report.md").read_text()
        self.assertLess(text.index("## Attestation conflicts"), text.index("## Parked"))
        self.assertIn("two attestations for agent r1", text)


class TierOne(AttestRepo):
    tier1 = True

    def test_the_first_registration_makes_the_key_outside_the_sandbox(self):  # F9
        key = os.path.join(self.root, ".gauntlet/private/attest.key")
        self.assertFalse(os.path.exists(key))  # init runs in the lead's sandbox, where the key is masked
        self.start("b1", "editor")
        self.assertEqual(oct(os.stat(key).st_mode & 0o777), oct(0o600))
        first = pathlib.Path(key).read_text()
        self.start("b2", "editor")
        self.assertEqual(pathlib.Path(key).read_text(), first)  # made once, never replaced

    def test_a_payload_without_the_key_is_refused_outright(self):  # AC-17.8, Tier 1
        self.green_pair()
        self.start("r1", "reader")
        before = len(self.events())
        code, _, err = self.stop("r1", "reader", self.verdict("valid", self.label("ours")), key=False)
        self.assertEqual((code, len(self.events())), (3, before))
        self.stop("r1", "reader", self.verdict("valid", self.label("ours")))
        self.assertEqual(self.names()[-1], "CRITIC_WIN")


class Usage(AttestRepo):
    """What each agent spent, recorded when it stops, so a run says how close a role came to its maxTurns."""

    def transcript(self, name, turns):
        path = pathlib.Path(self.base, f"{name}.jsonl")
        path.write_text("".join(json.dumps({"message": {"id": f"m{i}", "role": "assistant", "usage": {"input_tokens": 10, "output_tokens": 5}}}) + "\n"
                                for i in range(turns)))
        return str(path)

    def stopped(self, agent_id, agent_type, turns, message=""):
        self.start(agent_id, agent_type)
        self.hook({"hook_event_name": "SubagentStop", "agent_id": agent_id, "agent_type": agent_type,
                   "last_assistant_message": message, "agent_transcript_path": self.transcript(agent_id, turns)})

    def test_an_author_is_recorded_when_it_stops(self):  # F37: units and units-2 recorded no author, so metrics left out its spend
        self.stopped("w1", "author", 27)
        done = self.events()[-1]
        self.assertEqual((done["event"], done["agent_type"], done["tokens"], done["turns"]), ("AUTHOR_DONE", "author", 405, 27))
        self.assertEqual(self.piece["round"], 0)  # an author moves no piece

    def test_metrics_name_the_most_turns_per_role_and_the_agents_that_never_stopped(self):  # maxTurns review, 2026-09-24
        self.stopped("w1", "author", 27)
        self.stopped("b1", "editor", 15, ".gauntlet/wt/parse")
        self.assertEqual(self.events()[-1]["turns"], 15)
        self.start("r1", "reader")  # an agent at its maxTurns fires no stop hook (S3), nor does one cut off
        m = ctl.metrics(ctl.read_events(), ctl.load())
        self.assertEqual((m["most_turns_by_role"], m["agents_that_never_stopped"]), ({"author": 27, "editor": 15}, 1))


class Editors(AttestRepo):
    def test_a_builder_is_attested_across_two_rounds_on_one_agent_id(self):  # A6, S12
        self.built()
        self.assertEqual((self.names()[-1], self.piece["round"], self.piece["building"]), ("BUILDER_DONE", 1, False))
        before = len(self.events())
        self.stop("b1", "editor", ".gauntlet/wt/parse")  # a stop with no open attempt is a note, never a conflict
        self.assertEqual(len(self.events()), before)
        self.ok("event", "GAP_ROUTED", "piece=parse", "class=artifact")
        self.built()  # resumed with the same agent id: the start and stop hooks fire again
        self.assertEqual((self.names()[-1], self.piece["round"]), ("BUILDER_DONE", 2))

    def test_blocked_parks_and_not_reproduced_waits_for_the_rerun(self):  # FR-3.4, FR-5.3
        self.built("NOT REPRODUCED: `node run.mjs b abc` -> throws invalid duration")
        done = self.events()[-1]
        self.assertEqual((done["event"], done["returned"], self.piece["round"]), ("BUILDER_DONE", "not-reproduced", 0))
        self.ok("event", "GAP_ROUTED", "piece=parse", "class=artifact")
        self.built("BLOCKED: the fix needs a migration")
        self.assertEqual((self.names()[-2:], self.piece["state"]), (["PIECE_PARKED", "RUN_ENDED"], "PARKED"))
        self.assertIn("migration", ctl.load()["parked"][0]["reason"])

    def test_a_builder_that_hands_back_blocked_parks(self):  # A1: the bytesize parse builder, 2026-09-19
        self.start("b1", "editor")
        self.stop("b1", "editor", "I've already delivered the hand-off, so there is nothing further I can request.",
                  handback="BLOCKED: the permission layer refused to run the required suite")
        self.assertEqual((self.names()[-2:], self.piece["state"]), (["PIECE_PARKED", "RUN_ENDED"], "PARKED"))
