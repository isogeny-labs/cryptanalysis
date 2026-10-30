# Pinned finite-matrix check

The toolchain is `leanprover/lean4:v4.35.0-rc4` with no external dependencies. From the experiment directory, `python3 formal/generate.py` checks that the generated Lean source still matches the hash-pinned class receipt and independently audited analysis. From this directory, `lake build RankP941` builds the actual module. [build-output.txt](build-output.txt) retains every `#print axioms` result: four row-kernel facts are axiom-free; the finite coordinate and inverse identities use only standard `propext`.

The module contains both direct and Hecke matrices, two independent F5 kernel vectors, inverse certificates for 38×38 minors modulo 5, and inverse certificates for 40×40 minors modulo 7. The mathematical implications for rank and the bridge to the Sage curve points are written in [RESULT.md](../RESULT.md) and remain partial in [PROOF_MAP.json](PROOF_MAP.json).
