# H115 verifier source gate

Gate date: 2026-11-18

Status: **PASS** for source compilation, synthetic rejection and unlabeled
structural agreement. Real producer evidence is absent. `[pcc:unverified]`

## Source

- verifier: `h115_verify.py`
- SHA-256:
  `e625542931d0b8b6b6b753ce19b495a03b9640c7f1cdb6ba06b3d7d9196e1a37`
- lines: 1,392
- dependencies: Python 3 standard library only

Commands:

```text
python3 -m py_compile h115_verify.py
python3 h115_verify.py --selftest
```

Both exited `0`. Selftest output:

```json
{"modulus":[1,0,1],"predicate_ids":648,"synthetic_field":"F_3^2","tamper_rejections":["extension-coefficient","frobenius-image","fiber-member","moment","scalar-label","predicate-id","raw-digest","summary-count"]}
```

## Independent unlabeled structural receipt

One context construction per frozen curve produced:

```text
h115-fp7-a1-b1-r5-d4 modulus=[1,0,0,1,1] N=2475 cofactor=99 states=10 torsion=25 kernel=5 T=[2009,1194] H=[2009,1194]
h115-fp5-a2-b1-r7-d6 modulus=[1,0,0,0,1,1,1] N=15680 cofactor=320 states=6 torsion=49 kernel=7 T=[14161,6938] H=[612,5192]
h115-fp13-a2-b4-r17-d4 modulus=[1,0,0,1,1] N=28611 cofactor=99 states=14 torsion=289 kernel=17 T=[7013,8633] H=[25744,15384]
h115-fp31-a1-b19-r37-d4 modulus=[1,0,0,1,1] N=924075 cofactor=675 states=33 torsion=1369 kernel=37 T=[755239,33125] H=[384612,757240]
h115-fp47-a1-b38-r61-d3 modulus=[1,0,5,1] N=104188 cofactor=28 states=48 torsion=3721 kernel=61 T=[51403,71944] H=[65855,12311]
```

These values agree with the producer's non-scoring structural receipt. The
Python path independently checked every torsion point's Frobenius
characteristic equation, the factorization, and the complete kernel set. It
did not instantiate a frozen target moment or score a scalar label.

## Deferred gates

- byte-level producer/verifier handshake on checkpointed evidence;
- one-at-a-time rejection of all eight mutations on a copied real packet;
- PCC publication for any empirical statement;
- assessment of the still-open `Theta(r)` moment-construction barrier.
