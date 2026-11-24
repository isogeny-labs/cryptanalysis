# Construction cost of public M31 abscissa lookup

Three local processes on an unpinned Apple M4 Pro used Apple Clang 21.0.0 and the 4,096 bases from window-holdout.json. Each run shuffled base order and used its own deterministic query stream with a one-half probability of drawing a stored key and otherwise a uniformly reduced PRNG word. Each of the three methods received identical queries within a run. The input keys remained in generator order. Every round compared every output byte against an independent linear search.

The scan compares all 17 values. The sorted arm copies and sorts each base before binary search. The window arm tries the ten frozen offsets in order, stopping at the first collision-free choice, fills 128 entries, then compares each full key. All 143 bases where selection fails use the scan after paying the search cost. Input generation, shuffling and validation are outside the timer. Every timed traversal includes a new construction for every base. The same data is traversed in each round, so this measures setup-charged throughput within a process.

To replay from this directory using the holdout generator in window-holdout.py:

```sh
sed -e 's/setrand(291160)/setrand(291161)/' -e 's/count<256/count<4096/' ../m31-projection-controls/sample.gp | gp -q -f > /tmp/window-holdout.jsonl
python3 -c 'import json,sys; [print(*(x for x,b in json.loads(line) if b)) for line in sys.stdin]' < /tmp/window-holdout.jsonl > /tmp/window-keys.txt
clang++ -std=c++17 -O3 -mcpu=native window-cost.cpp -o /tmp/window-cost
for seed in 1 2 3; do /tmp/window-cost "$seed" < /tmp/window-keys.txt; done
```

Each seed contributes six measured rounds following three warmups. The CSV reports nanoseconds per base, including all queries for that base. At 64 queries the scan won in all three processes. At 256 the ordering varied. At 1024 the window method won in all three.
