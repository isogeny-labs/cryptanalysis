# Requirement-to-evidence map

| Requested item | Status | Evidence |
| --- | --- | --- |
| Use the exact N83 W3 plus first-4,000-W4 base | Verified complete | `gate_spec.json` and `inputs.sha256` bind the replayed geometry and all 2,554 representatives. |
| Do not rerun SAT or fixed-offset paths | Verified complete | Those records are inputs only; no solver or offset command appears in `verify.sh`. |
| Assess separator, pair-certificate, and algebraic-index options before data | Verified complete at the stated scope | `REPORT.md` records the literature and exact preflight proofs. |
| Freeze a prospective experiment before data | Not applicable after failed admission | No experiment is represented as admitted. The pre-data gate bytes are frozen by `gate_spec.sha256`. |
| Run a planted control, then ordinary public queries only after it passes | Not attempted by design | The certified ordinary-query admission bound fails before data. `positive_control_sanity` proves why a planted-only pass would be non-discriminating. |
| Preserve failures/timeouts and replay every witness | Not applicable to a no-run gate | No execution row or witness was produced; the prior frozen failures remain unchanged. |
| Produce a formal no-go rather than a pretend experiment | Verified complete | Native Pocklington and exact integer checks in `n83_pdp_resource_gate.cpp`, frozen result in `gate_output.json`. |
| State exact revisit conditions | Verified complete | `REPORT.md`, “Revisit conditions.” |
