# Root-balanced N131 quadratic certificate and prospective source-code holdout

## Contribution

One exact quadratic Boolean certificate excludes zero across both first-slot roots of four frozen, source-valid N131 W23 codes, covering eight complete 64-sign charts. Its 131-bit polar form has rank 32, so an exact factorization uses 16 AND gates on linear forms. A prospective fifth source-valid code selected by the frozen ascending-mask rule has certificate-one counts 28/64 and 31/64 on its two roots. The single fitted certificate therefore does not reject either new root chart as a whole. Independent Gaussian determinant and curve-sum replay checked all 128 prospective signs.

This extends the earlier root-0 four-chart certificate to both roots of those codes and tests generalization on a source code selected after the certificate was fixed. The result identifies a concrete design limit: a freely fitted field-word quadratic form gives compact exact certificates on the training family, but does not yet supply a reusable whole-family source-code selector.

## Instance and exact method

The curve is `y²+xy=x³+1` over `GF(2)[t]/(t^131+t^13+t²+t+1)`. The raw public target and five fixed suffix pair outputs are frozen in `../n41_n131_rr_code_family_span_20261017/panel_n131_v2.json`. Each first-slot code supplies two x roots; each root has 64 y-sign combinations with the five fixed points. The four training codes are the archived sample indices `(0,1,7,None)` with mask pairs `(3,898617)`, `(10,898608)`, `(41,898579)`, and `(46,898580)`. Their root-0 determinants inherit the archived independent checked-Sage coefficient replay. Their root-1 determinants were independently checked by Gaussian elimination and group sums in the earlier experiment.

For each 131-bit nonzero determinant value `v`, the fit requires `q(v)=1`, where `q` has zero constant term and all linear and squarefree quadratic Boolean features. The ordered eight-chart system has rank **512** in **8,646** feature coordinates. Symplectic factorization gives

`q(v) = linear(v) XOR XOR_{k=1}^{16} linear_k(v) AND linear'_k(v)`.

The independent symbolic audit expanded all 8,646 coefficient bits and checked equality with the original polynomial, including the zero constant term. It then evaluated the factorization on all 512 training determinants. The 32 input forms contain 264 input-bit literals. The [previous Lean theorem](../n41_rr_quadratic_separator_20261017/QuadraticCertificate.lean) proves that any such zero-constant factored circuit that evaluates to one on every determinant in a family excludes a zero determinant; [PROOF_MAP.md](PROOF_MAP.md) records the finite-instance bridge.

The holdout rule, frozen in `holdout_prepare_protocol.json` before source selection, scans first-slot masks `47..255` in ascending order. It requires the fixed W23 seed mate, source trace conditions, two-root/four-sign point structure, and distinct cofactor-four folded orbit keys against the five suffix pairs and the four training codes. The checked repository Sage launcher selected the first eligible mask **47**, with mate **898581**, after one tested mask. `sage_runtime_info.json` and `holdout_prepare_receipt.json` retain the runtime and one-worker resource record. The certificate, source panel, and evaluation script were hash-bound again in `eval_protocol.json` before determinant evaluation.

## Measured results

| Stage | Result | Wall and resource boundary |
| --- | --- | --- |
| Eight-chart fit | 8/8 charts, 512/512 signs certified; linear comparator 3/8 charts; quadratic rank 512; polar rank 32; 16 AND gates | 21.635 s parent wall, 21,807,104 B child peak RSS, one worker, 180 s / 4 GiB cap |
| Independent fit audit | 8,646 symbolic coefficients and 512 determinants match | `audit_result.json`: `BALANCED_SYMBOLIC_AUDIT_PASS` |
| Checked-Sage prospective source selection | first eligible code `(47,898581)`; 2 x roots, 2 y signs each | 9.094 s parent wall, 265,076,736 B child peak RSS, one worker, 180 s / 4 GiB cap |
| Fixed-certificate prospective evaluation | root 0: 28/64 words accepted; root 1: 31/64; 0/2 complete charts certified | 0.063 s producer wall on ordinary host |
| Independent prospective replay | 128 Gaussian determinants and 128 six-point group sums match; zero group hits | 0.441 s audit wall on ordinary host |

The fit has 8,134 free feature dimensions after its 512 constraints, so the fitted polynomial is weakly determined outside the training panel. The prospective accepted fraction is 59/128. The certificate is evaluated on a completed determinant word; the fit and source selection costs are separate and no factor-base relation search was reduced by this result. `candidate_id` remains `null`.

## Next algorithmic gate

Restrict a selector to features derived from the source-code algebra or from partial RR data, and freeze held-out codes and both roots before fitting. Require a whole-chart rejection on prospective source-valid codes while preserving the independently verified N41 relation, with coefficient construction and all failed branches charged. A surviving selector then belongs inside an unpinned N41 point-decomposition search before an N131 one-worker, 600-second, 4-GiB promotion.
