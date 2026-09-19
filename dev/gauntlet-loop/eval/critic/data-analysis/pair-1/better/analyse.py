import csv, statistics, sys
rows = list(csv.DictReader(open(sys.argv[1])))
amounts = [float(r["amount"]) for r in rows if r["amount"].strip()]
print(f"rows: {len(rows)}, used: {len(amounts)}, dropped for a missing amount: {len(rows) - len(amounts)}")
print(f"median order amount: {statistics.median(amounts):.2f} (median, because one order of {max(amounts):.0f} would drag a mean)")
