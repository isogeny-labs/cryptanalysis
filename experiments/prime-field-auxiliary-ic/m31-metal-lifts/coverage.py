"""Count actual and possible singleton emissions in the frozen four-lane scan."""
import csv
import sys
P = 2**31 - 1
primes = (2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89)
w = csv.writer(sys.stdout,lineterminator='\n')
w.writerow(('prime','parents','singleton_parents','batched_parents','children'))
live = [1]
for q in primes:
    limit = (P-1)//q
    live = [x for x in live if x <= limit]
    stop = len(live)
    singleton = sum(x > limit//q for x in live)
    i = batched = children = 0
    while i < stop:
        if i+4 <= stop and min(live[i:i+4]) > limit//q:
            batched += 4
            children += 4
            i += 4
        else:
            y = live[i]*q
            while y < P:
                children += 1
                if y <= limit:
                    live.append(y)
                y *= q
            i += 1
    w.writerow((q,stop,singleton,batched,children))
