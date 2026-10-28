# Rank stopping preserves D79 class-log recovery while avoiding 84% of eight-source probes

On eight prospectively frozen D79 classes, the early-stop collector reached **F_q rank 39 and independently replayed all 40 q-projected class-point logarithms in every class** after 24–31 degree-13 sources (median 27.5). It then stopped eight-source queries while the paired support-seven arm continued on the same source stream. Across those eight classes, it executed **25,451,104** signed quintuple probes and avoided **135,891,392** of the **161,342,496** probes required to run the same eight-source index through each paired arm's retained horizon, an exact **84.2% probe reduction**. The support-seven arm reached rank 39 in two classes by that horizon; the other six finished at ranks 35–38.

| Cohort | p | q | Sources retained | Seven final rank / first 39 | Eight first 39 | Eight probes run | Eight probes avoided |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| Known control | 2076797 | 103867 | 40 | 37 / — | 27 | 2,583,360 | 18,472,896 |
| Fresh | 2374997 | 2293 | 37 | 39 / 37 | 25 | 1,700,160 | 12,248,544 |
| Fresh | 2399717 | 283 | 40 | 39 / 40 | 28 | 3,144,960 | 17,911,296 |
| Fresh | 2405917 | 3823 | 40 | 38 / — | 31 | 5,437,152 | 15,619,104 |
| Fresh | 2437037 | 5081 | 40 | 38 / — | 26 | 2,104,960 | 18,951,296 |
| Fresh | 2468357 | 73 | 40 | 37 / — | 24 | 1,360,128 | 19,696,128 |
| Fresh | 2621477 | 34919 | 40 | 35 / — | 30 | 4,560,192 | 16,496,064 |
| Fresh | 2653957 | 149 | 40 | 38 / — | 27 | 2,583,360 | 18,472,896 |
| Fresh | 2719517 | 22669 | 40 | 36 / — | 30 | 4,560,192 | 16,496,064 |

The eight fresh classes were selected by the frozen odd-v prescreen starting at v=1521, beyond the preceding panel's selected range, before new degree-13 lifts. The retained p2076797 control's audited prefix and exact support-eight rows were replayed before the producer ran. The producer wrote and fsynced each of **357 retained source equations** with its exact support-four through eight rows, rank states, stop state, operation counts, and exclusive phase timings. The eight-source probe identity is `32 * binomial(n, 5)` for n retained sources; the saved count subtracts the observed prefix at the first eight-source rank-39 stop. It is an operation-count difference on the same frozen source horizon, not a wall-time extrapolation.

The independent Sage audit passed all nine cases. It recomputed the public prescreen and source equations, used a different four-plus-four split to match every eight-source row through the stop, matched support-four through seven rows through the paired horizon, checked each prefix rank with separate dense elimination and each final rank with Sage matrices, verified the skipped-source records and exact probe arithmetic, checked exclusive phase sums, and solved and replayed all nine anchored 40-log systems from their **stopped prefixes**.

The local eight-source stage wall intervals were 4.18–17.35 seconds on the eight fresh classes, recorded separately from lifting, lower-support searches, rank work, and replay. On the retained p2076797 control the earlier full-horizon eight-source run recorded 66.58 seconds for that stage; this early-stop run recorded 8.58 seconds. Those are exploratory local diagnostics from separate executions without Tier 0/1 isolation. The empirical rank-39 completion proportions on the fresh panel were 8/8 through eight and 2/8 through seven; exact two-sided 95% binomial intervals are [0.631, 1] and [0.032, 0.651], respectively, as descriptive rates under this selection rule. `candidate_id` and `target_online_ms` remain null. The next experiment should test whether a rank-aware query order finds the needed eight-source directions earlier within each prefix, using exact row verification and a frozen disjoint panel.
