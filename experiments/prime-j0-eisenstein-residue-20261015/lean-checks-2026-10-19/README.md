# Fresh Lean rebuilds (2026-10-19)

These dated receipts preserve the fresh outputs from the pinned Lean checks without replacing the original hash-bound receipts beside each module. The checks ran with the repository's `leanprover/lean4:v4.34.1` toolchain (`Lean 4.34.1`, commit `5045d0056413266e57c625dcd7c365b10e377c52`, x86_64 Linux). The installed binary SHA-256 was `47bf4bbd78f70c2e9670598ab7124d92b6efb7330ff33e5fbb4030f6fd72e4e4`.

All 19 checker scripts exited successfully and recorded their source hashes, build commands, outputs, and `#print axioms` results. The 16 `check_*_lean.py` scripts cover checkpointing, digit graphs, Horner, joint Horner/seed graphs, radix-4033, rotated radix, secp256k1 scalar/τ identities, and sparse radices. The three `verify_triple*_lean.py` scripts cover the 81, 243, and mixed-radix modules. Standard Lean foundations are reported in each receipt; no `sorryAx` was found. `lean4checker --fresh` was unavailable, and no fresh-checker claim is made.

The fresh receipts are:

- [Checkpointed sparse](checkpointed-lean-check.json), [checkpointed radix family](checkpointed-radix-family-lean-check.json), [digit graph](digit-graph-lean-check.json), and [Horner](horner-lean-check.json).
- [Joint Horner](joint-horner-lean-check.json) and [joint seed graph](joint-seed-graph-lean-check.json).
- [Radix-4033](radix4033-lean-check.json), [radix-4033 bounds](radix4033-bounds-lean-check.json), and [radix-4033 selector](radix4033-selector-lean-check.json).
- [Rotated radix step](rotated-radix-step-lean-check.json), [subgroup scalar radix](secp256k1-scalar-radix-lean-check.json), [τ denominator](secp256k1-tau-denominator-lean-check.json), [τ formula](secp256k1-tau-formula-lean-check.json), and [τ normalization](secp256k1-tau-normalize-lean-check.json).
- [Sparse radix family](sparse-radix-family-lean-check.json) and [sparse τ radix](sparse-tau-lean-check.json).
- [Triple-243](triple243-lean-check.json), [triple-81 digit](triple81-digit-lean-check.json), and [triple mixed radix](triple-mixed-lean-check.json).

After the matching Lean 4.34.1 builtin `leanchecker` became available, all 26
research modules were rebuilt in dependency order and replayed by the kernel
checker. The fresh [kernel-replay record](leanchecker-kernel-replay/README.md)
preserves the module source hashes, toolchain hashes, build output, and checker
output. This is builtin kernel replay; `lean4checker --fresh` remains
unavailable, and no external-checker claim is made.

These checks verify the committed Lean statements and their recorded dependencies. They do not establish a source-level refinement from the native Rust field/point operations to the abstract point maps, nor do they close any curve-wide group-law proof gap.
