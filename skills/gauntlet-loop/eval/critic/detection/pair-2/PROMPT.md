The bar: a detection rule for encoded PowerShell commands (ATT&CK T1059.001) that fires on every line of the attack set and on none of the benign set.
On each side: read `rule.json` in `a/` and `b/`; run `python3 match.py a/rule.json attack.txt benign.txt` and `python3 match.py b/rule.json attack.txt benign.txt`; paste the counts.
Reading floors: zero benign lines fire; abbreviated and differently-cased flags are covered.
