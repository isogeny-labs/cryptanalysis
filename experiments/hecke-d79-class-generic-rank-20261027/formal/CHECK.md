# Direct rank certificate check

The toolchain is pinned to `leanprover/lean4:v4.35.0-rc4`; `lakefile.toml` has no external dependencies. From this directory, run `python3 generate.py` to check that the generated Lean source matches the frozen Python/Sage result, then `lake build DirectRankP317`. [build-output.txt](build-output.txt) retains the successful build and `#print axioms` audit: the two projection facts have no axioms, and the four finite minor identities use standard `propext` only.

The Lean declarations directly establish 140 F61 row annihilations, a nonzero projection vector, a 38×38 modular inverse, and a 39×39 mod-2 inverse. The abstract theorem that converts those identities into exact matrix ranks, and the bridge from the curve-point computations to the row entries, remain unformalized. The written argument is in [RESULT.md](../RESULT.md), and [PROOF_MAP.json](PROOF_MAP.json) names the open obligations.
