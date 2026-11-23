from pathlib import Path
import csv
import sys
import runpy

base = Path(__file__).resolve().parents[1]
previous = runpy.run_path(str(base/'m31-doubling-smooth/census.py'))
values = [1]
writer = csv.writer(sys.stdout,lineterminator='\n')
writer.writerow(['bound','smooth','comparison_lifts'])
for q in previous['PRIMES']:
    extra = []
    for x in values:
        x *= q
        while x < previous['P']:
            extra.append(x)
            x *= q
    values.extend(extra)
    if q in (47,67,89):
        p = previous['P']
        hits = sum(pow(previous['cubic'](x),(p-1)//2,p)==1 for x in values)
        writer.writerow([q,len(values),hits])
