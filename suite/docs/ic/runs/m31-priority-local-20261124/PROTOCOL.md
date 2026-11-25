# Native coordinate-priority follow-up

Adaptive follow-up to the completed default-branching feasibility run. Preserve
all earlier results. Hypothesis: prioritizing the coordinate bits, rather than
the derived monomial gates, changes the native solver search enough to return
more valid m31 relations within the same caps. This is not a preregistered
speedup claim and has no promotion gate.

Use the same n=7,13,17, dimensions3,3,4, seeds1,2, serial/balanced m31 cases,
max_trials4, conflicts1000, models4, native walk/rho reference, 20-second
process wall and 2-GiB RSS caps as the original run. The only solver setting
changed is branching=coordinates. No seed or cap changes after observation.
The existing m2 controls remain in the first run; no new m2 comparisons.

Keep raw outputs and native self-checks locally under the user's local-run
authorization; retain timeouts/unknown separately. CPU-only debug build,
producer assertions [pcc:unverified].
