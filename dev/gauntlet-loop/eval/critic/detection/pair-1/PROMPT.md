The bar: a detection rule for scheduled-task creation (ATT&CK T1053.005) that fires on every line of the attack set and on none of the benign set.
On each side: read `rule.json` in `a/` and `b/`; run `python3 match.py a/rule.json attack.txt benign.txt` and `python3 match.py b/rule.json attack.txt benign.txt`; paste the counts.
Reading floors: zero benign lines fire; the rule matches the behaviour, not one literal command line.
