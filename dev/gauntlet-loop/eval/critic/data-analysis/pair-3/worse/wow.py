import csv, sys
last, this = [int(r["orders"]) for r in csv.DictReader(open(sys.argv[1]))]
print(f"last week {last}, this week {this}: {100 * (this - last) / last:+.1f}% week over week")
