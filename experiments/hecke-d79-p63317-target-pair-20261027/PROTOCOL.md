# p63317 frozen one-target partial-coverage test

Use the hash-pinned p63317 40-point class and audited support-four relation rows. Before the target is generated, freeze the input seed, SHA-256 scalar derivation, rejection of identity and projected class points, 100-counter cap, and exact signed pair policy. A failed target lookup remains `NO_RELATION`; do not replace the target after inspecting pair coverage.

Under the checked repository Sage launcher, choose the first nonzero `T=25P_i` and solve the F2531 class-log system from all frozen support-four rows plus the known anchor `log_T(T)=1`. Keep the index construction target independent. The producer must read only the public point, never the scalar fixture. Build all signed distinct pairs, record exact subgroup coverage, then query the one public point. If found, verify the pair equation, derive its scalar from solved class logs and replay `kT=Q`. If absent, preserve `NO_RELATION`.

Independently enumerate all 2531 multiples of `T` to audit class logs and the fixture, replay the pair index and target status in Sage, and retain all component costs. This is an operational target-relation and coverage test; no complete IC candidate or paired rho comparison is defined. Keep `candidate_id` and `target_online_ms` null. Save `./sage --runtime-info` before measured Sage work.
