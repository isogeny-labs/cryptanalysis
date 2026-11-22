# Exact W20 source-selector projector and first circuit

The frozen W20 pair-product map has an explicit 19-coordinate left inverse. Exhaustive evaluation over all **524,288** selector codes verified that the decoder recovers each source code, projects its product unchanged, and reconstructs its source endpoint. Under the projector membership equations, the 19 source selectors are uniquely determined by the pair output and its inverse. The seven-pair constructed relation satisfies every row of the resulting circuit.

The selected seed is 898618 on `EC1N131Ckb1heb5f1998f20b` over `GF(2)[t]/(t^131+t^13+t²+t+1)`. Each pair output `a` and inverse `b` obey `ab=1` and `P(s)=(1+h²)a+h²b`. The frozen product basis has rank 19, with pivot coordinates 21–39. The decoder in `selector.py` inverts that pivot minor over `GF(2)`. A product `p` is supported exactly when `encode(decode(p))=p`; the decoded source endpoint is then a linear function of `p`. `SelectorProjection.lean` proves the abstract membership and uniqueness statements under the explicit left-inverse hypothesis, with no reported axioms. The concrete basis and all 19-bit codes are checked in `basis_result.json`; the exact field-to-Lean bridge is in `PROOF_MAP.md`.

| Formula | Variables | Clauses | Native XOR rows | Bytes |
| --- | ---: | ---: | ---: | ---: |
| Prior inverse-output form | 217,842 | 423,142 | 73,828 | 11,914,495 |
| First projector form | 218,397 | 423,009 | 74,516 | 12,735,095 |

The first form materializes 131 intermediate product bits and reconstructs a projected product from them. It removes free source selectors but adds 555 variables and 688 XOR rows. The monitored one-worker control build completed in **65.6303055 s**, below its 120 s and 4 GiB caps, with sampled combined RSS 182,239,232 bytes. Formula construction consumed 45.258296292 s inside that interval; this host has no isolation receipt. Its constructed assignment passes all 423,009 clauses and 74,516 native XOR rows. Source, compiler-independent Python code, basis receipt, public circuit dependencies, input fixture, limits, and formula hash are in the frozen protocols. Run `python3 -B verify.py` for the read-only receipt check.

The measured formula growth motivates the direct-parity variant: emit the 112 product-image checks and 19 derived source bits directly as XORs of the output and inverse wires, without materializing intermediate product bits. That version is frozen separately for an exact constructed-control comparison. This is a component encoding with `candidate_id: null`.
