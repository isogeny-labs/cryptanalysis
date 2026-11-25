# Checked-root ABI in the complete public M31 basis preparation phase

Two processes on a local Apple M4 Pro replayed construction of both 500-point public fixtures. Each timing includes candidate generation, cubic evaluation, lift checks, filtering, and construction of the ordered Python point list. For the auxiliary basis the timer also includes the archived isogeny chain, all coordinate generation and the checks on every chain output. Both native-library arms include Python buffer creation and ctypes dispatch. Library loading, interpreter startup, disk output and post-timing comparisons are outside the clock.

| Basis and process | Archived Python ms | Cofactor-one Python ms | Portable C ABI ms | ARM C ABI ms | Paired archived / ARM |
|---|---:|---:|---:|---:|---:|
| Plain, first | 2.4869 | 1.9018 | 0.3229 | 0.2815 | 8.867× |
| Plain, repeat | 2.5255 | 1.9061 | 0.3195 | 0.2913 | 8.655× |
| Auxiliary, first | 10.5262 | 9.9258 | 8.4559 | 8.4250 | 1.248× |
| Auxiliary, repeat | 10.8075 | 10.1062 | 8.4930 | 8.4752 | 1.276× |

Times are medians over 24 blocks per process. Ratios are medians of comparisons paired within blocks. Each method occupies each position six times. Every measured list matched all 500 archived ordered point pairs. The portable and ARM arms shared the same caller. Portable/ARM median paired ratios were 1.156× and 1.111× for plain preparation, and 1.0024× and 0.9999× for auxiliary preparation. The plain-phase gain includes moving square-root computation out of Python. Timing supports little additional benefit from ARM over portable C in the full auxiliary phase.

Run `python3 panel.py` twice to reproduce the protocol. It requires SymPy, a C++17 compiler, and the sibling m31-root-schedule directory. The driver extracts the original timed statements and scalar lift from the pinned Python source. The separate cofactor-one arm omits the archived multiplication by one. The ABI arms exploit the same identity, operate in blocks of 64 and preserve the order and stopping condition. Plain generation pays for the entire final block, even when its 500th accepted point arrives partway through it. No timing arm reads the known last coordinate as a stopping rule.

Archived totals provide a separate upper bound on relevance to the complete workload. In revision efb9330c1, snapshot/comparison/runs.json records basis construction as 0.806–0.870% of setup plus process wall time on the three M31 plain runs, and 3.088–3.485% on the auxiliary runs. Removing all such time would save at most that fraction if the rest of the archived run stayed fixed. This replay measured setup locally and does not combine timings across hosts.
