# H115 independent Frobenius--Kummer verifier

This directory contains the source-frozen independent verifier for crypto
draft PR #4625 at producer revision `6d8def5473`. No H115 candidate evidence
exists in this repository and no H115 result is claimed. `[pcc:unverified]`

The verifier is deliberately implemented in Python with tuple-valued field
elements and the standard `json`/`hashlib` libraries; it does not import or
execute the Rust producer. It reconstructs every frozen extension, torsion
table, fiber, moment, channel, score, control and decoder trace from literal
curve fixtures.

Source-only checks:

```text
python3 -m py_compile h115_verify.py
python3 h115_verify.py --selftest
```

The selftest uses only a synthetic `F_3^2` fixture and rejects all eight
frozen mutation classes. The additional structural audit documented in
`SOURCE_GATE.md` constructs the five unlabeled curve contexts but does not
generate a frozen row or evaluate a frozen scalar label.

Evidence verification, after a checkpointed producer run:

```text
python3 h115_verify.py --verify /path/to/h115.jsonl
```

The command must exit nonzero on any mismatch. A successful verification is
still finite toy evidence, not a novelty, generic-ECDLP or subexponential
claim.
