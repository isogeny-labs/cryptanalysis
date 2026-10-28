# Row-level rank stopping saves 1.97 million more D79 eight-source probes

Checking the F_q rank after each verified support-eight relation let the collector stop **inside** the source that first reached rank 39. On eight prospectively frozen D79 classes, this saved **1,969,146 signed quintuple probes**, or **3.27%** of the **60,299,296** probes that whole-prefix stopping would have issued through those same first rank-39 sources. Combined with stopping after the rank-39 source, it avoided **103,012,346 of 161,342,496** through-horizon probes, an exact **63.85%** operation-count reduction on the paired source streams. Every fresh class reached rank 39 through eight, with independently replayed logs for all 40 q-projected class points; the support-seven arm reached rank 39 in one class by its retained horizon.

| Cohort | p | q | Sources retained | Seven final rank / first 39 | Eight first 39 | Eight probes run | Extra probes saved inside last source | Total probes saved through horizon |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| Known control | 2468357 | 73 | 40 | 37 / — | 24 | 1,306,295 | 53,833 | 19,749,961 |
| Fresh | 2792557 | 5639 | 40 | 35 / — | 30 | 4,538,679 | 21,513 | 16,517,577 |
| Fresh | 2893717 | 10709 | 40 | 37 / — | 31 | 5,424,293 | 12,859 | 15,631,963 |
| Fresh | 2989757 | 293 | 40 | 37 / — | 33 | 7,010,640 | 584,112 | 14,045,616 |
| Fresh | 3101437 | 839 | 37 | 39 / 37 | 29 | 3,744,808 | 55,352 | 10,203,896 |
| Fresh | 3129677 | 1987 | 40 | 37 / — | 39 | 18,360,943 | 63,281 | 2,695,313 |
| Fresh | 3172277 | 7207 | 40 | 35 / — | 32 | 6,437,374 | 6,658 | 14,618,882 |
| Fresh | 3200837 | 67 | 40 | 36 / — | 33 | 7,376,261 | 218,491 | 13,679,995 |
| Fresh | 3243917 | 13513 | 40 | 38 / — | 32 | 5,437,152 | 1,006,880 | 15,619,104 |

The eight fresh classes were frozen by the odd-v prescreen beginning at v=1651, after the preceding panel's last selected v=1649. The audited p2468357 control was replayed before any new source lifts: the new index found rank 39 at source 24 after 1,306,295 probes, with its emitted rows a verified subset of the prior full-prefix rows. The producer then retained and fsynced **357 source equations** across all nine cases. Each record includes exact support-four through eight rows, both rank trajectories, the eight-source query boundary, status and caps, and exclusive phase timing. Eight-source row-rank checks are charged inside the eight-source phase.

The independent Sage audit passed all nine cases. It recomputed the public prescreen and every source equation, checked complete earlier eight-source row sets with a different four-plus-four split, reconstructed the final three-plus-five query prefix in exact support/sign order through its recorded probe boundary, checked the rank-raising last row, checked support-four through seven sets and both rank trajectories, verified the two probe counterfactuals and phase sums, and solved and replayed each 40-log system from the **exact stopped row prefix**. The first rank-39 source counts ranged from 29 to 39 in the fresh panel, with median 32.

The extra within-source saving ranged from 6,658 to 1,006,880 probes, median 59,317 rounded to the nearest integer. The eight-source stage wall intervals ranged from 14.00 to 75.23 seconds in the fresh panel; these are exploratory local diagnostics without Tier 0/1 isolation. The observed rank-39 completion proportions were 8/8 through eight and 1/8 through seven, with descriptive exact two-sided 95% binomial intervals [0.631, 1] and [0.003, 0.527]. `candidate_id` and `target_online_ms` remain null. The modest 3.27% within-prefix reduction identifies query order as the next lever: score several deterministic orders on the prior full-row panel, freeze one order, then test it prospectively on disjoint classes with exact row and query-prefix audits.
