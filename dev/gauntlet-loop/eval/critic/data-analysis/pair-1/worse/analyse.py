import csv, sys
total = 0
n = 0
for r in csv.DictReader(open(sys.argv[1])):
    total += float(r["amount"] or 0)
    n += 1
print("typical order amount:", round(total / n, 2))
