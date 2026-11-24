# Exact index lookup with variable hit probability

The panel uses the same 4096 held-out 17-key sets as window-holdout.json. Every method returns the index in generator order or the sentinel 17. Each measured traversal constructs and destroys the appropriate index for each set. Coordinates are read from the x field of a point-shaped record. The three processes shuffle the order of sets independently. They generate queries outside the timer, retain their expected original indices, and check the full output vector after every timed traversal. A miss is resampled if its coordinate accidentally belongs to the base.

The four methods are a direct scan, the archived unreserved unordered map type, a seven-bit XOR index with early termination, and the same XOR index with four additional six-bit lookup tables. The XOR construction starts with the seven low bits. It inspects higher bits until all current addresses are distinct. A candidate mask must separate addresses that would collide across the new bit. The final query checks the stored full coordinate in each occupied slot.

On an unpinned Apple M4 Pro with Apple Clang 21.0.0, each cell has four warmups and eight timed traversals per seed. The CSV records nanoseconds per base including all queries. Query inputs are synthetic. The loop counters from the historical collector do not supply the corresponding number of failed lookups.

From this directory generate the holdout JSONL as in window-cost.md, then run:

```sh
python3 -c 'import json,sys; [print(*(x for x,b in json.loads(line) if b)) for line in sys.stdin]' < /tmp/window-holdout.jsonl > /tmp/window-keys.txt
clang++ -std=c++17 -O3 -mcpu=native xor-index.cpp -o /tmp/xor-index
for seed in 7 8 9; do /tmp/xor-index "$seed" < /tmp/window-keys.txt; done
```

At 16 probes the direct scan beat the four-table XOR method for all four hit probabilities and all three seeds. At 256 probes the XOR method won all three comparisons at 0%, 1%, and 100% hits, while the scan won all three at 50%. At 1024 probes the XOR method won in every seed and mix. Paired scan-to-XOR time ratios at that count ranged from 1.44–1.77 at 0% hits, 1.90–1.92 at 1%, 1.13–1.14 at 50%, and 5.60–5.75 at 100%. The timing distributions alone do not identify which instructions account for the differences.
