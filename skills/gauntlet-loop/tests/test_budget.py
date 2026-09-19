"""The envelope is escrow the controller owns: three accounts, per-piece allocation, a ceiling that counts and never grades."""
import unittest

from _util import Repo, ctl

POLICY = ctl.policy()


class Sim:
    def __init__(self, pieces, envelope={"E": 150, "T_hours": 24}):
        self.tx, self.clock = ctl.Tx([]), 0
        self.fact("RUN_STARTED", run="g-test", policy="v1", tier=2, containment={}, attestation="tier-2",
                  readers={"reader": "fable", "reader-alt": "opus"}, envelope=envelope,
                  envelope_policy=POLICY["envelope"], lease_hours=POLICY["lease_hours"])
        self.fact("REFERENCE_FROZEN", artifact="reference/ms")
        self.tx.emit("SPLIT_DECIDED", "judgment", "event", pieces=len(pieces))
        for pid in pieces:
            self.open(pid)

    def fact(self, name, **fields):
        self.clock += 60
        now, ctl.now = ctl.now, lambda: ctl.time.strftime("%Y-%m-%dT%H:%M:%SZ", ctl.time.gmtime(1_800_000_000 + self.clock))
        try:
            return self.tx.emit(name, "fact", "test", **fields)
        finally:
            ctl.now = now

    def open(self, pid, kind="piece"):
        self.fact("PIECE_OPENED", piece=pid, piece_kind=kind, referent="reference/ms", cost=1,
                  allocation=ctl.allocation_for(self.tx.state))

    def lose(self, pid):
        """One round against an unreachable bar, stepped the way a lead steps it: never past a park or the end."""
        n = len(self.tx.new)
        steps = [lambda: self.fact("BUILDER_DONE", piece=pid, artifact="x"),
                 lambda: self.fact("FLOOR_PASS", piece=pid),
                 lambda: ctl.afford(self.tx, pid) and self.fact("CRITIC_DISPATCHED", piece=pid, attempt_id=f"a{n}", pair_id=f"a{n}",
                                                                shape="pairwise", order="first", expected_type="reader", cost=1),
                 lambda: self.fact("CRITIC_RESULT", piece=pid, attempt_id=f"a{n}", agent_type="reader", valid=True, model="fable",
                                   winner="reference", gap=f"gap {n}"),
                 lambda: ctl.afford(self.tx, pid) and self.tx.emit("GAP_ROUTED", "judgment", "event", piece=pid, cost=1, **{"class": "artifact"})]
        for step in steps:
            if self.run["ended"] or self.tx.state["pieces"][pid]["state"] != "ACTIVE":
                return
            step()

    def win(self, pid):
        self.fact("BUILDER_DONE", piece=pid, artifact="x")
        self.fact("FLOOR_PASS", piece=pid)
        for order, agent in (("first", "reader"), ("swapped", "reader-alt")):
            n = len(self.tx.new)
            self.fact("CRITIC_DISPATCHED", piece=pid, attempt_id=f"a{n}", pair_id=f"a{n}", shape="pairwise", order=order, expected_type=agent, cost=1)
            self.fact("CRITIC_RESULT", piece=pid, attempt_id=f"a{n}", agent_type=agent, valid=True, model=self.tx.state["readers"][agent], winner="ours")

    run = property(lambda self: self.tx.state["run"])
    names = property(lambda self: [e["event"] for e in self.tx.new])


class Budget(unittest.TestCase):
    def test_three_accounts_and_an_equal_allocation_per_piece(self):
        sim = Sim(["parse", "format"])
        self.assertEqual(sim.run["accounts"], {"local": 90, "escalation": 37, "gate": 23})
        self.assertEqual([p["allocation"] for p in sim.tx.state["pieces"].values()], [45, 45])

    def test_the_default_envelope_comes_from_the_piece_count(self):  # FR-14.1, C7
        sim = Sim(["a", "b", "c"], envelope=None)
        self.assertEqual(sim.run["envelope"], {"E": 50, "T_hours": 4})  # ceil(3 * 10 / 0.60); max(4, 3 * 1)

    def test_a_piece_pays_local_then_the_reserve_and_never_the_gate(self):  # FR-14.4, FR-17.6
        sim = Sim(["parse", "format"], envelope={"E": 20, "T_hours": 24})  # local 12, escalation 5, gate 3: 6 a piece
        sim.lose("parse")
        sim.lose("parse")
        self.assertEqual((sim.tx.state["pieces"]["parse"]["spent"], sim.run["spent"]), (5, {"local": 6, "escalation": 0, "gate": 0}))
        sim.lose("parse")  # crosses its allocation of 6
        self.assertIn("ALLOCATION_SPENT", sim.names)
        self.assertEqual(sim.names.count("ALLOCATION_SPENT"), 1)
        self.assertEqual((sim.tx.state["pieces"]["parse"]["rung"], sim.run["spent"]["gate"]), (1, 0))
        self.assertEqual(sim.tx.state["escalations"][0]["trigger"], "spend")

    def test_an_unreachable_bar_ends_on_its_own_with_the_gate_reserve_untouched(self):  # AC-14.3
        sim = Sim(["parse", "format"], envelope=None)  # no named budget
        for _ in range(200):
            active = [pid for pid, p in sim.tx.state["pieces"].items() if p["state"] == "ACTIVE"]
            if sim.run["ended"] or not active:
                break
            sim.lose(active[0])
        self.assertEqual(sim.run["ended"], "ceiling")
        self.assertEqual(sim.names[-1], "RUN_ENDED")
        self.assertEqual(sim.run["spent"]["gate"], 0)
        self.assertLessEqual(sim.run["spent"]["escalation"], sim.run["accounts"]["escalation"])
        self.assertEqual({p["state"] for p in sim.tx.state["pieces"].values()}, {"PARKED"})
        with self.assertRaises(ctl.Rejected):  # the run is over: no more work is opened
            sim.open("late")

    def test_the_clock_is_a_ceiling_too(self):
        sim = Sim(["parse"], envelope={"E": 150, "T_hours": 0.05})  # three minutes
        sim.lose("parse")
        self.assertEqual((sim.run["ended"], "BUDGET_EXHAUSTED" in sim.names), ("ceiling", True))

    def test_the_whole_pays_from_the_gate_reserve_and_a_win_ends_the_run(self):
        sim = Sim(["parse", "format"])
        sim.win("parse")
        sim.win("format")
        self.assertIsNone(sim.run["ended"])
        sim.open("whole", kind="whole")
        sim.win("whole")
        self.assertEqual((sim.run["ended"], sim.run["spent"]["gate"]), ("win", 3))

    def test_every_remaining_piece_parked_is_nothing_left(self):
        sim = Sim(["parse", "format"])
        sim.win("parse")
        sim.tx.emit("PARK_REQUESTED", "judgment", "event", piece="format", reason="needs a migration", **{"class": "execution"})
        self.assertEqual(sim.run["ended"], "nothing-left")

    def test_a_voided_dispatch_still_cost_what_it_cost(self):
        sim = Sim(["parse"])
        sim.fact("BUILDER_DONE", piece="parse", artifact="x")
        sim.fact("FLOOR_PASS", piece="parse")
        seq = sim.fact("CRITIC_DISPATCHED", piece="parse", attempt_id="a", pair_id="a", shape="pairwise", order="first", expected_type="reader", cost=1)["seq"]
        sim.fact("ATTEST_CONFLICT", piece="parse", voids=[seq], agent_id="r1")
        self.assertEqual(sim.run["spent"]["local"], 2)  # the open and the voided dispatch


class Leases(Repo):
    installed = True

    def test_an_expired_lease_blocks_the_piece_for_resume_or_parking(self):  # FR-17.7
        self.ok("init", "--invocations", "150", "--hours", "24")
        self.write("upstream/index.js")
        self.ok("freeze", self.root + "/upstream", self.root + "/reference/ms")
        self.ok("event", "SPLIT_DECIDED", "pieces=2")
        self.ok("piece", "open", "parse", "--referent", "reference/ms")
        state = ctl.load()
        self.assertEqual(state["pieces"]["parse"]["allocation"], 45)
        self.assertEqual(state["pieces"]["parse"]["lease"]["attempt"], "build")
        now = ctl.now
        later = ctl.epoch(state["run"]["started"]) + 3 * 3600  # past the two-hour lease, inside the envelope
        ctl.now = lambda: ctl.time.strftime("%Y-%m-%dT%H:%M:%SZ", ctl.time.gmtime(later))
        self.addCleanup(setattr, ctl, "now", now)
        ctl.expire_leases()
        self.assertEqual((self.names()[-1], ctl.load()["pieces"]["parse"]["state"]), ("LEASE_EXPIRED", "BLOCKED"))
