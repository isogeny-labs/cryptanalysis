# Public-target destination calculus for chained transfers

Prospective continuation of the completed forward transfer and independent
canonical-class norm in parent PR1521. The existing N4/B2 solver is reused;
this is not a claim to a new solver or an algorithmic speedup. [pcc:unverified]

Follow [PROTOCOL-01.md](PROTOCOL-01.md). P1 supplies a strict public-Q interface
and a five-target bounded correctness smoke. P2 supplies explicit field,
elliptic/plane model, basepoint and completed-transfer/norm bridges. All source
and protocol changes land before new cases or native implementation.

| Requirement | Current status | Checkable completion |
| --- | --- | --- |
| Prior work | Source reviewed, unsigned | Twelve whole originals in parent b992d8; source catalog |
| Public-Q IC/rho APIs | Not implemented | Literal derivative, strict input, original verification |
| Five public target solves | Not attempted | All five within original six-attempt cap; every failure retained |
| Concrete V2 bridges | Not implemented | Full model/origin identities, both compositions, exact subgroup |
| Written/Lean bridge proofs | Not attempted | Exact declarations/original audits plus explicit geometric gaps |
| Computational advantage | Not established | Admitted matched cold comparison against verified strongest references |

Retain the old q5/7/11 exhaustive controls and all negative results. The new
q223 constructor case is a separate bounded correctness fixture. Keep candidate
identity null until the executable maps and full curve/subgroup identity are
admitted. [pcc:unverified]
