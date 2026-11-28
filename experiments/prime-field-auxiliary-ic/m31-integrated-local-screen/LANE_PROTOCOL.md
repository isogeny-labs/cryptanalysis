# M31 batch-lane screen

Use the same frozen coordinate-input target, release `m31-fast` worker and
B256 interval/m2 indexed configuration as `PROTOCOL.md`. Compare lane counts
32,64,128,256,512,1024 over seeds 0,1,2, with one fresh process per cell
and shuffled order from `random.Random(2026112729)`. The budget is four
million queries and five seconds online per cell. Charge complete process
wall and parent-plus-child CPU, preserve all 18 JSON reports and statuses,
and check any recovered scalar against the public generator and target.
Different lane counts induce different walk trajectories, so these are
same-target tuning cells rather than matched-work equivalence pairs.
Assess both success frequency and total cost; a promising lane requires a
fresh-target confirmation against lane64 before adoption.
