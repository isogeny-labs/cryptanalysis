# Proof and evidence map

| Result | Evidence | Verification status |
| --- | --- | --- |
| Every actual four-pair target sum passes the reciprocal S3 span screen | S3 identity and `BilinearGate.bilinear_column_trace_zero` in the earlier N41 pair-output work; native group-positive at every width; independent Sage target-sum replay | Structural identity inherited; the finite witness bridge is independently checked in Sage |
| A cross term `(tcd)^2+tcd` has absolute trace zero | `BilinearGate.artin_schreier_trace_zero` in `../n41_bilinear_rank_screen_20261013/BilinearGate.lean`, checked with Lean 4.34.1 and `#print axioms` in that experiment | Lean checked under explicit trace laws |
| Witness-centered width-four cross span has rank 40 | `result.json` and independently reconstructed `audit_result.json` | Complete finite native and Sage elimination for the selected regions; exact 40-pivot certificate is not imported into Lean |
| Each of 58 sampled nonempty width-four regions passes the linear screen | `result.json`, frozen deterministic source and seed in `protocol.json`, read-only `verify.py` | Complete native panel; Sage independently checks the witness-centered region and the empty-region control, not all 64 sampled quadruples |
| A region with no valid two-pair partial sum must be rejected | Definition of the candidate family, versioned native check, independent Sage same-edge width-four control | Direct structural implication and finite control |

The full-rank width-four fact is a finite computation. A faithful Lean
completion would import the exact frozen pair points and region law,
formalize the binary-field arithmetic and curve group operation, and check
40 independent cross columns. The previous generic trace theorem does not
by itself prove the finite rank or the sampled region counts; those remain
computational evidence with an independent Sage replay of the central
positive case. No new general theorem is asserted here.
