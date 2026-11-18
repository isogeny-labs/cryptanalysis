# CT199 — carryover-conditioned route-price interpretation (frozen protocol)
2026-11-18 UTC · [pcc:unverified] · No native execution or paid compute.

## Existing evidence and precise defect
Reuse merged CT188 physical A/B roster (seed 20261119, SHA-256 `1bc8c26a01e7952e57d944fd535c9832607f2ab7bcc910342ad704171ab67af1`), merged CT190 per-packet 14-column block-fixed-effect regression, CT189 physical producer, and CT198 frozen 48-packet C169 versus two C13 counter identity. The 48-packet fixture Git blob is `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3`. Unchanged original CT125 arithmetic and all frozen records.

CT190's reported `median_direct_over_retained_ratio_block_fixed = exp(-median(beta_B))` is **only conditional on previous_B=0**, not a population route contrast when `beta_B_x_previous_B != 0`. The fitted model is
`log t = alpha[block] + period + beta_B*B + beta_z*previous_B + beta_Bz*(B*previous_B)`.
For previous-B state `z=0` or `1`, the model-conditional DIRECT/RETAINED ratio at fixed z is `exp(-(beta_B+z*beta_Bz))`; common carryover `beta_z` cancels. The planned CT188 eight four-position sequences contain exactly 12 previous-B positions among 32 per packet (and 20 previous-A). A clearly labelled **model-standardized** contrast at *registered roster mix* q=3/8 is `exp(-(beta_B+(3/8)*beta_Bz))`. This is not necessarily the effect of a different run schedule or a causal speedup.

## Preregistered source-only implementation
- Add an exact rational roster-share check for every original packet and fail closed on changed sequences, expected 12/32, frozen roster digest or altered rank.
- Add **three separate** median direct/retained diagnostic ratios to CT190's report: previous-A, previous-B, and q=3/8 model-standardized; keep the old field as a documented previous-A-compatible legacy alias so callers do not break.
- Add per-packet paired log contrast fields so no one can infer a median of times is a complete solve.
- No changes to CT188/CT189 producer or schedules, CT125/CT192 Rust, historical fixture, PCC, model coefficients, CI budget or approval.
- Verify synthetic null, nonzero `beta_Bz`, nuisance-only `beta_z`, known true 1.25 direct/retained factor with 1.08 B-after-B modifier, amended standardized factor `1.25/1.08**(3/8)`, missing/corrupted roster failures, normal and `-O` Python; preserve all existing tests.
- Never pool packet timings or identity/generic strata as independent ECDLP targets. Report as **source-only conditional diagnostics**. No confidence interval or causal interpretation.

## Sources and gating
Prior work: [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), [#4215](https://github.com/isogeny-labs/crypto/pull/4215), [cryptanalysis #1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523), [CT188 #1725](https://github.com/isogeny-labs/cryptanalysis/pull/1725), [CT190 #1732](https://github.com/isogeny-labs/cryptanalysis/pull/1732), [CT198 #1748](https://github.com/isogeny-labs/cryptanalysis/pull/1748), [GPU IC #4178](https://github.com/isogeny-labs/crypto/pull/4178). Original source reviewed at `ct188_physical_crossover_design.py` and `ct190_block_fixed_effect_diagnostic.py`. Research-KB connector unavailable; no novelty or prior-art absence claim. Shared autoresearcher lab-contract currently unreadable as plaintext, so only local cryptanalysis AGENTS and frozen source apply.

Successful source CI is not a signed PCC verdict or actual hardware pricing. Full native all-48 replay, authenticated original 695/701 custody, same-host actual C169/C13a/C13b/N2_actual/D, and complete cold single-target rho/BSGS/IC with memory, uncertainty and independent PCC remain gates. Do not launch unapproved compute or merge against review gates.
