# Exact two-case exclusion for an N131 width-three public block

Two independently replayed degree-six Boolean Macaulay certificates exclude the complete left-code block `0..7` paired with every 32-bit right source code for the frozen N131 public resultant input. Solving the two width-two cases sequentially took **489.734 seconds** of target-dependent parent wall time with one native worker and under 4 GiB combined RSS. The direct width-three solver reached its 590-second wall cap after 17,000 rows; the exact case split therefore decided a block that direct elimination left censored within the same envelope.

## Exact input and coverage

The curve is `EC1N131Ckb1heb5f1998f20b` over GF(2^131) with modulus `u^131+u^13+u^2+u+1`. The frozen public raw point is `(877610862732227974378969808549299291499, 2063336771837286479337213121437715536874)`. The W33 source seed is `898618`, with rotations `0` and `18`. The Boolean input is the 131 coordinate equations of the frozen two-product resultant, using one source code for each side. `audit_sage.py`, run through the checked repository Sage launcher, independently reconstructed the anchor-4 equation file over the specified field and compared every coordinate support. The first anchor-0 input and its independent Sage audit are frozen in the prior interleaved-block experiment.

For fixed right code `b` in `0..2^32-1`, every left code `a` in `0..7` belongs to exactly one case: `a<4` or `4≤a<8`. Both case certificates replay to the polynomial identity `1 = Σ m_i e_i` over GF(2), where each `e_i` is a coordinate equation and every multiplier `m_i` has degree at most two. Any zero of the resultant coordinate equations would make the right side zero. The two cases therefore exclude `8 × 2^32 = 2^35` source-code pairs from this exact resultant input. The case-partition implication is proved in `SplitBlock.lean`; the finite-field and certificate bridges are checked by the frozen Sage audit and Python replays.

## Frozen measurements

| Case | Left codes | Solver status | Rows processed | Certificate rows | Parent wall seconds | Sampled combined RSS bytes |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Prior first half | `0..3` | `REJECT_CERTIFICATE` | 13,071 | 4,414 | 204.902 | 346,669,056 |
| New second half | `4..7` | `REJECT_CERTIFICATE` | 12,972 | 6,537 | 284.832 | 447,430,656 |
| Sequential target-dependent solver total | `0..7` | both exact replays pass | 26,043 | 10,951 | **489.734** | 447,430,656 peak per run |
| Direct width-three comparator | `0..7` | `WALL_CAP` | 17,000 at last checkpoint | — | 590.033 | 740,507,648 |

The second-case preparation took 0.189 seconds; its independent Sage audit took 0.276 seconds and is a verification gate. The first-case preparation belongs to its prior frozen run. The 489.734-second number is the sum of target-dependent **solver parent walls**, rather than a complete IC online measurement. No factor-base relation, final matrix solve, target descent, scalar replay, or matched rho run is represented by this component metric. `candidate_id` remains `null`.

## Controls and verification

The N41 ordinary anchor-4 block gave a 291-row certificate in 0.053 seconds, independently replayed to `{0}`. The previously verified N41 known-root control retains `(253,63)` and the N131 positive source input retains `(3,16722)`. `verification_n41.json` and `verification_result.json` retain the control and public replay statuses. The new N131 certificate has rank 12,969 at row 12,972 and 13,608,036 recorded reductions; independent replay returns XOR support `{0}`. The direct width-three comparator remains `WALL_CAP`, with root existence undecided for its direct elimination path.

The frozen protocols, equation files, source and binary hashes, checked Sage runtime receipt, native stdout and stderr, supervisor receipts, replay scripts, Lean build output, and proof map are retained here. The prior first-half receipt and the direct comparator live in their adjacent versioned experiment directories.

## Next experiment

Use the exact case split as a lower-dimensional exclusion primitive inside a search that can also **find** a valid decomposition. Freeze a candidate with a relation-bearing N41 control and an N131 ordinary-query law, then measure accepted roots, full failed-attempt cost, novel relation rank, and the one-target online interval. A larger excluded source-code block alone does not select an IC pipeline.
