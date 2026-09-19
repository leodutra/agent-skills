The bar: a detection rule for local account creation with `net user ... /add` (ATT&CK T1136.001) that fires on every attack line and on no benign line.
On each side: read `rule.json` in `a/` and `b/`; run `python3 match.py a/rule.json attack.txt benign.txt` and `python3 match.py b/rule.json attack.txt benign.txt`; paste the counts.
Reading floors: zero benign lines fire.
