# Actual canonical-class norm on three fixed prime-field descents

Pre-code protocol ac58df/c3b and ready PR1521 precede this code. The runtime
accepts tagged canonical divisor classes, reconstructs their actual length-three
quotient algebra including nilpotents, evaluates the completed Ciani cover over
an explicit Fq6 embedding and subtracts the geometric plane-section origin.
Original field, polynomial, elliptic and canonical Picard engines are reused.
No scalar label or DLP table is accepted. Native75275f and CLIaf3d78 are unsigned
local evidence; no computational advantage is established. [pcc:unverified]

Run from this directory, with the exact sibling crypto source pin named by
`../g3-norm-upstream-commit.txt`:

```sh
cargo clippy --all-targets --offline --locked -- -D warnings
cargo test --release --offline --locked --lib -- --nocapture --test-threads=1
cargo run --release --offline --locked -- fixtures/q5-request.json /tmp/g3-norm-q5.json
```

Output must be a fresh file. Requests use `g3-canonical-norm/v1`, q5/7/11 and
at most256 classes, at most65,536 bytes. Every class has the exact field/model
hash and canonical19-word exceptional or typical encoding. Unknown fields,
foreign models, noncanonical/rank/offcurve inputs and extra arguments reject.
The fixed instances are correctness fixtures, not a general curve-selection API.
[pcc:unverified]

The full replay is `../check-g3-norm.sh EXACT_CRYPTO_ROOT FRESH_OUTPUT`, with a
fresh build cache outside the raw output and both sources clean. It replays the
pinned producer, four full-domain tests, three bounded CLI golden comparisons,
the two original Lean gates and13 exact consumer PCC bindings. The six existing
CI jobs stay whole; a separate seventh job invokes this replay. Original native
failures remain in versioned evidence. [pcc:unverified]

See `../G3_NORM_DERIVATION.md` and `../G3_NORM_PROOF_MAP.md` for the faithful
written argument and exact partial formalization boundary. All admissible-chart
invariance is a written argument; native alternate-chart controls cover eight
typical classes per field. Runtime support-root work and all setup must be
charged in future comparisons. The broad root regression's missing original
fixture is a separate unresolved gate. [pcc:unverified]
