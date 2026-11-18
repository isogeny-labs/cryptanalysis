# CT191 source implementation result — actual norm-point price arm

2026-11-17 UTC · producer-only [pcc:unverified].

## What was committed

- Frozen prospective source/cost protocol: `PROTOCOL.md`, commit `b8862e3452265def143af99c07e209d28b157a05`.
- Additive **Rust** package `Cargo.toml` and `src/main.rs`. It retains the six historical CT126 labels/operations but renames its proxy `D` to `D_padd`, adds `N2_actual` as the seventh arm, shifts the existing direct/retained arms without changing their code, and preserves alternating forward/reverse 16 blocks (4 warmup, 12 recording).
- `N2_actual` directly evaluates `curve::pmul(&target.quadratic.f, e, &final_pts[i], 2)`, then matches `Pt::Inf` or affine coordinates via `back6`, reproducing the exact CT125 `descend_point` code path. The scalar labels are fixture setup only; the runtime transfer methods do not accept their logs. A new preflight checks its mathematical result against `D_padd` + identical descent, then confirms target-model admission. These extra preflight checks are outside the timed block.
- `source_contract.py` refuses changes to the historical CT126 Git blob `ac4146577f5019fc17674deb342eb5d9fc749715`, CT125 optimized runtime Git blob `b80eb91a39ae1e87f0fcde95e52ea3d3634558bc`, any unauthorized derivative change, wrong `pmul` or `back6` behavior or missing dependency. The full exact source diff is an equality test, not a list of loosely matched substrings.
- `test_source_contract.py` exercises ten positive/mutated checks in both normal Python and Python -O, entirely without Cargo or native execution.

## Exact-head observed source check

[GitHub workflow #44174277423](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44174277423) completed success for source commit `a7cf4bb2597278d46dee3d5737b9bd2ef6c5a639`. Its decoded job log shows the exact Git blob bindings, source guard `true`, and **10/10 ordinary + 10/10 optimized Python tests** passing. It explicitly reports `rust_native_executed: false`, `full_48_695_701_native_parity_reproduced: false` and `complete_single_target_ecdlp_advantage_established: false`. Later documentation commits are not covered by that head's check until separately observed.

## Critical limits

This proves only *static* code provenance and intentional source shape. **The Rust package has not been compiled or run.** The currently measured `D_padd` from historical CT126 is not a measured `N2_actual`. No physical ratio, native parity from this branch, cost confidence interval, complete-solve win or independent PCC exists here. It remains unknown whether the actual norm step is faster or slower than the proxy.

The CT126 operand cohort is five known-source-scalar fixture points in one direction, **not** the eight exceptional and forty other frozen public selected-call rows and not the original 695/701-object corpus. Even a future native five-point CT191 run does **not** satisfy the 48-packet pricing requirement or standalone cold ECDLP success.

## Reproduction and next experimental acceptance

The cheap source-only check is:

```sh
d=experiments/chained-transfer-public-target/primitive-pricing-01/ct191-actual-norm
python3 -S "$d/source_contract.py"
python3 -S -m unittest discover -s "$d" -p test_source_contract.py -v
python3 -O -S -m unittest discover -s "$d" -p test_source_contract.py -v
```

After **separate** restored Rust/dependency provenance and owner/provider admission, the following is the planned Rust invocation, **not an executed command in this run**:

```sh
cargo +1.99.1 run --release --manifest-path \
  experiments/chained-transfer-public-target/primitive-pricing-01/ct191-actual-norm/Cargo.toml \
  --bin ct191-price
```

Before using any actual primitive prices, independently build and test the original 48 source-prime public packet inputs and extract each *actual* norm preimage without scalar disclosure; verify CT125 whole canonical output and all 21 route counters on every case, then price all distinct operations including `C169,C13a,C13b,N2_actual,D_padd` paired on the same host/operands. Record nulls and negative effects. Only compare complete cold **single-target** transfer-plus-DLP solve against strongest matched source rho/BSGS/IC after including setup, correction, inverse, LA, recovery, verification, memory, uncertainty, independent PCC and budget constraints.

Reviewed: root [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), norm-cost [crypto #4215](https://github.com/isogeny-labs/crypto/pull/4215), consumer [cryptanalysis #1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523), [CT173 source mismatch](../CT173_NORM_POINT_PRICE_PATH_AUDIT.md), concurrent [CT189 #1729](https://github.com/isogeny-labs/cryptanalysis/pull/1729), [CT190 #1732](https://github.com/isogeny-labs/cryptanalysis/pull/1732), [GPU IC #4178](https://github.com/isogeny-labs/crypto/pull/4178) and [central queue #3904](https://github.com/isogeny-labs/crypto/issues/3904). Locked research-KB and crypto-autoresearcher vault contents were not accessed; there is no novelty or literature-absence claim. [pcc:unverified]
