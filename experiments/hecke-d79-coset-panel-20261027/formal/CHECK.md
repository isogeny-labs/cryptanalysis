# Order-five coset proof check

The pinned toolchain is `leanprover/lean4:v4.35.0-rc4` with no external dependencies. From this directory, `lake build CosetPanel` builds the actual theorem module. [build-output.txt](build-output.txt) retains the `#print axioms` audit; the four declarations use standard `propext` only.

[CosetPanel.lean](CosetPanel.lean) proves the conditional three-term obstruction for any additive projection into `Fin 5`, checks the four frozen residue-count totals, and checks that the other two residue patterns permit a zero projection sum. The independent Sage audit supplies the exact curve-specific projection hypotheses. The curve bridge and numerical rank formalization are explicitly partial in [PROOF_MAP.json](PROOF_MAP.json).
