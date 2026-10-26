# Fixed software checks for the Hess inclusion corollary

Date: 2026-10-24. Classification: theorem/identity and native software unit
verification, not an empirical comparison, benchmark, or new curve-search run.

The owner's original family/criterion and total-cost objectives remain open.
This check does not substitute for the 355 pending denominator jobs. Those
jobs must wait for the missing canonical experiment protocol tooling to be
located. No `experiment.protocol/v1` or statistical control contract is
invented here. The controlled-experiment skill classifies theorem/identity
claims as requiring proof, and exact computations as requiring reproducible
verification, rather than statistical controls.

Freeze the example, this contract and the proof text in git before running
the new assertions. The example's fixed unit cases are:

1. Relative degree 2, base degrees 1, 2, 3 and 4, coefficient b=2 in the
   deterministic binary power basis. Test a=0 and the first absolute-trace-one
   element. Expect gamma=1 and witness genus 2 in each case.
2. Base degree 1, relative degree 3, a=1, b=2 in modulus 11. Expect
   gamma=2, beta=3, m=3, genus 6, and gamma/beta annihilators 7 and 9.
3. Base degree 1, relative degree 4, b=2 and the first trace-one a. Verify
   the field identities and genus <=14. Also check the historical
   base-degree-2, relative-degree-5, a=236, b=166 coefficient: trace(a)=1,
   all parameter conditions hold and the witness genus is <=30. Neither
   assertion says the witness is a minimum-genus presentation.
4. Reject b=1, b=0 and a out of range in the cubic pair; reject relative
   degree one. No conclusion about subfield/Koblitz inputs is licensed.

Every positive case checks gamma*beta=sqrt(b), relative traces, annihilator
divisibility, the exact-constant condition, joint period and the stated genus
bound using both log-table and raw polynomial arithmetic. No curve, Jacobian,
generator, target or planted log is constructed. No cost, unusualness, random
yield, optimality or publication-novelty conclusion is allowed.

Commands, from the repository root:

```sh
cargo fmt --manifest-path experiments/ghs-sweeper/Cargo.toml -- --check
cargo clippy --locked --manifest-path experiments/ghs-sweeper/Cargo.toml \
  --all-targets -- -D warnings
cargo test --release --locked \
  --manifest-path experiments/ghs-sweeper/Cargo.toml --example hess_scope
```

The figure inputs are fixed too: plot the exact integer expression 2^N-2
at N=2,...,13, with the ordinate labelled an existence upper bound. There
is no empirical confidence interval or performance ratio. The diagram
contains symbolic objects and published theorem implications, not new
curve IDs or isogeny edges.

The proof's hypotheses, field conventions and open obligations are recorded
in HESS_SCOPE.md. Retain the actual exit statuses and any failed unit output
under scope-checks/. A failed assertion is an implementation/proof-check
failure and blocks that software certificate; do not change its mathematical
claim or silently discard the failure. Passing units do not replace the proof.
