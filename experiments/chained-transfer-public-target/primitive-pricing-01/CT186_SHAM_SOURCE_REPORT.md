# CT186 — first-four-slot all-A sham assignment diagnostics

2026-11-17 UTC · [pcc:unverified] · PR [#1718](https://github.com/isogeny-labs/cryptanalysis/pull/1718)

## Source-level result

Implemented `ct186_same_route_sham.py` and seven fail-closed `test_ct186_same_route_sham.py` tests. This is a **new source-only** placebo schedule, offline scorer and falsification harness. It does **not execute a native process** and is not an ECDLP transfer or complete solver.

- New distinct protocol `ct186-first-four-same-route-sham/v1`: 48 original public packet indices × 8 blocks × **four** first slots = **1,536 potential fresh-process samples**. Every slot's physical arm is `direct_composite`; A/B is only a sham label, never a native command argument.
- Exactly four ABBA and four BAAB labels per packet, independently randomized relative to original CT183 block parity; deterministic seed 20261118 and wire roster SHA-256 `7cf758b05c82adf2d1e9edc675d10dc5a0bb603a004d51a42f9375a077d75228`.
- Strict complete-order/sample-field validation rejects wrong physical arms, malformed durations including booleans, missing/extra and reordered records, wrong labels, wrong schema, incomplete rows.
- The estimator pairs two placebo labels each block, computes eight block-level log ratios per packet and then a packet-level median; 48 packet effects remain separate. No CI or reported hardware speedup is promoted from these scripted inputs.

## Synthetic falsification table

| Source-only scenario | Same physical route A on all slots | Global median placebo A/B |
| --- | --- | ---: |
| Equal durations everywhere | yes | 1.00× |
| Stationary slot multipliers (3,2,2,3) | yes | 1.00× |
| CT185 assignment-conditioned order nuisance: ABBA (3,2,2,3), BAAB (2,3,3,2) | yes | **1.50× false-label contrast** |

The 1.50× control is deliberately created from *known synthetic* numbers. It demonstrates the sham estimator can flag assignment-conditioned timing confounding under its stated nuisance model; **it is not evidence of such confounding on a real host**. A zero all-A sham cannot exclude A↔B physical route carryover, thermal effects tied to real B execution or other unobserved treatment interactions. Honest real A/B causal interpretation still requires randomized physical order and other controls, not this test alone.

## Reproduction and CI

```bash
root=experiments/chained-transfer-public-target/primitive-pricing-01
python3 -S -m unittest discover -s "$root" -p 'test_ct186_same_route_sham.py' -v
python3 -O -S -m unittest discover -s "$root" -p 'test_ct186_same_route_sham.py' -v
python3 -S "$root/ct186_same_route_sham.py"
```

Exact-code-head [source-only CI #44119777747](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44119777747), tested commit `a12fc45639138865e3612602312c06859dabdc0e`, finished successfully on 2026-11-17: **7/7 normal Python** and **7/7 optimized Python**, plus pinned 1536-slot roster digest. Source CI does not authenticate native performance or count toward independent signed PCC.

Prospective contract was committed first (`0853f71f301dfc1dccfc7c4b0dd7ed51b64fd8e2`), before source `8cf25ded`, test `763923ea` and fix `87251748`. Root context: merged [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), transferred-cost model [crypto #4215](https://github.com/isogeny-labs/crypto/pull/4215), paired IC baseline [cryptanalysis #1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523), original CT182/183 producer/reader and CT185 #1715. Literature checked: Kalibera and Jones, *Rigorous Benchmarking in Reasonable Time*, ISMM 2013, DOI 10.1145/2491894.2464160. Shared research KB MCP and Rust/Cargo were unavailable in this runtime; no novelty/absence assertion.

## Next protected computational gate

To test this on actual hardware requires a separately authorized and versioned **1,536-process** sham producer with the exact authenticated native child, original 48 arithmetic parity, 695/701 custody, binary/host/output hashes, process capture/deadlines, and independent custody. Owner/provider EKS Spot budget and source/CI/PCC gates remain mandatory. Only after that can same-host `C169,C13a,C13b,N2_actual,D` pricing and full cold single-target rho/BSGS/IC/transfer solve comparisons adjudicate a speedup. Every setup, group map, inversion, linear-algebra, recovery and memory cost must be counted. **No native run, paid allocation, full solver, signed PCC, or performance advantage was produced here.**
