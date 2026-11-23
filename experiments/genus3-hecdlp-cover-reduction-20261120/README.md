# Genus-3 HECDLP reduction screen

Repository integration note: this is a retrospective bounded experiment
package imported on 2026-11-20. Its producer checks and raw summary artifacts
are preserved, but they do not have signed PCC standing; mathematical and
empirical statements remain [pcc:unverified]. The sibling `crypto` PR carries
the repository-native assessment and comparison with the existing genus
ladder.

This package evaluates the published Smith route from an eligible genus-3
hyperelliptic Jacobian to a non-hyperelliptic plane-quartic Jacobian.  The
transfer changes the best cited soft-O exponent for the HECDLP stage from
`q^(4/3)` to `q`.  It does not, by itself, establish a faster attack on a [pcc:unverified]
prime-field ECDLP.

The complete assessment is in [report.md](report.md).  The machine-readable
certificate is [artifacts/assessment.json](artifacts/assessment.json).
Cover-lifted subgroup retractions are recorded separately in
[artifacts/cover_retraction.json](artifacts/cover_retraction.json).
The NIST prime-field exponent filter is
[artifacts/complexity_gate.json](artifacts/complexity_gate.json); it proves [pcc:unverified]
that a native `F_p` curve has no proper cubic subfield descent and that a
same-field soft-`O(p)` plane-quartic stage loses to elliptic rho.
The toy measured scaling run is
[artifacts/empirical_benchmark.json](artifacts/empirical_benchmark.json).
Complete toy genus-3 HECDLP solves, including relation matrices, factor-base
logs, individual descent, and same-Jacobian rho, are in
[artifacts/end_to_end_hecdlp.json](artifacts/end_to_end_hecdlp.json).
Signed transfer, dual composition, and recovery timings on explicit toy
isogenies are in
[artifacts/signed_transfer_benchmark.json](artifacts/signed_transfer_benchmark.json).

## Reproduce

Run the self-tests:

```sh
PYTHONDONTWRITEBYTECODE=1 python tests/test_smith_screen.py -v
PYTHONDONTWRITEBYTECODE=1 python tests/test_cover_retraction.py -v
PYTHONDONTWRITEBYTECODE=1 python tests/test_complexity_gate.py -v
PYTHONDONTWRITEBYTECODE=1 python tests/test_empirical_benchmark.py -v
PYTHONDONTWRITEBYTECODE=1 python tests/test_end_to_end_hecdlp.py -v
PYTHONDONTWRITEBYTECODE=1 python tests/test_signed_transfer_benchmark.py -v
python src/empirical_benchmark.py --out artifacts/empirical_benchmark.json
python src/end_to_end_hecdlp.py --out artifacts/end_to_end_hecdlp.json
python src/signed_transfer_benchmark.py --out artifacts/signed_transfer_benchmark.json
```

Screen an affine degree-7 model (the rational point at infinity is added
automatically):

```sh
python src/smith_screen.py \
  --prime 37 \
  --poly 1,28,15,20,33,12,29,2 \
  --q-bits 5.2094533656
```

Screen just a homogeneous factorization type and emit JSON:

```sh
python src/smith_screen.py --degrees 6,1,1 --q-bits 85 --out artifacts/example.json
```

The program checks only the rational-kernel combinatorics.  A positive result
still requires constructing the isogeny, checking that the codomain is a
nonsingular plane quartic, and verifying the transported subgroup.
