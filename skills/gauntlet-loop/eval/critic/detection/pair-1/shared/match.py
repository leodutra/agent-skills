import json, re, sys
rule = json.load(open(sys.argv[1]))
for name in sys.argv[2:]:
    lines = [l.rstrip("\n") for l in open(name) if l.strip()]
    hits = [l for l in lines if all(re.search(p, l, re.I if rule.get("ignore_case") else 0) for p in rule["all"])]
    print(f"{name}: {len(hits)}/{len(lines)} fire")
    for l in hits:
        print("   ", l)
