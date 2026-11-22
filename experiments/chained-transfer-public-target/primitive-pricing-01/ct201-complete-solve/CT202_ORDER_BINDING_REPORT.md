# CT202 — counterexample-based source audit of complete ECDLP timing evidence

Date: 2026-11-18 UTC. Scientific standing: **[pcc:unverified]**. This extends [draft PR #1766](https://github.com/isogeny-labs/cryptanalysis/pull/1766) without changing or rerunning the original Jacobian transfer.

## New defect demonstrated

CT201's first source reader scores an unordered collection of declared block/arm times. It does not distinguish a properly counterbalanced experiment from one systematically putting `transfer` last in every block. Moreover, it accepts a `rho_sham` record from an entirely different declared executable digest. Both conditions can appear in a synthetic document that CT201 otherwise scores, with a perfectly passing A/A timing ratio. Neither represents adequate experimental controls. This is a **design/validation omission**, not evidence that any past native logs were compromised.

Two executable counterexample tests first call the unchanged CT201 `evaluate()`, confirm the malformed design is accepted as a complete set of 10 blocks or an A/A-pass, and then demand rejection from CT202. They pass.

## Prospective correction

The [frozen design](CT202_ORDER_BINDING_PROTOCOL.md) requires exact chronological rows in whole ten-block Williams cycles, 50 fresh-process records per cycle. `0=transfer, 1=rho, 2=rho_sham, 3=bsgs, 4=ic` and base order `(0,1,4,2,3)`; first take all five cyclic arm relabelings, then the five corresponding reversals. Independently checked: 25 position/arm cells all have count **2**; 20 distinct ordered first-order carryover pairs each have count **2**. SHA-256 of compact JSON of the ten named-arm rows: `16e26c6e33e8147732de1816879f6c1475711af3968990aa8184151c9c85c9fe`.

CT202 also requires a stable declared `binary_sha256` per arm for every block and the identical declared digest for `rho` and `rho_sham`. All five original mathematical, phase, memory and process-wall obligations stay in CT201, which remains unmodified. CT202 refuses incomplete ten-block cycles and retrospectively reordered rows before calling CT201 scoring. Its result explicitly states that chronology and executable digests are **untrusted producer declarations**.

## Reproduction and source validation

```sh
d=experiments/chained-transfer-public-target/primitive-pricing-01/ct201-complete-solve
python3 -S -m unittest discover -s "$d" -p 'test_ct20*_*.py' -v
python3 -O -S -m unittest discover -s "$d" -p 'test_ct20*_*.py' -v
python3 -S -m py_compile "$d/ct201_complete_solve_gate.py" "$d/ct202_balanced_order_gate.py" "$d/test_ct201_complete_solve_gate.py" "$d/test_ct202_balanced_order_gate.py"
python3 -S "$d/ct202_balanced_order_gate.py" /path/to/future/untrusted-ct201-v1.json
```

[Exact-source CI #44263113035](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44263113035) **passed** at source/workflow head `bb31815876aa80853aec27239f6021335ed74c88`: 28/28 normal tests and 28/28 `python3 -O -S` tests, plus compile. Of these, eight are newly added CT202 source/synthetic controls. `lab-parity` also passed at that head. Tests include adversarial candidate-last ordering, same-timing sham-binary substitution, candidate binary drift, partial cycle, reversed blocks, mathematical roster balance and complete two-cycle acceptance.

All positive timing inputs are deliberately **synthetic**. No real cold ECDLP solution or wall timing, native Rust compilation, original 695/701-record fixture replay, primitive cost measurement or PCC signature was produced. The unsigned source test does not authenticate external runtime.

## Remaining decisive gates and operational boundaries

1. Recover *authorized* access to the byte-identical original model inputs; CT200 original hydration [run #44247758448](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44247758448) stopped at S3 HTTP 403 before Rust compilation.
2. Native Rust 1.99.1 release typecheck, all-48 parity against original CT125 transfer, then independently authenticate the original 695/701 evidence.
3. With an unchanged approved EKS/budget/corpus protocol, physically price paired same-host `C169`, `C13a`, `C13b`, `N2_actual`, `D`. The CT198 direct-vs-retained norm count cancels; compare `C13a+C13b-C169` without double credit.
4. Run actual cold complete single-target solves (transfer, strongest optimized rho, BSGS, IC) on a balanced declared roster, with binary and command custody, raw runner traces, all setup/transfer/LA/recovery/verification/wall/memory, uncertainty and independently signed PCC. Reject a losing route and record the negative result.

No EKS Spot, paid hardware, GitHub protection bypass, new benchmark, artifact substitution or merge occurred. The original CT201 evidence schema is still v1 and the new guard is opt-in `ct202_balanced_order_gate.py`, so no historical result is silently reinterpreted.

Sources checked: merged crypto #3877, #4215 and #4178; cryptanalysis #1523, #1748, #1756, #1761, #1766; root AGENTS and current session logs; crypto queue #3904. Shared research-KB service is unavailable through this runtime; there is no novelty or exhaustive-prior-art claim. [pcc:unverified]
