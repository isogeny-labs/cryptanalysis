# CT181 — frozen counterbalanced cold-transfer price design (before implementation)

Date: 2026-11-17 UTC. Standing **[pcc:unverified]**. Parent [CT180 #1710](https://github.com/isogeny-labs/cryptanalysis/pull/1710), [CT179 #1708](https://github.com/isogeny-labs/cryptanalysis/pull/1708), live [CT178 #1706](https://github.com/isogeny-labs/cryptanalysis/pull/1706), root [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), queue [#3904](https://github.com/isogeny-labs/crypto/issues/3904). **This is prospective design testing; no native run or claim of computational advantage.**

## Falsification of the currently frozen A/B/B/A/A/A estimator

The existing `test_ct179_panel_adjudicator.py:sample` assigns wall times **by position alone**: slots 1 and 2 receive 2,000,000 ns, all other slots 3,000,000 ns. There is *no arm-specific timing parameter*. Nonetheless `ct179_panel_adjudicator.py:paired_statistics` reports direct/retained ratio `(3+3)/(2+2)=1.5` and A/A absolute-log drift zero. It can even produce a degenerate packet-bootstrap CI around 1.5 if repeated across all five generic scalar-label packets. This is an exact synthetic **negative** control for position confounding, not evidence of a 1.5x algorithmic improvement. The current v1 protocol never counterbalances treatment assignments to slots.

An explicit model proves the flaw. Let both arms have the same intrinsic wall time (t>0), and assign position-specific multiplicative factors (m=(3/2,1,1,3/2,3/2,3/2)). In A/B/B/A/A/A, `A0+A3 = 3t`, `B1+B2 = 2t`, so reported `A/B=3/2` while `A4/A5=1`. Repeating blocks and bootstrap cannot cure a fixed assignment confound. Neither valid outputs, exact counters, host identity nor CT180 clock nesting detect it.

## Predeclared v2 counterbalanced schedule and statistic

Keep **the same immutable 48 public packets**, 8 blocks, 6 fresh processes per packet, 2,304 total, frozen seeded packet shuffle and source/counter/timeout/memory gates. For each packet index `i` and block `b`, choose:

- `(b+i)%2 == 0`: slots `A B B A A A`.
- `(b+i)%2 == 1`: slots `B A A B A A`.

Thus each packet has exactly four ABBA and four BAAB blocks; each block has 24 packets of each treatment order; every block always has two A/A controls. Preserve both raw arm labels and actual slot numbers. The v2 collector and scorer MUST share a distinct schema/protocol, refuse v1 as v2, pin their exact code/binary and fixture SHA, and write complete raw transcripts. No v1 reinterpretation or retrofitting already timed data.

For each packet-block, define `d_ib = log((sum of A times in slots 0..3)/(sum of B times in slots 0..3))`; the fixed A/A control remains `abs(log(A4/A5))`. Under the **position-only multiplicative** null (T_{ibj} = t,m_j), the ABBA log-ratio is `log(3/2)`, BAAB is `-log(3/2)`, so per-packet median over 4+4 is zero and `exp(median)=1`. If the true direct/retained time ratio is (r), with multiplicative separable slot effect identical across both arms, the v2 median estimates (r), while v1 reports (3r/2). This cancels the specified stationary slot effect, **not** arbitrary block-by-arm interactions or dynamic treatment carryover.

Recreate full synthetic normal and optimized Python tests: (1) v1 falsely gives 1.5 with no intrinsic difference; (2) counterbalanced v2 gives exactly 1 for the same slot-only null; (3) with separable true arm ratio 1.25, v2 returns 1.25; (4) every packet and block is balanced exactly as declared; (5) A/A p95 remains zero. The new source-only code is NOT yet the production collector or a complete ECDLP benchmark.

## Admission and scientific limits

Do not start a new 2,304-process native panel until v2 source/collector/adjudicator are integrated and source CI, native 48-case parity, authentic 695/701 custody, provider admission and budget gates are satisfied. PR #1706 remains separate and open; CT179/180 are stacked elsewhere. Do not overwrite their branches or original v1 fixture/panel. An actual advantage requires paired same-host cold **complete single-target ECDLP** against strongest rho/BSGS/IC, `C169,C13a,C13b,N2_actual,D`, setup/transfer/corrections/inversion/LA/verification/memory, independently repeated on genuine public targets, statistically defensible CI, signed independent PCC. v2 would establish only more credible transfer-stage pricing, not the solver advantage.

Internal sources reviewed: cryptanalysis `AGENTS.md`, `docs/ACTIVE.md`, `docs/session-logs/2026-11-17.md`, original CT175/176 Rust/Python source, CT179/180 exact code and tests; merged crypto #4215, cryptanalysis #1523, GPU IC #4178, live Richelot #4544. Shared research KB MCP unavailable; targeted repository search and published methodology were used instead, with no novelty claim. External performance-methodology context: Kalibera and Jones (2013), *Rigorous Benchmarking in Reasonable Time*, https://doi.org/10.1145/2464157.2464160. The counterexample above is direct arithmetic, not a claim from that paper.
