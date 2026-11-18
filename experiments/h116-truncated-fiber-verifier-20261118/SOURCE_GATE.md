# H116 verifier source gate

Gate date: 2026-11-18

Status: **PASS** for strict Python compilation, excluded-fixture arithmetic,
synthetic controls and mutation rejection. No H116 target-admission command or
candidate/direct packet has run. `[pcc:unverified]`

## Source binding

- verifier: `h116_verify.py`
- SHA-256:
  `d99493788c1b722e56270a8e5fb2503e2144b417e1da7b5e09451ea2caa40e0b`
- lines: 1211
- interpreter: Python 3.12.14
- dependencies: Python 3 standard library only

Commands:

```text
python3 -W error -m py_compile h116_verify.py
python3 -W error h116_verify.py --selftest
```

Both exited zero. The self-test used the excluded H115 p=31 fixture, not an
H116 curve. It independently rebuilt the extension and `ker(V-1)`, enumerated
the 37-point fiber, and matched all 16 candidate/direct moments under native
and lambda-two coordinates. It also passed the SHA-256, SplitMix64 and first-
irreducible known-answer vectors; 32 separable-root positive controls; and all
p=5,7,13 boundary rejections. [pcc:unverified]

Self-test stdout SHA-256 was
`65dd5559c04805e8dd4b624617be1c85d42973c075e0e7c1b0e66148c1012b98`.
It exited in 2.248s elapsed, 2.235s user and 0.013s system CPU on the development
host. These are source-test diagnostics, not admitted performance evidence.

## Synthetic tamper gate

The self-test rejected these 12 one-at-a-time mutations:

```text
target-coordinate, target-digest, target-order, truncated-row,
header-hash, candidate-coordinate, direct-coordinate, aa-coordinate,
positive-coordinate, negative-boolean, duplicate-row, summary-count
```

The real target and packet gates remain unrun. Their copied-artifact mutation
tests remain mandatory after each artifact exists. A source self-test is not
independent verification or evidence for a scalar predicate, decoder or
complexity claim. [pcc:unverified]
