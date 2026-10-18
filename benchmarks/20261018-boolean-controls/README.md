# Boolean solver and order correctness controls

The [combined report](report.pdf), [count graph](counted-work.svg) and
[pipeline diagram](pipeline.svg) copy the
[source study](../../experiments/ideas_boolean_20261018/REPORT.md).
Corresponding PNGs were rendered from those exact SVGs at 150 dpi with Inkscape;
the source study used 180 dpi/default Graphviz PNG output. Its sources and
records remain unchanged.

Forty-eight M4RI plus completion order arms passed exact ideal certificates;
sixteen existing F5/M4RI signature-budget arms passed. Both scalar adapters
retain twelve 20-second 12-variable timeouts. Fixed-degree matrix reduction
plus unbounded completion does not determine solving degree. The tiny fixed-row
trace transfer paid 428 row XORs including learning and fallback, against 180
for baseline alone; it is not full Joux-Vitse symbolic trace learning.

CPU-only shared-host controls, not a CUDA experiment or host-isolated Tier 0
comparison. No credible c fit, general solving-degree result or complete IC
speedup follows. Exact full-curve fixtures retain null subgroup/candidate IDs;
historical registry aliases with mismatched moduli are not borrowed.
