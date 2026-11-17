# CT188 — physical A/B crossover design and first-order carryover source diagnostics

2026-11-17 UTC · [pcc:unverified] · [prospective protocol PR #1723](https://github.com/isogeny-labs/cryptanalysis/pull/1723) (merged, protocol only), [implementation PR #1725](https://github.com/isogeny-labs/cryptanalysis/pull/1725) (draft).

## Increment beyond CT187

CT187's 1,536-process sham assigns placebo labels but **always invokes the same physical degree-169 route**; it cannot detect actual A/B treatment-dependent carryover. CT188 specifies an additional physical (non-placebo) crossover with eight randomized sequences per public packet: AABB, ABAB, ABBA, BAAB, BABA, BBAA, ABBA, BAAB (two of every arm in each 4-position block). Every packet has four A and four B at **each period**, not just overall; all six distinct two-A/two-B sequences appear and the last two slots remain physical A/A controls.

The fully frozen original 48-public-packet identity and 21-counter dictionary are not touched. The new planner generates 48 × 8 × 6 = 2,304 *planned* fresh-process positions. The exact output depends on the pinned protocol seed; the code derives a SHA-256 for the full ordered roster, but no native process is launched.

## Conditional model and falsification

For log wall time at treatment position i, let x_i=1 when the physical arm is B, z_i=1 when the immediately preceding physical arm within the same block was B (zero at i=0). The seven coefficient columns are:

`[1, i==1, i==2, i==3, x_i, z_i, x_i*z_i]`.

The eight-sequence design has rank **7 over the rationals** on each packet; the code checks this with exact Fraction row reduction. Under the **explicit linear first-order log-time model**, physical-arm cost, prior-B carryover and B×prior-B interaction can be estimated distinctly. Any nonlinearity, thermal drift correlated with individual blocks, effects beyond one lag, packet×time interactions or systematic unrecorded differences can still bias these terms; rank is not causal identification in an unrestricted runtime model. The scorer is intentionally called `adjudicate_untrusted_times`.

Programmed source-only tests cover no intrinsic A/B effect with nonzero carryover, a 1.25× programmed true ratio with nonzero carryover and B×previous B interaction, position balance, exact rank, and refusal of missing/mutated/nonpositive records. These test inputs are algebraic/synthetic, **not measured Jacobian times**. The main v3 collector, strict native transcript reader and any physical run remain future separate, prospectively frozen work.

## Reproduction (source only)

From a complete exact source checkout:

```sh
root=experiments/chained-transfer-public-target/primitive-pricing-01
python3 -S -m py_compile "$root/ct188_physical_crossover_design.py" "$root/test_ct188_physical_crossover_design.py"
python3 -S -m unittest discover -s "$root" -p 'test_ct188_physical_crossover_design.py' -v
python3 -O -S -m unittest discover -s "$root" -p 'test_ct188_physical_crossover_design.py' -v
python3 -S "$root/ct188_physical_crossover_design.py"
```

The [source-only CI workflow](../../../.github/workflows/ct188-physical-crossover-source.yml) contains the same commands; it intentionally has no native child or paid compute.

**Observed exact-source CI:** [GitHub Actions run #44143583837](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44143583837) completed **success** at SHA `6dba406df12de42010f33d13f446ced511e7b9c1` (job `134252579880`): **5/5 normal and 5/5 optimized Python tests passed**, compilation and source-only plan passed. Its pinned roster digest is `1bc8c26a01e7952e57d944fd535c9832607f2ab7bcc910342ad704171ab67af1`, 2,304 planned source-only positions, exact design rank 7. These are source/synthetic tests; not native performance, not full solver evidence and not independently signed PCC.

## Scientific standing and bottleneck

No native measurements, independent original 695/701 custody, authenticated exact Rust 48-case parity, EKS/Spot admission, same-host primitive prices or complete ECDLP solve were obtained. No measured advantage, cross-characteristic map, or formal impossibility theorem is asserted. Independent signed PCC remains unavailable.

**Next decisive gate:** restore the original whole corpus, get exact native Rust replay on the original 48 public packets and budget admission; then run same-host C169, C13a/C13b, N2_actual and D, including randomized physical A/B and all-A sham, before any transfer-cost attribution. Ultimately compare complete *single-target cold* source-prime transfer+solve+verification (including setup/inversion/LA/memory) against matched strongest rho, BSGS and index calculus on identical public challenges and report uncertainty and negative outcomes.

Sources checked: cryptanalysis #1523, #1711, #1713, #1715, #1718, #1719 and CT175/CT187 reports; crypto #3877, #4215, #4178, root queue #3904, AGENTS.md and active session log. Research KB service was not available; this is no prior-art novelty search.
