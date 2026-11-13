# Actual q223 Frobenius-compatible symplectic kernels

Unsigned nativec88589 enumerates all1,451,520 distinct symplectic actions
and checks the original135 Lagrangians. All120,960 actions matching the
actual bitangent cycle type and rational2-torsion fixed count have one
stable kernel. Every matrix is retained in a13,063,688-byte binary.
[pcc:unverified]

Read-only replay907dfc independently uses Gaussian ranks, quadratic truth
tables and a centralizer count12; it reads every row and reproduces the
single conjugacy-class size120,960. It is a different mathematical route,
not a trusted producer-independent execution backend. [pcc:unverified]

The full written polarization audit and exact fixed-degree obstruction are
in ../KERNEL_OBSTRUCTION_DERIVATION_01.md,c2270b. A different gluing on
Res(E) remains a proposed longer-chain route,../GLUING_CHAIN_PROPOSAL_01.md.
No new nondual map or computational advantage is implemented here.
[pcc:unverified]

```sh
export N4_KERNEL_CENSUS_OUT=/tmp/unique-output/all-symplectic-matrices.bin
cargo test --release --offline --locked --manifest-path \
  experiments/chained-transfer-public-target/kernel-census/Cargo.toml \
  --lib -- --nocapture --test-threads=1
```

The output parent must already exist outside the source tree; the binary
must not exist. The replay crate consumes that exact file read-only.

Five named Lean declarations392a95/039ca3/9f99f1/e7e736/ea637d pass both
unchanged original4.35/4.34.1 gates:8 audited declarations including3
generated count equations,zero trusted. Actual group cardinality, native
execution, theta/Galois/polarization and Jacobian geometry remain written
bridges. The first failed build and exact statement-preserving tactic
correction are retained6956b2. [pcc:unverified]
