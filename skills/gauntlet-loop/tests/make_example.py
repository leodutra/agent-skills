#!/usr/bin/env python3
"""Regenerate tests/fixtures/example-events.jsonl: the run told in references/example-run.md, played through the real
machine in memory on a scripted clock. Run it after a change to the machine, then update the document's status lines:
test_example.py fails until the two agree. Prints each turn's status line."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _util import SKILL, ctl  # noqa: E402

POLICY = ctl.policy()


class Run:
    def __init__(self):
        self.tx, self.clock, self.n = ctl.Tx([]), 1_789_000_000, 0

    def tick(self, minutes):
        self.clock += int(minutes * 60)

    def emit(self, name, kind="fact", source="controller", minutes=1, **fields):
        self.tick(minutes)
        real, ctl.now = ctl.now, lambda: ctl.time.strftime("%Y-%m-%dT%H:%M:%SZ", ctl.time.gmtime(self.clock))
        try:
            return self.tx.emit(name, kind, source, **fields)
        finally:
            ctl.now = real

    def judge(self, name, **fields):
        cost = {"GAP_ROUTED": 1, "VARIANT_APPROACHES_SELECTED": 2}.get(name)
        return self.emit(name, "judgment", "event", actor="lead", cost=cost, **fields)

    def open(self, pid, **kw):
        self.emit("PIECE_OPENED", source="piece", piece=pid, worktree=f".gauntlet/wt/{pid}", cost=1,
                  allocation=kw.pop("allocation", ctl.allocation_for(self.tx.state)), **kw)

    def built(self, pid, agent, minutes=14, returned=None, note=None):
        self.emit("AGENT_REGISTERED", source="attest", agent_id=agent, agent_type="editor")
        self.emit("BUILDER_DONE", source="attest", minutes=minutes, piece=pid, agent_id=agent, agent_type="editor",
                  artifact=None if returned else f".gauntlet/wt/{pid}", returned=returned, note=note, tokens=41_000)

    def floors(self, pid, failed=None):
        rnd = self.tx.state["pieces"][pid]["round"]
        if failed:
            self.emit("FLOOR_FAIL", source="floors", piece=pid, artifact=f".gauntlet/floors/{pid}/r{rnd}", note=failed, **{"class": "artifact"})
        else:
            self.emit("FLOOR_PASS", source="floors", piece=pid, artifact=f".gauntlet/floors/{pid}/r{rnd}")

    def verdict(self, pid, order, winner=None, gap=None, shape="pairwise", valid=True, reason=None, suffix=""):
        rnd = self.tx.state["pieces"][pid]["round"]
        pair = f"{pid}-r{rnd}-{ctl.hashlib.sha256(f'{pid}{rnd}{order}{shape}'.encode()).hexdigest()[:4]}"
        tries = sum(a["pair"] == pair for a in self.tx.state["attempts"].values()) + 1
        agent_type = "reader-alt" if order == "swapped" else "reader"
        self.n += 1
        agent = f"r{self.n:02d}"
        self.emit("CRITIC_DISPATCHED", source="swap" if order == "swapped" else "pair", piece=pid, attempt_id=f"{pair}#{tries}",
                  pair_id=pair, shape=shape, order=order, expected_type=agent_type, cost=1)
        self.emit("AGENT_REGISTERED", source="attest", agent_id=agent, agent_type=agent_type)
        n = 2 if order == "swapped" else 1
        self.emit("CRITIC_RESULT", source="attest", minutes=6, piece=pid, attempt_id=f"{pair}#{tries}", agent_id=agent,
                  agent_type=agent_type, model=self.tx.state["readers"][agent_type], valid=valid, reason=reason, winner=winner,
                  gap=gap, shape=shape, artifact=f".gauntlet/verdicts/{pid}-r{rnd}-{n}{suffix}.md", tokens=18_000)

    def win(self, pid):
        self.verdict(pid, "first", "ours")
        self.emit("RERUN_OBSERVED", source="rerun", piece=pid, note="one cited command, rerun on the win", exit=0,
                  artifact=f".gauntlet/floors/{pid}/rerun.txt")
        self.verdict(pid, "swapped", "ours")

    def turn(self, label):
        line = self.emit("LEAD_TURN", source="status", minutes=2, note=label)
        print(f"{label:<28} {ctl.status_line(self.tx.state, at=line['ts'])}")


def main():
    r = Run()
    # Turn 1: round zero.
    r.emit("RUN_STARTED", source="init", run="g-20260918-d41c07", policy="v1", tier=2, attestation="tier-1",
           containment={"sandbox": True, "strict": True, "network": True, "credentials": True},
           readers=POLICY["confirmation"], envelope={"E": 150, "T_hours": 24}, envelope_policy=POLICY["envelope"],
           lease_hours=POLICY["lease_hours"], goal="a duration library for TypeScript",
           bar="A TypeScript duration library that parses and formats like vercel/ms 2.1.3 and beats it on a blind read; floor: "
               "ported ms suite green, held-out green, hostile script exits 0, 1e6 parses under 500 ms; never add a runtime dependency.",
           critic_bar="A TypeScript duration library: parse strings like \"2h 30m\" to milliseconds and format back, short and long "
                      "form; floor: each thrown error names the bad input; the code handles the case, not the literal test input.",
           invariants=["never add a runtime dependency"])
    r.emit("REFERENCE_FROZEN", source="freeze", artifact="reference/ms", note="https://github.com/vercel/ms")
    r.emit("REFERENCE_VERIFIED", source="freeze-verify", minutes=3, artifact="reference/ms", note="sandbox, strict, network allowlist")
    r.judge("SPLIT_DECIDED", pieces="3")
    r.emit("AGENT_REGISTERED", source="attest", agent_id="au01", agent_type="author", cost=1)
    for fid, cmd, derived in (("required", "node --test tests/required/", None), ("heldout", "node --test heldout/", True),
                              ("hostile", "node heldout/hostile.mjs", True), ("bench", "node bench/parse.mjs --max-ms 500", None),
                              ("no-deps", "node bench/no-deps.mjs", True)):
        r.emit("FLOOR_ADDED", source="floor", floor=fid, cmd=cmd, derived=derived)
    r.open("parse", referent="reference/ms/parse")
    r.open("format", referent="reference/ms/format")
    r.open("locale", referent="reference/ms/format", mode="champion-challenger")
    r.emit("PLAN_COMMITTED", source="commit")
    r.turn("1 round zero")
    # Turn 2: a red floor, and a piece blocked on a missing tool.
    r.built("parse", "a1f3")
    r.floors("parse", failed="heldout")
    r.judge("GAP_ROUTED", piece="parse", gap="FLOOR held-out 9/12", **{"class": "artifact"})
    r.judge("BLOCK_REQUESTED", piece="locale", reason="the locale floor needs full ICU data and this Node build has none")
    r.turn("2 a red floor")
    # Turn 3: the first pair.
    r.built("format", "7c02")
    r.floors("format")
    r.verdict("format", "first", "reference", gap="B prints fractional units (1.5h, 1.5 hours) in an output that is whole-unit everywhere else")
    r.emit("AGENT_REGISTERED", source="attest", agent_id="au02", agent_type="author", cost=1)
    r.emit("FLOOR_ADDED", source="floor", floor="heldout-whole-units", cmd="node --test heldout/whole-units.test.mjs", derived=True,
           for_piece="format", artifact="heldout/whole-units.test.mjs")
    r.judge("GAP_ROUTED", piece="format", gap="prints fractional units (1.5h) where the rest of the output is whole-unit", **{"class": "artifact"})
    r.judge("BLOCKER_CLEARED", piece="locale", note="full-icu installed in the lead's environment")
    r.turn("3 a loss, a finding, a floor")
    # Turn 4: a discarded verdict; the resumed builder's second round.
    r.built("parse", "a1f3", minutes=9)
    r.floors("parse")
    r.verdict("parse", "first", valid=False, reason="WINNER before EVIDENCE")
    r.built("locale", "c55d")
    r.floors("locale")  # the first green attempt is the champion, unjudged
    r.judge("GAP_ROUTED", piece="locale", gap="the champion stands; move it closer to the referent", **{"class": "artifact"})
    r.turn("4 a discarded verdict")
    # Turn 5: parse wins and is confirmed; format's builder says NOT REPRODUCED and is right.
    r.verdict("parse", "first", "ours", suffix=".2")
    r.emit("RERUN_OBSERVED", source="rerun", piece="parse", note="node run.mjs b parse 1.5.5h", exit=1, artifact=".gauntlet/floors/parse/rerun-1.txt")
    r.verdict("parse", "swapped", "ours")
    r.built("format", "7c02", minutes=11)
    r.floors("format")
    r.verdict("format", "first", "reference", gap="B returns undefined for \"1.5.5h\" instead of throwing")
    r.judge("GAP_ROUTED", piece="format", gap="returns undefined for 1.5.5h instead of throwing", **{"class": "artifact"})
    r.built("format", "7c02", minutes=3, returned="not-reproduced", note="NOT REPRODUCED: `node run.mjs b format 1.5.5h` -> throws invalid duration: \"1.5.5h\"")
    seq = r.emit("RERUN_OBSERVED", source="rerun", piece="format", note="node run.mjs b format 1.5.5h", exit=1,
                 artifact=".gauntlet/floors/format/rerun-2.txt")["seq"]
    r.judge("NOT_REPRODUCED_ACCEPTED", piece="format", rerun=seq)
    r.turn("5 a win, a NOT REPRODUCED")
    # Turn 6: format wins, loses its confirmation, then repeats a gap and is split. locale's challenger replaces the champion.
    r.verdict("format", "first", "ours", suffix=".2")
    r.verdict("format", "swapped", "reference", gap="B's long form says \"2 hour\"; A pluralises")
    r.judge("GAP_ROUTED", piece="format", gap="long form says \"2 hour\"", **{"class": "artifact"})
    r.built("locale", "c55d", minutes=12)
    r.floors("locale")
    r.win("locale")  # CHAMPION_REPLACED
    r.judge("GAP_ROUTED", piece="locale", gap="the new champion stands; move it closer", **{"class": "artifact"})
    r.built("format", "7c02", minutes=10)
    r.floors("format")
    r.verdict("format", "first", "reference", gap="long form prints \"1 days\"")
    r.judge("GAP_SAME_AS_LAST", piece="format")
    share = max(r.tx.state["pieces"]["format"]["allocation"] - r.tx.state["pieces"]["format"]["spent"], 0) // 2
    r.open("format-short", referent="reference/ms/format", parent="format", rung=1, allocation=share)
    r.open("format-long", referent="reference/ms/format", parent="format", rung=1, allocation=share)
    r.turn("6 a lost confirmation, a split")
    # Turn 7, after compaction: status --full, then work. format-long's builder is blocked and the piece parks.
    r.turn("7 after compaction")
    r.built("format-short", "d2e8", minutes=8)
    r.floors("format-short")
    r.win("format-short")
    r.built("format-long", "e9a1", minutes=5, returned="blocked", note="BLOCKED: pluralisation wants the intl-pluralrules package; installs are outside my directory's rules")
    for _ in range(2):  # two challenger losses in a row
        r.built("locale", "c55d", minutes=9)
        r.floors("locale")
        r.verdict("locale", "first", "reference", gap="the challenger drops the narrow no-break space French needs")
        r.judge("GAP_ROUTED", piece="locale", gap="drops the narrow no-break space French needs", **{"class": "artifact"})
    r.turn("7 a parked piece")
    # Turn 8: a human resumes the parked piece; locale converges.
    r.emit("HUMAN_RESUMED", source="resume", piece="format-long", actor="leo")
    r.judge("GAP_ROUTED", piece="format-long", gap="Node 22 ships Intl.PluralRules; no package is needed", **{"class": "execution"})
    r.built("locale", "c55d", minutes=1, returned="not-reproduced", note="NOT REPRODUCED: the champion already emits U+202F")
    r.verdict("locale", "first", shape="gap-only", gap=None)
    r.verdict("locale", "swapped", shape="gap-only", gap=None)  # CONVERGED
    r.built("format-long", "e9a1", minutes=12)
    r.floors("format-long")
    r.win("format-long")
    r.turn("8 a resume, a convergence")
    # Turn 9: the wave, then the gate: lost once on coherence, and a scope failure filed beside it.
    r.judge("SHARED_EDGE_RECORDED", pieces="format-short,format-long")
    r.emit("AGENT_REGISTERED", source="attest", agent_id="s001", agent_type="editor-fast", cost=1)
    r.emit("SMOOTHER_DONE", source="attest", minutes=7, agent_id="s001", agent_type="editor-fast", note="wave-1", tokens=22_000)
    for pid in ("parse", "format-short", "format-long", "locale"):
        r.floors(pid)
        r.emit("WAVE_COMPLETE", source="wave", piece=pid, artifact="3f9c2ab")
    r.open("whole", piece_kind="whole", referent="reference/ms", allocation=0)
    r.floors("whole")
    r.verdict("whole", "first", "reference", gap="B documents parse and format as two imports; A is one function that does both")
    r.judge("SCOPE_FAILURE_FILED", note="The goal said \"format milliseconds back, short and long form\". The whole gate showed the long "
            "form's language is unspecified: ours follows the system locale, the reference is English only. The goal should have "
            "said which locales the long form must support, or that English alone is the bar.")
    r.open("coherence", piece_kind="coherence", referent="reference/ms", allocation=ctl.allocation_for(r.tx.state) // 3)
    r.turn("9 the gate, lost")
    # Turn 10: coherence wins; the gate again; the whole wins.
    r.built("coherence", "b9e0", minutes=13)
    r.floors("coherence")
    r.win("coherence")
    r.floors("coherence")
    r.emit("WAVE_COMPLETE", source="wave", piece="coherence", artifact="a81d07e")
    r.emit("AGENT_REGISTERED", source="attest", agent_id="s002", agent_type="editor-fast", cost=1)
    r.emit("SMOOTHER_DONE", source="attest", minutes=5, piece="whole", agent_id="s002", agent_type="editor-fast", note="whole", tokens=19_000)
    r.floors("whole")
    r.win("whole")  # RUN_ENDED win
    r.turn("10 the whole wins")
    # Turn 11: report, commit, promote.
    r.emit("ARTIFACTS_COMMITTED", source="commit")
    r.emit("PR_OPENED", source="promote", artifact="https://github.com/example/durations/pull/12")
    r.turn("11 commit, promote")
    # Later: a human approved and merged; status read it from the remote.
    for pid in ("parse", "format-short", "format-long", "locale", "coherence"):
        r.emit("PR_MERGED", source="status", minutes=90 if pid == "parse" else 0, piece=pid, artifact="https://github.com/example/durations/pull/12")
    r.turn("12 merged")

    out = os.path.join(SKILL, "tests", "fixtures", "example-events.jsonl")
    with open(out, "w") as f:
        f.writelines(json.dumps(e) + "\n" for e in r.tx.new)
    state = r.tx.state
    print(f"\n{len(r.tx.new)} events -> {os.path.relpath(out, SKILL)}")
    print("by class:", ctl.metrics(r.tx.new, state)["by_class"])
    if "--metrics" in sys.argv:
        print("\n".join(ctl.metric_lines(ctl.metrics(r.tx.new, state))))
    if "--workbench" in sys.argv:
        print(ctl.render_workbench(state))


if __name__ == "__main__":
    main()
