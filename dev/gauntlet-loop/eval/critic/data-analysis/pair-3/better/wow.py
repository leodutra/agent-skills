import csv, sys
rows = {r["week"]: int(r["orders"]) for r in csv.DictReader(open(sys.argv[1]))}
change = (rows["this"] - rows["last"]) / rows["last"]
print(f"orders: {rows['last']} -> {rows['this']} ({change:+.1%} week over week)")
