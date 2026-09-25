"""pair and swap: seeded, idempotent, blind on disk, and refusing secrets and loop traces."""
import filecmp
import json
import os
import pathlib
import shutil
import subprocess

from _util import Repo, ctl


def tree(path):
    out = {}
    for folder, _, files in os.walk(path):
        for name in files:
            full = os.path.join(folder, name)
            out[os.path.relpath(full, path)] = pathlib.Path(full).read_bytes()
    return out


class PairRepo(Repo):
    installed = True
    mode = []

    def setUp(self):
        super().setUp()
        self.ok("init", "--invocations", "150", "--hours", "24")
        self.write("upstream/index.js", "export const parse = () => 1\n")
        self.ok("freeze", os.path.join(self.root, "upstream"), os.path.join(self.root, "reference/ms"))
        self.write(".gauntlet/staging/prompt.md", "The bar: a duration parser.\nOn each side: run node run.mjs.\nReading floors: errors name the input.\n")
        self.ok("event", "SPLIT_DECIDED", "pieces=1")
        self.ok("piece", "open", "parse", "--referent", "reference/ms", *self.mode)
        self.ok("pair", "parse", "--prepare", "--reference", "reference/ms", "--prompt", ".gauntlet/staging/prompt.md")
        self.round("export const parse = () => 2\n")

    def round(self, source):
        self.write(".gauntlet/wt/parse/src/parse.js", source)
        self.write(".gauntlet/wt/parse/node_modules/dep/index.js")
        with ctl.transaction() as tx:
            tx.emit("BUILDER_DONE", "fact", "test", piece="parse", artifact=".gauntlet/wt/parse")
            tx.emit("FLOOR_PASS", "fact", "test", piece="parse")

    def result(self, winner=None, agent_type="reader", gap=None):
        state = ctl.load()
        attempt = next(k for k, a in state["attempts"].items() if a["status"] == "open")
        with ctl.transaction() as tx:
            tx.emit("CRITIC_RESULT", "fact", "test", piece="parse", attempt_id=attempt, agent_type=agent_type, valid=True,
                    model=state["readers"][agent_type], winner=winner, gap=gap)

    def mapping(self, name):
        return json.loads(pathlib.Path(self.root, ".gauntlet/private/mapping", name + ".json").read_text())

    pair_dir = property(lambda self: os.path.join(self.root, ".gauntlet/pairs/parse"))


class Pair(PairRepo):
    def test_twice_gives_identical_trees_mapping_and_one_attempt(self):  # AC-17.5
        self.ok("pair", "parse")
        first, pair_id = tree(self.pair_dir), pathlib.Path(self.pair_dir, "PAIR_ID").read_text().strip()
        first_map = self.mapping(pair_id)
        shutil.rmtree(self.pair_dir)
        self.ok("pair", "parse")
        self.assertEqual((tree(self.pair_dir), self.mapping(pair_id)), (first, first_map))
        self.assertEqual(self.names().count("CRITIC_DISPATCHED"), 1)

    def test_the_pair_says_nothing_about_which_side_is_ours(self):
        self.ok("pair", "parse")
        files = tree(self.pair_dir)
        self.assertEqual(sorted({p.split(os.sep)[0] for p in files}), ["PAIR_ID", "PROMPT.md", "a", "b"])
        self.assertFalse([p for p in files if "node_modules" in p or "MANIFEST" in p or ".git" in p])
        text = b"\n".join(files.values()).decode()
        for word in ("ours", "reference", "upstream", "vercel", "gauntlet/parse"):
            self.assertNotIn(word, text)
        sides = self.mapping(pathlib.Path(self.pair_dir, "PAIR_ID").read_text().strip())
        self.assertEqual(sorted([sides["a"], sides["b"]]), ["ours", "reference"])

    def test_refuses_a_tree_with_an_env_file_or_a_secret(self):  # AC-15.2
        self.write(".gauntlet/wt/parse/.env", "TOKEN=abc\n")
        code, _, err = self.run_ctl("pair", "parse")
        self.assertEqual((code, ".env" in err), (3, True))
        os.remove(os.path.join(self.root, ".gauntlet/wt/parse/.env"))
        self.write(".gauntlet/wt/parse/src/config.js", "const api_key = 'sk-fixture-0123456789abcdef0123'\n")
        self.assertEqual(self.run_ctl("pair", "parse")[0], 3)
        self.assertFalse(os.path.exists(self.pair_dir))

    def test_refuses_a_trace_of_the_loop_inside_the_artifact(self):  # FR-NN.8
        self.write(".gauntlet/wt/parse/src/parse.js", "// round 3: fixed what the critic's gap named\nexport const parse = () => 2\n")
        code, _, err = self.run_ctl("pair", "parse")
        self.assertEqual((code, "parse.js:1" in err), (3, True))

    def test_history_is_stripped_and_a_trace_in_a_filename_is_refused(self):  # plan 9c as amended (A13)
        wt = os.path.join(self.root, ".gauntlet/wt/parse")
        self.write(".gauntlet/wt/parse/CLAUDE.md", "gauntlet round 2: ours is the challenger\n")
        for argv in (["add", "-A"], ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "round 2: close the critic's gap"]):
            subprocess.run(["git", "-C", wt, *argv], check=True, capture_output=True)
        self.ok("pair", "parse")  # what is not the deliverable is left out, so its traces refuse nothing
        text = b"\n".join(tree(self.pair_dir).values()).decode()
        self.assertFalse([w for w in ("round 2", "critic's gap", "challenger") if w in text])
        self.write(".gauntlet/wt/parse/src/parse-final.js", "export const parse = () => 2\n")
        code, _, err = self.run_ctl("pair", "parse")  # inside the deliverable: a rename in the copy would break what imports it
        self.assertEqual((code, "parse-final.js: the filename" in err, "rename it in the artifact" in err), (3, True, True))

    def test_floor_outputs_enter_a_pair_on_both_sides_or_on_neither_and_name_no_side(self):  # FR-1.x: blind on disk
        self.ok("floor", "add", "heldout", "--cmd", "echo checked $GAUNTLET_OURS && echo in $GAUNTLET_PIECE", "--derived")
        self.ok("floors", "parse")
        self.ok("pair", "parse")
        self.assertFalse([p for p in tree(self.pair_dir) if "FLOORS" in p])  # the reference was never verified: a one-sided file says which side is ours
        shutil.rmtree(self.pair_dir)
        self.write("reference/ms/.verify/01.txt", f"$ npm test\nexit 0\nok {self.root}/reference/ms/test.js\n")
        self.ok("pair", "parse", "--prepare", "--reference", "reference/ms", "--prompt", ".gauntlet/staging/prompt.md")
        self.ok("pair", "parse")
        files = tree(self.pair_dir)
        self.assertEqual(sorted(p for p in files if "FLOORS" in p), ["a/FLOORS/01.txt", "b/FLOORS/01.txt"])  # one naming scheme
        text = b"\n".join(v for k, v in files.items() if "FLOORS" in k).decode()
        for tell in ("GAUNTLET", "wt/parse", "reference/ms", self.root, "heldout.txt"):
            self.assertNotIn(tell, text)
        self.assertIn("checked .", text)

    def test_a_critic_executes_nothing_unless_the_reference_was_verified(self):  # A3, FR-15.7
        self.ok("pair", "parse")
        self.assertIn(ctl.READ_ONLY_LINE, pathlib.Path(self.pair_dir, "PROMPT.md").read_text())
        self.result("ours")
        self.ok("swap", "parse")  # the confirming critic reads the same line
        self.assertIn(ctl.READ_ONLY_LINE, pathlib.Path(self.pair_dir, "PROMPT.md").read_text())

    def test_a_referent_over_verified_copies_counts_as_verified(self):  # F35: units-2's whole gate read only
        self.write("upstream2/index.js", "export const format = () => 1\n")
        self.ok("freeze", os.path.join(self.root, "upstream2"), os.path.join(self.root, "reference/other"))
        with ctl.transaction() as tx:
            tx.emit("REFERENCE_VERIFIED", "fact", "test", artifact="reference/ms")
        self.ok("piece", "open", "whole", "--referent", "reference", "--kind", "whole")
        self.ok("pair", "whole", "--prepare", "--reference", "reference", "--prompt", ".gauntlet/staging/prompt.md")
        with ctl.transaction() as tx:
            tx.emit("FLOOR_PASS", "fact", "test", piece="whole")
        self.ok("pair", "whole")
        self.assertIn(ctl.READ_ONLY_LINE, pathlib.Path(self.root, ".gauntlet/pairs/whole/PROMPT.md").read_text())  # one copy unverified
        with ctl.transaction() as tx:
            tx.emit("REFERENCE_VERIFIED", "fact", "test", artifact="reference/other")
        self.ok("pair", "whole")  # the same attempt: the pair is rebuilt, and now every copy under the referent is verified
        self.assertNotIn(ctl.READ_ONLY_LINE, pathlib.Path(self.root, ".gauntlet/pairs/whole/PROMPT.md").read_text())

    def test_a_verified_reference_lets_the_critic_run_both_sides(self):
        with ctl.transaction() as tx:
            tx.emit("REFERENCE_VERIFIED", "fact", "test", artifact="reference/ms")
        self.ok("pair", "parse")
        self.assertNotIn(ctl.READ_ONLY_LINE, pathlib.Path(self.pair_dir, "PROMPT.md").read_text())

    def test_a_pair_carries_no_name_on_either_side(self):  # F16, FR-6.5: bytesize-3's lead anonymised the reference by hand
        ref = os.path.join(self.root, "reference/ms")
        for rel, text in (("README.md", "# upstream\n"), ("LICENSE", "MIT (c) 2020 Someone\n"),
                          ("package.json", '{"name": "upstream", "author": "Someone", "repository": "someone/upstream", "version": "3.1.2", '
                                           '"description": "Utility", "keywords": ["bytes"], "devDependencies": {"mocha": "9"}, "type": "module", '
                                           '"exports": "./index.js"}\n'),
                          ("index.js", "/*!\n * upstream\n * Copyright(c) 2020 Someone\n */\nexport const parse = () => 1 // upstream\n")):
            pathlib.Path(ref, rel).write_text(text)
        self.write(".gauntlet/wt/parse/README.md", "# bytesize\n")
        self.ok("pair", "parse", "--prepare", "--reference", "reference/ms", "--prompt", ".gauntlet/staging/prompt.md")
        self.ok("pair", "parse")
        files = tree(self.pair_dir)
        self.assertFalse([f for f in files if os.path.basename(f) in ("README.md", "LICENSE")])  # both sides
        side = next(os.path.dirname(f) for f in files if f.endswith("package.json"))
        self.assertEqual(json.loads(files[os.path.join(side, "package.json")]), {"type": "module", "exports": "./index.js"})  # F36: what loads it
        code = files[os.path.join(side, "index.js")].decode()
        self.assertEqual(code, "/*!\n */\nexport const parse = () => 1 // upstream\n")  # comments go, code stays

    def test_identity_files_match_in_any_case_and_floor_trees_never_enter(self):  # F28, F29: the units whole gate
        pathlib.Path(self.root, "reference/ms/license.md").write_text("MIT (c) Someone\n")  # ms ships it lowercase
        self.write(".gauntlet/wt/parse/Readme.MD", "# bytesize\n")
        self.write(".gauntlet/wt/parse/reference/ms/MANIFEST", "{}\n")  # committed by the plan; excluded, its folder was not
        self.write(".gauntlet/wt/parse/heldout/x.mjs", "export default 1\n")
        self.ok("pair", "parse", "--prepare", "--reference", "reference/ms", "--prompt", ".gauntlet/staging/prompt.md")
        self.ok("pair", "parse")
        files = tree(self.pair_dir)
        self.assertFalse([f for f in files if os.path.basename(f).lower() in ("license.md", "readme.md")])
        for side in ("a", "b"):
            for top in ("reference", "heldout", "bench"):
                self.assertFalse(os.path.exists(os.path.join(self.pair_dir, side, top)), f"{side}/{top}")

    def test_a_document_goal_keeps_the_document_it_judges(self):  # F38, found preparing the writing run, 2026-09-24
        # A README is an identity file in a code pair and the work itself when the goal is the README: with the reference
        # passed as its folder, both sides lost the one file the critic was there to compare.
        ref = os.path.join(self.root, "reference/ms")
        pathlib.Path(ref, "Readme.md").write_text("Convert time formats.\n")
        pathlib.Path(ref, "LICENSE").write_text("MIT (c) 2020 Someone\n")
        self.write(".gauntlet/wt/parse/README.md", "Parse and format durations.\n")
        self.ok("pair", "parse", "--prepare", "--reference", "reference/ms", "--prompt", ".gauntlet/staging/prompt.md")
        self.ok("pair", "parse", "--ours", ".gauntlet/wt/parse/README.md")
        names = [os.path.basename(f) for f in tree(self.pair_dir)]
        self.assertEqual(sorted(n.lower() for n in names if n.lower() == "readme.md"), ["readme.md", "readme.md"])
        self.assertNotIn("LICENSE", names)

    def test_a_document_keeps_its_bullets_headings_and_example_comments(self):  # F40: units-docs lost ours' unit bullet
        # A comment-looking line in prose is content: a bullet, a heading, a comment inside an example. Stripping them for
        # the reference's name took a line from ours on every piece, and every critic docked ours for the missing item.
        pathlib.Path(self.root, "reference/ms/Readme.md").write_text("Convert time formats.\n")
        doc = "# Sizes, upstream style\n\n* upstream units: `B`, `KB`\n\n```js\n// like upstream: 1 KB is 1024 bytes\nparse('1KB')\n```\n"
        self.write(".gauntlet/wt/parse/README.md", doc)
        self.ok("pair", "parse", "--prepare", "--reference", "reference/ms", "--prompt", ".gauntlet/staging/prompt.md")
        self.ok("pair", "parse", "--ours", ".gauntlet/wt/parse/README.md")
        self.assertIn(doc, [v.decode() for k, v in tree(self.pair_dir).items() if k.lower().endswith("readme.md")])

    def test_refuses_on_a_red_floor(self):  # FR-NN.4
        with ctl.transaction() as tx:
            tx.emit("FLOOR_FAIL", "fact", "test", piece="parse", **{"class": "artifact"})
        self.assertEqual(self.run_ctl("pair", "parse")[0], 2)

    def test_swap_archives_the_first_pair_and_inverts_the_same_files(self):  # FR-1.5, FR-6.7
        self.ok("pair", "parse")
        first_id = pathlib.Path(self.pair_dir, "PAIR_ID").read_text().strip()
        first = self.mapping(first_id)
        self.assertEqual(self.run_ctl("swap", "parse")[0], 2)  # nothing is awaiting confirmation
        self.result("ours")
        before = {side: tree(os.path.join(self.pair_dir, side)) for side in "ab"}
        pathlib.Path(self.pair_dir, "_probe.mjs").write_text("a reader's scratch file\n")
        pathlib.Path(self.pair_dir, "b", "src").mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.pair_dir, "b", "src", "tampered.js").write_text("x\n")
        self.ok("swap", "parse")
        self.assertFalse(os.path.exists(os.path.join(self.pair_dir, "_probe.mjs")))  # swap inverts the pristine copy
        swapped_id = pathlib.Path(self.pair_dir, "PAIR_ID").read_text().strip()
        self.assertNotEqual(swapped_id, first_id)
        self.assertEqual((self.mapping(swapped_id)["a"], self.mapping(swapped_id)["b"]), (first["b"], first["a"]))
        self.assertEqual((tree(os.path.join(self.pair_dir, "a")), tree(os.path.join(self.pair_dir, "b"))), (before["b"], before["a"]))
        self.assertTrue(os.path.isdir(os.path.join(self.root, ".gauntlet/private/pairs", first_id)))
        attempt = [a for a in ctl.load()["attempts"].values() if a["status"] == "open"][0]
        self.assertEqual((attempt["expected_type"], attempt["order"]), ("reader-alt", "swapped"))

    def test_a_discarded_verdict_gets_a_new_attempt_on_the_same_pair(self):
        self.ok("pair", "parse")
        pair_id = pathlib.Path(self.pair_dir, "PAIR_ID").read_text().strip()
        state = ctl.load()
        with ctl.transaction() as tx:
            tx.emit("CRITIC_RESULT", "fact", "test", piece="parse", attempt_id=next(iter(state["attempts"])), agent_type="reader",
                    valid=False, reason="WINNER before EVIDENCE")
        self.ok("pair", "parse")
        self.assertEqual(pathlib.Path(self.pair_dir, "PAIR_ID").read_text().strip(), pair_id)  # a retry cannot change the experiment
        self.assertEqual(self.names().count("CRITIC_DISPATCHED"), 2)


class Variants(PairRepo):
    def test_when_every_variant_lost_one_pick_pair_says_which_continues(self):  # A2
        self.assertEqual(self.run_ctl("pair", "parse", "--pick", ".gauntlet/wt/parse-v2")[0], 2)  # no such path
        self.write(".gauntlet/wt/parse-v2/src/parse.js", "export const parse = () => 5\n")
        self.assertEqual(self.run_ctl("pair", "parse", "--pick", ".gauntlet/wt/parse-v2")[0], 2)  # no variants were selected
        self.ok("event", "VARIANT_APPROACHES_SELECTED", "piece=parse", "approaches=table-driven|regex")
        self.ok("pair", "parse", "--ours", ".gauntlet/wt/parse", "--pick", ".gauntlet/wt/parse-v2")
        self.assertEqual(sorted(os.listdir(self.pair_dir)), ["PAIR_ID", "PROMPT.md", "a", "b", "r"])
        self.result(".gauntlet/wt/parse-v2")  # attest translates the label through the mapping; here it is given
        piece = ctl.load()["pieces"]["parse"]
        self.assertEqual((piece["artifact"], piece["variants"], piece["state"]), (".gauntlet/wt/parse-v2", [], "ACTIVE"))


class ChampionChallenger(PairRepo):
    mode = ["--champion-challenger"]

    def test_anchor_plus_two_of_ours_then_the_gap_only_pair(self):  # A1, A2
        ctl.snapshot_champion(ctl.load(), "parse")  # `floors` does this when the first green attempt becomes champion
        self.round("export const parse = () => 3\n")
        self.ok("pair", "parse")
        self.assertEqual(sorted(os.listdir(self.pair_dir)), ["PAIR_ID", "PROMPT.md", "a", "b", "r"])
        sides = self.mapping(pathlib.Path(self.pair_dir, "PAIR_ID").read_text().strip())
        self.assertEqual(sorted([sides["a"], sides["b"]]), ["challenger", "champion"])
        self.assertIn("closer to R", pathlib.Path(self.pair_dir, "PROMPT.md").read_text())
        self.assertEqual(self.run_ctl("pair", "parse", "--gap-only")[0], 2)  # not before two challenger losses
        self.result("reference")  # the champion won
        self.round("export const parse = () => 4\n")
        self.ok("pair", "parse")
        self.result("reference")
        self.ok("pair", "parse", "--gap-only")
        self.assertEqual(sorted(os.listdir(self.pair_dir)), ["PAIR_ID", "PROMPT.md", "a", "b"])
        self.assertIn("GAP: none", pathlib.Path(self.pair_dir, "PROMPT.md").read_text())
        self.result(gap=None)
        self.ok("swap", "parse")
        self.result(gap=None, agent_type="reader-alt")
        self.assertEqual(ctl.load()["pieces"]["parse"]["state"], "CONFIRMED")
        self.ok("report")  # AC-2.3: converged against its referent, never "beat the bar"
        text = pathlib.Path(self.root, ".gauntlet/report.md").read_text()
        self.assertIn("parse: converged against reference/ms", text)
        self.assertNotIn("beat the bar", text)
