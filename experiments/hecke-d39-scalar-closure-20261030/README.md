# D39 Hecke scalar-closure investigation

- [Current result](RESULT.md): rank 52 -> 63; doubling alone also reaches 63
  without Hecke rows; four solutions independently replayed, 256 scalar labels.
- [Result PDF](result.pdf), [diagram](result.svg), [rank chart](ranks.svg).
- [Frozen six-arm protocol](PROTOCOL.md) and [exploratory control protocol](CONTROL_PROTOCOL.md).
- [Historical pre-run report](REPORT.md): the original checkpoint-access blocker,
  subsequently resolved for this session; its PDF is preserved unchanged.
- [Remaining sparse-base and target-descent problem](../../problems/hecke-d39-sparse-closure-and-descent.md).

Run the synthetic tests with `python3 -m unittest discover -s
experiments/hecke-d39-scalar-closure-20261030 -p 'test_*.py' -v` from the
repository root. Research runs require the repository checkpoint gate.
