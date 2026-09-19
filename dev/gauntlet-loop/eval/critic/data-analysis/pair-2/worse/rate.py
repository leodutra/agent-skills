import csv, sys
rows = list(csv.DictReader(open(sys.argv[1])))
rates = [int(r["signups"]) / int(r["visitors"]) for r in rows]
print(f"conversion: {sum(rates) / len(rates):.2%}")
