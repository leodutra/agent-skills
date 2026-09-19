#!/usr/bin/env python3
"""Check the critic runs, two ways.

Picks: a clear pair passes when the known-better side wins in both orders; a near-tie passes when both orders give a
WINNER and no hedge. Judged on the verdict block wherever it starts, so a shape miss never hides a flip.
Shape: the share of replies the controller itself would accept: first line `PAIR: <id>`, EVIDENCE before WINNER, a citation.
A reply that opens with its conclusion is the failure the shape rule exists to catch, and it is counted here, not forgiven.

check_critic.py [--baseline] [--only domain[/pair-N]] <outdir>"""
import importlib.machinery
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
loader = importlib.machinery.SourceFileLoader("gauntletctl", os.path.join(HERE, "..", "bin", "gauntletctl"))
spec = importlib.util.spec_from_loader("gauntletctl", loader)
ctl = importlib.util.module_from_spec(spec)
loader.exec_module(ctl)  # the shape check is the controller's own


def verdict_of(path, pair_id):
    """(label for the pick check, shaped as the controller demands?, why not)."""
    if not os.path.exists(path):
        return None, False, "no output"
    try:
        text = json.load(open(path)).get("result") or ""
    except ValueError:
        return None, False, "unreadable output"
    strict = ctl.parse_verdict(text, "pairwise")
    shaped = strict["valid"] and strict["pair"] == pair_id
    start = text.find("PAIR:")
    block = ctl.parse_verdict(text[start:], "pairwise") if start >= 0 else strict
    if not block["valid"] or block["pair"] != pair_id:
        return None, False, block["reason"] or f"names pair {block['pair']}"
    return block["label"], shaped, None if shaped else strict["reason"]


def main(argv):
    only = argv[argv.index("--only") + 1] if "--only" in argv else ""
    outdir, picks, shapes = argv[-1], [], []
    root = os.path.join(HERE, "critic")
    for domain in sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))):
        for pair in sorted(os.listdir(os.path.join(root, domain))):
            name = f"{domain}/{pair}"
            if not name.startswith(only):
                continue
            kind = open(os.path.join(root, domain, pair, "kind")).read().strip()
            bad, notes = [], []
            for order, better in (("ab", "A"), ("ba", "B")):
                pair_id = f"{domain}-{pair}-{order}"
                label, shaped, why = verdict_of(os.path.join(outdir, pair_id + ".json"), pair_id)
                shapes.append(shaped)
                if label is None:
                    bad.append(f"{order}: {why}")
                elif label == "hedge":
                    bad.append(f"{order}: a hedge")
                elif kind == "clear" and label != better:
                    bad.append(f"{order}: PICKED THE KNOWN-WORSE SIDE")
                elif not shaped:
                    notes.append(f"{order}: {why}")
            picks.append(not bad)
            print(f"{'FAIL' if bad else 'pass'}  {name} ({kind})" + (": " + "; ".join(bad + notes) if bad or notes else ""))
    pick_rate = sum(picks) / len(picks) if picks else 0.0
    shape_rate = sum(shapes) / len(shapes) if shapes else 0.0
    print(f"picks: {sum(picks)}/{len(picks)} pairs ({pick_rate:.2f})   shape: {sum(shapes)}/{len(shapes)} verdicts ({shape_rate:.2f})")
    if "--baseline" in argv:
        floor = json.load(open(os.path.join(HERE, "baseline.json")))["critic"]
        ok = pick_rate >= floor["pick_rate"] and shape_rate >= floor["shape_rate"]
        print(f"baseline picks {floor['pick_rate']:.2f}, shape {floor['shape_rate']:.2f}: {'ok' if ok else 'BELOW'}")
        return 0 if ok else 1
    return 0 if all(picks) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
