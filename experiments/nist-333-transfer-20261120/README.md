# NIST `(3,3,3)` genus-three lead

Repository integration note: this is a retrospective bounded reproduction
imported on 2026-11-20. Its producer tests and artifacts are preserved, but
they do not have signed PCC standing; mathematical and empirical statements
remain [pcc:unverified]. The sibling canonical native study is
`crypto:research/nist_cover_three_tests_20261116/`.

This directory is a standalone, reproducible continuation of the NIST
genus-three isogeny lead. It does not solve discrete logarithms.

Start with [report.md](report.md). The principal machine-readable outputs are:

- `artifacts/evidence.json` — exact torsion fields, points, kernels, exhaustive
  Lagrangian census, controls, and cost-model numbers;
- `artifacts/assessment.json` — obligation-by-obligation transfer assessment;
- `artifacts/complex_theta_diagnostic.json` — bounded complex-period
  theta-null controls for the repeated-product specialization;
- `artifacts/p224_finite_field_theta.json` — exact P-224 normal-Weil and
  64-characteristic calculations plus the corrected quartic over `F_(p^6)`;
- `artifacts/p224_descended_quartic.json` — the explicit 15-term nonsingular
  P-224 plane quartic over `F_p` and its descent validation record;
- `artifacts/p224_point_map_status.json` — the exact 64-coordinate Kummer map,
  kernel-generator fiber checks, transverse control, and signed-map obstacle;
- `artifacts/p224_jacobian_prerequisites.json` — rational bitangent contacts,
  canonical divisor, and basepoint encoding;
- `artifacts/p224_frobenius_certificate.json` — exact expected `E^3`
  L-polynomial and independent-evidence boundary;
- `artifacts/p256_finite_field_theta.json` — the exact P-256 `F_(p^3)` quartic
  candidate with its theta and bitangent checks;
- `artifacts/p256_descent_status.json` — exact field audit and external descent
  obstruction certificate;
- `artifacts/p256_aronhold_frobenius.json` — all 28 odd-characteristic
  Frobenius orbits and the exact obstruction to a seven-bitangent descent;
- `artifacts/follow_on_status.json` — aggregate status of requested items 1–6;
- `artifacts/theta_structure_diagnostic.txt` — exact Tian source controls that
  identify and close the two-sign reduced-characteristic defect;
- `requirements.md` — the requested scope and acceptance evidence;
- `attempts.md` — unsuccessful checks and the explicit reconstruction blocker.
- `handoff/nist_333_kernel_input.m` — generated Magma input that reconstructs
  and checks both exact kernels; it does not include the missing corrected
  theta reconstruction.
- `handoff/p224_quartic_descent.m` — generated input for the maintained
  Dixmier–Ohno checks and direct Frobenius/Hilbert-90 descent bundled with
  Magma.
- `handoff/p256_descent_diagnostic.m` — generated P-256 moduli,
  Frobenius-isomorphism, and order-three cocycle diagnostic.

Reproduce with:

```bash
python src/nist_333.py --out artifacts/evidence.json
python src/build_assessment.py
python src/export_magma_input.py
python src/finite_field_theta.py --out artifacts/p224_finite_field_theta.json
python src/finite_field_theta.py --curve P-256 --out artifacts/p256_finite_field_theta.json
python src/p224_jacobian_prerequisites.py --out artifacts/p224_jacobian_prerequisites.json
python src/p224_point_map_status.py --out artifacts/p224_point_map_status.json
python src/p224_frobenius_certificate.py --out artifacts/p224_frobenius_certificate.json
python src/p256_aronhold_frobenius.py --out artifacts/p256_aronhold_frobenius.json
python src/p256_descent_status.py --out artifacts/p256_descent_status.json
python src/build_follow_on_status.py
python src/export_quartic_descent.py
python src/export_p256_descent_diagnostic.py
python tests/test_nist_333.py -v
python tests/test_complex_theta_diagnostic.py -v
python tests/test_finite_field_theta.py -v
```
