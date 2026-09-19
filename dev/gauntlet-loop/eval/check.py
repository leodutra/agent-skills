#!/usr/bin/env python3
"""Write-mode eval checks. check.py [--baseline] [--upto N] [--only id,id] <outdir> | --list [--upto N] [--only id,id] | --field <id> <goal|model>"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SUITE = json.load(open(os.path.join(HERE, "write-mode", "cases.json")))


def prompt_of(text):
    """The paste prompt: from the first line starting with /goal to its fixed last line, else the fence or the end."""
    m = re.search(r"^/goal .*?(?:^Fan out subagents\.|(?=^```)|\Z)", text, re.S | re.M)
    return m.group(0).strip() if m else ""


def failures(case, text):
    c, low, p = case["checks"], text.lower(), prompt_of(text)
    out = []
    if c.get("prompt") is True and not p: out.append("no /goal prompt")
    if c.get("prompt") is False and p: out.append("wrote a prompt; expected a refusal")
    if p and len(p.split()) > c.get("max_words", 10**9): out.append(f"{len(p.split())} words")
    first = p.splitlines()[0].lower() if p else ""
    out += [f"first line lacks {s!r}" for s in c.get("first_line", []) if s.lower() not in first]
    out += [f"prompt lacks {s!r}" for s in c.get("prompt_contains", []) if s.lower() not in p.lower()]
    out += [f"reply lacks {s!r}" for s in c.get("contains", []) if s.lower() not in low]
    out += [f"reply has {s!r}" for s in c.get("not_contains", []) if s.lower() in low]
    out += [f"reply does not match {s!r}" for s in c.get("matches", []) if not re.search(s, text, re.I)]
    return out


def main(argv):
    upto = int(argv[argv.index("--upto") + 1]) if "--upto" in argv else 10**9
    only = argv[argv.index("--only") + 1].split(",") if "--only" in argv else None
    cases = [c for c in SUITE["cases"] if c["phase"] <= upto and (not only or c["id"] in only)]
    if "--field" in argv:
        cid, name = argv[argv.index("--field") + 1:][:2]
        case = next(c for c in SUITE["cases"] if c["id"] == cid)
        print({"goal": case["goal"] + (SUITE["suffix"] if case["checks"].get("prompt") else ""), "model": SUITE["model"]}[name])
        return 0
    if "--list" in argv:
        print("\n".join(c["id"] for c in cases)); return 0
    outdir, failed = argv[-1], 0
    for case in cases:
        path = os.path.join(outdir, case["id"] + ".json")
        text = json.load(open(path)).get("result") or "" if os.path.exists(path) else ""
        bad = failures(case, text) if text else ["no output"]
        failed += bool(bad)
        print(f"{'FAIL' if bad else 'pass'}  {case['id']}" + (": " + "; ".join(bad) if bad else ""))
    rate = (len(cases) - failed) / len(cases) if cases else 0.0
    print(f"{len(cases) - failed}/{len(cases)} passed ({rate:.2f})")
    if "--baseline" in argv:  # the gate: never below the lowest of three recorded runs; a single stochastic miss is not a regression
        floor = json.load(open(os.path.join(HERE, "baseline.json")))["write_mode"]["rate"]
        print(f"baseline {floor:.2f}: {'ok' if rate >= floor else 'BELOW'}")
        return 0 if rate >= floor else 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
