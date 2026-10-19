---
title: "n = 83 K600 rotation-key probe: a complete Frobenius-class invariant as the rank-stage key, end-to-end cold"
date: 2026-10-19
---

# n = 83 K600 rotation-key probe: a complete Frobenius-class invariant as the rank-stage key, end-to-end cold

**Status (2026-10-19): protocol frozen, Tier 1 run started; no result yet.**
The [protocol](protocol.json) and the [schedule](schedule.json) were
committed before any Tier 1 timing. The run is
RUN_URL. Every number below that is not from that run comes from the
cloud-agent VM and is a **local diagnostic**, not timing evidence (see
[`smoke/`](smoke/README.md)). Exactness results are exact wherever they were
run.

## Question

The n = 83 a = 1 K600 one-target index-calculus baseline is the rank-probe
producer, `koblitz-n83-rankprobe-20261019` (PR #980, run 39214027289,
producer digest `d4394df3...`): end-to-end cold `S` 6.39, gap to the tuned
rho rT770 64.0 [53.7, 78.0]. Its rank stage is 87% of end-to-end cold: 600
attempts, about 1.69 M probes each, 141.5 ns per probe on the runner. In
that experiment's local profile, lift_scan (the least rotation of each
partner's normal-basis word, the table key) is the largest piece of a probe
(54–62 ns of 233), and a branch-free rewrite of it gained only about 1.15x.

The lead is proposal IDEA-20261015-2d8e5a (crypto-autoresearcher): key the
table by something invariant under the Frobenius rotation that is cheaper
than a representative, and pay for exact canonicalization only at a hit.
Does that lower the **end-to-end cold** cost, with every rank relation,
every per-attempt probe count and the factor-log table unchanged? This is an
iteration under AGENTS.md "Success criterion".

![Design (from the frozen protocol; not a result). Source:
[figures/design.tex](figures/design.tex), vector:
[figures/design.pdf](figures/design.pdf).](figures/design.png)

## The key (derived; checked exhaustively at small n)

A normal-basis word v of GF(2^83) is an element of the ring
R = F2[X]/(X^83 + 1), and the Frobenius rotates it, which is multiplication
by a power of X. Define **rotkey(v) = v^83 in R**.

- **Invariant.** (X^s v)^83 = X^(83 s) v^83 = v^83.
- **Complete.** X^83 + 1 = (X + 1) Φ83, with coprime factors. Φ83 is
  irreducible over F2 because 2 has order 82 mod 83 (2^41 ≡ −1). So
  R ≅ F2 × F_{2^82}. If v^83 = w^83, the parities agree (a^83 = a in F2)
  and ξ^83 = η^83 in F_{2^82}. Then either ξ = η = 0, or ξ/η is an 83rd
  root of unity, and those are exactly the powers of X. Hence v = X^s w.

So rotkey(v) = rotkey(w) exactly when lift_scan(v) and lift_scan(w) are the
same word. **There are no false hits and no merged table entries**, by
algebra, not by a probability bound. The key is 83 bits, so it fits the
key field of the 16-byte compact slot.

The proposal's own form, (Σ x_i w^i)^n mod a 61-bit prime, has false
matches with probability about n/p per pair. It needs 11 table loads plus
about 9 64-bit modular multiplications, and duplicate keys would shadow
table entries. The ring power has none of these problems and uses the
carry-less multiplier. A crate test checks the condition the argument
needs. Exhaustively over all words, v^n separates the rotation classes
exactly at n = 11, 13 and 19, where 2 is primitive. It merges classes at
n = 7 and 17, where 2 is not primitive: that is the negative control.

## Design analysis (local)

All from [`smoke/design_inputs.json`](smoke/design_inputs.json) and the
files it cites.

| Question | Answer |
| --- | --- |
| Key cost per word | rotkey 21.8–22.3 ns against lift_scan 38.5–43.8 ns, batch throughput on 4,096 independent words (about 0.56x). A dependent chain costs 40.5 ns per key, so the gain needs independent keys, which a state's 332 partner words are. The loop computes them in one batch per state. |
| Collisions on the K600 stored set (exact, restored index) | 29,878,182 stored canonical keys give 29,878,182 distinct rotation keys: **0 collisions**. |
| False hits per probe (exact) | **0** in 983,094,828 probes. The planted arm checked every probe of a full rank stage against lift_scan and the compact table. |
| Hit-time verification | One lift_scan plus one compact-table lookup per hit, for the partner shift and a check. There were 600 hits per rank stage (one per attempt), about 0.1 ms in all, against about 10^9 probes. |
| Table layout | Unchanged. The key fills the 83-bit key field and the packed value is the same. The rotation-key table is a second 2^26 × 16-byte table (1 GiB; a rank process peaks at about 2.88 GB, against 1.83 GB). It is filled from the compact table inside the rank-stage interval: 7.0–8.8 s locally, charged to the candidate. |
| Exactness | The whole stage stays identical, including the per-attempt probe counts (next section). |
| Local rank stages (diagnostic) | Run on the inputs of run 39214027289 block K1, as concurrent processes on a loaded VM. Frame against rotkey: 360.3 / 279.8 s (three processes), then 304.6 / 274.4 s (two processes, CPUs swapped). Per probe that is 366 / 277 and 310 / 270 ns. |

**The candidate is promising.** The local rank stage ratio is
1.11–1.29x, and the key alone costs about 0.56x lift_scan. So it was built
and frozen.

## Exactness argument and gate

The rotation-key loop (`KIC_RANK_SOLVE=rotkey`) is the frame loop, code for
code, up to the key.

1. **Same probes.** It emits the same partner words in the same order, then
   computes rotkey of all of them in one batch, prefetching each home slot.
2. **Same hits.** It looks up rotkey(partner) where the frame loop looks up
   lift_scan(partner). The rotation-key table holds the same key → value
   map, because rotkey is injective on the stored canonical words. So every
   probe has the same hit status and, at a hit, the same packed value.
3. **Work at a hit only.** At a hit, lift_scan supplies the partner shift,
   and the hit is checked against the compact table (a panic on any
   difference). Then the frame loop's exact S3-order resolution, lift and
   relation check run unchanged.

So the first hit is the same in every attempt, and so are its resolution
order, relation and probe count. The gate is therefore the full identity,
with no weaker fallback: per block, one relation digest, one 600-entry probe
vector, one root-call count and one set of point-addition counters across
kP, kK, kKaa and kKX. Every rank process must also reproduce B's factor-log
table. The rotation-key counters are gated too:

- 0 collisions on the 29,878,182 stored keys;
- the carry-less (pclmulqdq) kernel;
- at least one verified hit per attempt;
- equal verified-hit counts in kK, kKaa and kKX.

Locally, every full rank stage met this identity against the archived kP
row of run 39214027289 block K1: `frame`, `rotkey` twice and
`rotkey_plant` (see [`smoke/rank_exactness_local.json`](smoke/rank_exactness_local.json)
and [`smoke/rank_pair_local.json`](smoke/rank_pair_local.json)). All 21
producer tests pass, including the three new ones (completeness at small
n; the kernel against the reference; the rotkey loops against the frame and
S3 loops on 40 planted targets). The 4 tuned-rho tests and the 24 lift2
tests also pass.

## Frozen Tier 1 design

The setup is the rank-probe experiment's: one GitHub `ubuntu-24.04` runner,
one pinned CPU, and a fresh process per run. Every IC arm runs
`ic_online_rotkey_r770`, which is the rank-probe producer plus the two new
`KIC_RANK_SOLVE` values. The derivation checks `d4394df3...` before adding
them.

| Arm | Kind | Rank solve | Role |
| --- | --- | --- | --- |
| `cP` | cold | (none) | **baseline** cold (the rank-probe producer's cold path) |
| `cK` | cold | (none) | **candidate** cold (the same code, its own processes) |
| `rT` | rho | — | tuned rho rT770 |
| `kP` | rank | `frame` | **baseline** rank stage |
| `kK` | rank | `rotkey` | **candidate** rank stage, table build included |
| `kKaa` | rank | `rotkey` | A/A of kK |
| `kKX` | rank | `rotkey_plant` | planted positive control: lift_scan, the compact lookup and the canonical word's key redone on every probe, and compared |

- **Cold panel.** 20 new public points, role `rotkey-cold-v1`
  ([`make_targets.py`](make_targets.py)). They are checked disjoint from
  every earlier n = 83 panel of the law, including:
  - `rankcut-cold-v1` and `rankprobe-cold-v1`;
  - the parallel experiment's `indexlift-cold-v1` (seeds 0..63, a
    superset of its 20);
  - the 64 n131-ref-walk `eval` points.
- **Rank blocks.** K1–K4 use the new rank seeds 501–504 (401–404 belong
  to the index-lift experiment).
- **Primary (pre-registered).** R = E2E(kP, cP) / E2E(kK, cK), the
  end-to-end cold ratio. It uses a paired bootstrap over blocks, then
  attempts within blocks, then points (10,000 draws, seed 20261020).
  **Improvement iff the 95% lower bound of R is above 1**; regression iff
  the upper bound is below 1; otherwise not separated. **Invalid** if any
  gate or control fails or any scheduled row is missing.
- **Controls.**
  - A/A: E2E(kK, cK) / E2E(kKaa, cP) and cold cK / cP must both be inside
    [0.97, 1.03].
  - Planted: kKX / kK per attempt must have its lower bound above 1.
- **Power.** [`power_check.py`](power_check.py) writes [`analysis/power.json`](analysis/power.json). It uses 200 simulations per cell with 300 bootstrap draws each and the frozen paired bootstrap. The prior is run 39214027289's kP/kPaa attempts and cR/cP cold times, the baseline's own code on the same kind of runner. Power is 1.00 for 2, 3 and 4 blocks at end-to-end effects of 1.02, 1.03 (the minimal effect of interest), 1.05 and 1.10. The rejection rate at no effect is 0.075, 0.045 and 0.010 for 2, 3 and 4 blocks. The design runs 4 blocks, the frozen minimum, which puts the no-effect rate below the nominal 0.025.

## Files

| File | Role |
| --- | --- |
| `protocol.json`, `make_protocol.py`, `schedule.json`, `make_schedule.py` | frozen protocol, its builder, frozen run order |
| `make_online_source.py`, `make_rankprobe_source.py` and its five verbatim parents, `online/`, `lift2/` | the rotation-key producer (the rank-probe derivation verbatim, digest-checked, plus `KIC_RANK_SOLVE=rotkey \| rotkey_plant`) |
| `restore.py`, `check_log_table.py` | restore and digest-check crypto 770f6a69 and every local source; re-verify B's factor-log table |
| `make_targets.py`, `inputs/cold_targets.json` | the new cold panel |
| `make_power_prior.py`, `inputs/power_prior.json`, `power_check.py`, `analysis/power.json` | power prior (run 39214027289), simulation, result |
| `arm.py`, `run_schedule.py`, `verify_receipt.py` | one arm per pinned process, the schedule runner, gates and decision rule |
| `figures/design.*` | design diagram (TikZ source, PDF, PNG) |
| `smoke/` | local diagnostics: key microbenchmark, full local rank stages, tests, runner smoke |
| `README.pdf` | this report: `pandoc README.md -o README.pdf --pdf-engine=pdflatex -H report_header.tex --lua-filter report_filter.lua -V geometry:margin=2cm -V fontsize=10pt -V colorlinks=true` |
