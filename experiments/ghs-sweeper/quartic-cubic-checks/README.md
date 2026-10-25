# Quartic census and CM proof evidence

Scientific contracts and implementations were committed before execution:

| Phase | Frozen commit |
|---|---|
| Published O3 census | `15e0c097d08216a3bfb3972f6264c1f163cd53f6` |
| First CM screen | `214ebc91c7a77154be87c3c8cfd0e3e902af0ca0` |
| Target automorphisms | `43f833b0b30062697bfc9760bf83f0ade755059c` |
| CM discriminant refinement and Lean core | `4d9121c8c5edba6274c106e7b023b14304ad0486` |

Each command receipt binds its captured stdout/stderr. `environment.json`
records the local tools and exposed hardware. Wall times are execution
receipts only, without calibrated attack-cost or performance claims.

`quality-commands.json` preserves the initial Clippy failure. Attempt 2
passes strict Clippy and all 48 Rust tests. Subsequent Rust changes relative
to the frozen scientific revisions are lint-only: indexed count assignment
becomes enumerated mutable assignment, and divisibility uses is_multiple_of.
`corpus-command-attempt-1.json` preserves the failed expectation of four
transitively audited theorems. The audit also covers generated valid.eq_1;
attempt 2 passes with five. It does not weaken any axiom check.

All three rendering commands were `python3
experiments/ghs-sweeper/render_quartic_cubic.py`, from the repository root,
and exited zero. The first PDF was 74,510 bytes; core PDF fonts and a shared
text font reduced the final result to below the 64 KiB artifact threshold.
No scientific text or evidence was removed for storage. Final PDF hashes
and all six inspected pages are recorded in `visual-inspection.json`.

`historical-evidence-replay.json` verifies the older 32+30+63 frozen entries
and the 15-entry overlap supplement against live bytes. Four mutable gate/
problem files in the 89-entry manifest have explicit old/new versions;
their historical bytes still verify at commit 9ddbe2c6. That manifest was
not regenerated. Its other 85 entries remain live-byte-identical.

The result report, proof map and manifest preserve the distinction between
explicit quartic equations, an abstract torsion kernel, the written
indecomposability theorem and the missing evaluated source-to-target map.
There is no newly certified weak-family, prime-subgroup transport or log.
