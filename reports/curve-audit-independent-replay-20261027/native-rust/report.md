# Native Rust followup for P-192/P-224 curve audit

2026-10-27 05:49 UTC. Conductor T-510 (exclusive memory-heavy build) and T-511
(source fix). Source before the fix was cryptanalysis commit
`50bd627d77df9568a6466546a78b910ac498d9f6`, whose curve-audit code was
the frozen producer `dc73f9791dc7d2c61e0c77572d2c3aaeedb30436`.
This followup validates the *repaired* Rust source and does not alter the
earlier independent Python result or historical fixture JSON.

## Observed sequence

| Step | Exit / result | Evidence |
| --- | --- | --- |
| `cargo test --locked --manifest-path bindings/rust/Cargo.toml -p ca-curve-audit` on unchanged source | 101, compile error E0277 at both `format!("{:x}", ...)` digest sites | [stderr](cargo-test.stderr), [receipt](cargo-test-receipt.json) |
| Source repair | Replaced unsupported `LowerHex` formatting of `sha2 0.11.1` digest arrays with explicit lowercase byte hex. Added the standard SHA-256 `abc` vector. | `bindings/rust/curve-audit/src/main.rs` in this PR |
| Same locked test command on repaired source | 0; **15 passed**, 0 failed; input hashes unchanged during the run | [stdout](cargo-test-fixed.stdout), [receipt](cargo-test-fixed-receipt.json) |
| Locked binary build and fresh `audit` CLI for P-192 and P-224 with exact checked-in prime certificates, `--max-k 6` | Three exit codes 0; candidate order, trace, twist order, status and verdict match each archived JSON | [CLI receipt](native-cli-receipt.json), [comparison](native-controls-and-comparison.json), [P-192](cli-p192.stdout), [P-224](cli-p224.stdout) |
| P-192 without certificate | Exit 0; order remains `supplied_unverified` | [output](cli-p192-no-cert.stdout) |
| Altered P-192 `b` with original certificate | Exit 2; `prime certificate is bound to different input bytes` | [control input](p192-altered-b.json), [stderr](cli-p192-misbound.stderr) |

The build used `CARGO_TARGET_DIR=/var/tmp/curve-audit-native-20261027-target`
on the existing Spot host after the other owner's build exited. The target
directory is a disposable local build cache; no new instance or EKS job was
started. All stdout, stderr, commands, exits, timestamps and file digests are
in the linked receipts. `rustfmt --check` and `git diff --check` passed.
The host ran `cargo 1.99.1` and `rustc 1.99.1` on
`Linux 6.18.54-121.166.amzn2023.x86_64`. The failed-at-compile receipt's
`main.rs` SHA-256 equals the immutable branch-head blob; comparison with the
successful test receipt shows that only `main.rs` changed among the bound
inputs. The exact source-file hashes are in both receipts.
The fresh binary SHA-256 was
`83380088501971481dd66260afb52c5758971011c63ca85a826c53382f9a4a0f`.
Its embedded source digest
`c1c3347beeeed6ec8474d16789e9fa347f25d2aa2832733d3944bc787722cf79`
was recomputed independently from the four exact Rust source files and
matched both CLI reports. It differs from the frozen producer digest because
`main.rs` changed in this repair; equality to the old source digest is no
longer expected.

The fresh CLI reports identify the curve order as a
`hasse_unique_multiple_certificate` for both inputs, with
`incomplete_assessment` overall. The source-level tests exercise certificate
rejection, the no-certificate status, and selected parser and arithmetic
paths. This is concrete build/runtime evidence for these fixtures, not a
proof of all 61 criteria, every parser path, or the actual curve orders in
Lean. The [original independent replay](../report.md) checks the certificate
arithmetic separately. The [squared Lean bridge review in PR #1200](https://github.com/isogeny-labs/cryptanalysis/pull/1200)
proves a conditional natural-number implication; the field, group, Hasse,
Lagrange, actual cardinality and Rust refinement bridges remain open. A fresh
Sage point count is still unavailable on this host.

No benchmark or performance measurement was made, so the canonical
performance graph and dashboard data have no new value to plot. The
[validation boundary diagram](validation-boundary.svg) records this new code
validation status. The accompanying [PDF](report.pdf) was rendered from
[`report.tex`](report.tex); the original packet's PDF remains a dated record.
