# CT193 — full-class binding for public pre-norm operands (prospective)

2026-11-17 UTC · draft cryptanalysis PR #1737 stacked on CT192 #1735 · **[pcc:unverified]**

## Precise defect / mathematical obstruction

CT192's new `ct192_pre_norm_operand` reconstructs a candidate target elliptic point `P` from each admitted public Jacobian class and checks only
`result.norm == norm_point(to, P)`, plus `check_final(&result)`. This verifies `[2]P` after descent, **not** that `P` corresponds to the original route's target *Jacobian class*. `check_final` is applied to the independently recomputed native `result`, not to `target_phi(to, P)`.

Doubling is noninjective whenever a nonidentity rational 2-torsion point exists. On the nonsingular curve `E/F_5: y^2=x^3-x`, let `P=(2,1)`, `T=(0,0)`, and `Q=P+T=(2,4)`. Then `P != Q`, `2T=O`, and `2P=2Q=(0,0)`. Thus a comparison of norm-point doubles cannot by itself exclude a wrong pre-norm point differing by 2-torsion. Whether the target Jacobian transfer distinguishes these points is a separate question; the probe must check directly rather than assume it.

## Pre-registered change

Modify **only the injected diagnostic method** in `ct192-public48-norm/source_contract.py` (do not edit CT125 original source or its frozen Git blob). After reconstructing `operand` and `result`, retain the old norm equality, then explicitly compute `target_phi(to, operand)` and require equality with `result.class`. Both calls are actual CT125 target arithmetic; this is a consistency guard rather than an independent proof. Preserve `self.check_final(&result)` and all downstream exact 19-word result/counter replay. This additional target-phi call increases diagnostic counters, but the CT192 timing driver resets counters before the replay, so measured route counters remain expected to be unchanged. Neither source scalar labels nor known generator multiples may enter the probe.

Add a standalone pure-Python finite-field regression for the doubling counterexample, plus a fail-closed test on the generated derivative requiring both comparisons and their ordering. Avoid adapting test expected values or original fixture to make a failure disappear.

## Success/failure and scope

The new source test passes on both standard and `python -O` execution and the preexisting CT192 full source suite remains green. Rustfmt parsing may be checked by source CI if available; these checks are **not** Rust typechecking or a 48-case native execution. If the new class equality fails during a later native all-48 replay, retain that failure: it is not permissible to relax the class binding to norm-only. The additional check does not establish an independent PCC verdict or a speedup.

The research goal still requires authenticated original 695/701 corpus custody, owner-admitted native 48-case replay, same-host actual `C169,C13a,C13b,N2_actual,D_padd` pricing with the existing sham/crossover controls, and complete identical-target cold transfer/IC/rho/BSGS solving with every phase and memory counted. No EKS/Spot spend or protected merge is authorized by this protocol.

## Primary source scope

- CT125 original `experiments/chained-transfer-public-target/fixed-jacobian-chain-evaluator-02/derived/lib.rs` (Git blob `b80eb91a39ae1e87f0fcde95e52ea3d3634558bc`)
- CT192 source `experiments/chained-transfer-public-target/primitive-pricing-01/ct192-public48-norm/source_contract.py`, `src/main.rs`, `PROTOCOL.md`; frozen selected 48 Git blob `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3`
- [CT192 #1735](https://github.com/isogeny-labs/cryptanalysis/pull/1735), [CT191 #1734](https://github.com/isogeny-labs/cryptanalysis/pull/1734), [root crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), [cost frontier #4215](https://github.com/isogeny-labs/crypto/pull/4215).

The research-KB MCP and authenticated original corpus are not available in this connector environment. No prior-art novelty claim is made. **[pcc:unverified]**
