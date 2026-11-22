# CT172 — native frozen 48-public-packet replay source

Date: 2026-11-16 (America/Denver). **[pcc:unverified]**. Implementation built as a prospective companion to cryptanalysis #1690 and the CT141 original owner-admission path. Protocol `CT172_SELECTED48_NATIVE_PROTOCOL.md` was committed separately at `6bb280b81052deb1b77ea20f6af0c315fd33ceab` **before** this implementation.

## Concrete change

- New isolated **Rust** binary at [ct172-replay/src/main.rs](ct172-replay/src/main.rs), using the **real CT125 norm-point-reuse Runtime**, not an invented toy curve or reimplementation of group arithmetic.
- Reads the original checked 48-public-packet fixture at compile time, without passing `scalar_OUTSIDE_runtime` to any curve operation. Builds packets from real fixed-model `field_tag`, `model_tag` and canonical 19-word public class keys; does not construct targets from known logarithms.
- Exhaustively enumerates 2 directions × 4 cofactor sectors × 6 externally labelled scalars, including the 8 identity/exceptional cases. Rejects duplicated/missing classes and changed public inputs.
- For every packet runs native direct degree-169, literal two-hop degree-13/13 and retained-lift degree-13/13, with fresh admissions and counters; validates each final norm and group order, complete output key, and the **entire** 21-field cost dictionary against frozen producer observations. Also performs a separate full-group inverse round trip (not charged as free).
- Emits all 48 comparison rows in deterministic JSON; 8 in-memory evidence/schema mutation controls are implemented. Nonzero exit on mismatch. These results are **expected outputs and test intentions, not an execution result**.
- CT126 five-point timings and CT171 source guard are unchanged. A new pull-request workflow is intentionally limited to the original CT171 pinned fixture checks, Rust **parse** and Cargo **manifest** validation; it does not compile/link, execute 48 transfers or price a primitive.

## Reproduction once execution is permitted

First restore the CT141 [frozen crypto dependency](https://github.com/isogeny-labs/crypto/tree/4de29a113dfc1b9d32c1809820b8caa2975042a8), its generated predecessor sources and authenticated model artifacts using the CT137/CT141 procedures. The standalone Cargo project assumes that existing sibling dependency layout (cryptanalysis and crypto) is assembled as the owner prescribed. It does not perform that materialization.

```sh
python3 -S experiments/chained-transfer-public-target/primitive-pricing-01/ct171_selected_coverage.py --self-test
python3 -O -S experiments/chained-transfer-public-target/primitive-pricing-01/ct171_selected_coverage.py --self-test

# These two are source-only (no native evaluation):
rustfmt --edition 2021 --emit stdout experiments/chained-transfer-public-target/primitive-pricing-01/ct172-replay/src/main.rs >/dev/null
cargo read-manifest --manifest-path experiments/chained-transfer-public-target/primitive-pricing-01/ct172-replay/Cargo.toml

# DO NOT RUN until owner/budget admission and sibling source/artifact restoration:
# cargo run --release --manifest-path experiments/chained-transfer-public-target/primitive-pricing-01/ct172-replay/Cargo.toml -- --self-test
```

## Remaining limitations

**Unexecuted**: no typecheck, native linked binary, 48-case parity observation, same-host `C169,C13a,C13b,D` price, cold public-target complete solve, original independent 695/701 raw custody, or signed PCC is claimed. CT172 shares the producer's original CT125 evaluator and therefore is not an independent arithmetic implementation, even after execution. The actual complete-solve benchmark must count startup/setup, norm/transfer/corrections, linear algebra, scalar recovery, verification and peak memory, and compare with the strongest optimized source rho, BSGS and IC on identical public inputs.

Scientific obstruction remains **NATIVE-ADMISSION-STOP + RAW-695/701-CUSTODY + MATCHED-COLD-ECDLP + SIGNED-PCC**. CT167/CT170's transferred sextic-twist toy was slower and should not be recycled as an efficiency lead. [pcc:unverified]
