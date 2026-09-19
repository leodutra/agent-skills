import csv, sys
rows = list(csv.DictReader(open(sys.argv[1])))
signups = sum(int(r["signups"]) for r in rows)
visitors = sum(int(r["visitors"]) for r in rows)
print(f"conversion: {signups}/{visitors} = {signups / visitors:.2%}")
