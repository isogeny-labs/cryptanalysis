# Validation receipt

This receipt covers documentation, source binding and protocol consistency.
It is not an experiment receipt and contains no solver measurement.

## Starting identity

- Repository: `isogeny-labs/cryptanalysis`
- Base commit: `1ee4f47e962aac7f0f09781e34fccfaec1c6456e`
- Branch: `codex/prime-ic-arity-correction-20261031`

## Source binding

Command:

```sh
sha256sum \
  experiments/compact-s3-m4-20261003/q1421_work_counted/theory_solver.cpp
```

Observed digest:

```text
0a0d2c673e9484f4b217917ee306e7663140e4d4618d8bb0ed8dc91947d08bc6
```

This agrees with the committed Q1421 compile receipt. The binding proves
which binary-field external-propagator source is being cited; it does not
qualify that source as an `F_p` implementation.

## Static consistency

The following checks are required before commit:

```sh
git diff --check
python3 - <<'PY'
from pathlib import Path

root = Path('experiments/prime-field-m3-cdclt-20261031')
readme = (root / 'README.md').read_text()
protocol = (root / 'PROTOCOL.md').read_text()
problem = Path('problems/prime-field-m3-cdclt-implementation.md').read_text()

assert 'e<m/2-1' in readme
assert 'e<m/2-1' in problem
assert 'strictly below `0.5`' in protocol
assert '`s=6..14`' in protocol
assert 'No affected data collection is authorized' in protocol

for path in [
    root / '../compact-s3-m4-20261003/q1421_work_counted/theory_solver.cpp',
    Path('problems/prime-field-m3-cdclt-implementation.md'),
]:
    assert path.resolve().exists(), path
print('OK: correction gates, no-run status and owned links are consistent')
PY
```

No compiler or scientific run is required for this documentation-only
handoff. The missing prime-field implementation is the named blocker, not a
test that can be reported as passing.

## Execution status

- Scientific rows created: 0
- Held-out instances generated: 0
- Solver builds attempted: 0
- Performance conclusions: 0
