# Fixed-seed inverse-trace source-code falsifier

The W33 source eligibility predicates retain full algebraic degree on three frozen 12-bit affine code slices, and their eligible sets admit no nonzero vanishing polynomial of degree at most four on those slices. This rules out a direct low-degree ANF or low-degree source-only equation as the next replacement for the five-pair circuit's inverse witnesses on these inputs. The result redirects the solver experiment toward a *factored target-coupled constraint* over several source codes.

The exact N131 field is `GF(2)[u]/(u^131+u^13+u²+u+1)` and the curve source is W33 with seed mask `898618`, 32 free canonical source bits, and seed element `s = 898618 << 1`. For a source element `a`, eligibility here tests `Tr(a)=Tr(1/a)=Tr(1/(a+s))=0`, with nonzero denominators. Checked Lean field identities and an additive-trace theorem connect these conditions to the existing product-inverse witness formulation. The N41 W11 control uses `GF(2)[u]/(u^41+u³+1)`, seed element `112`, and ten free code bits. The frozen affine anchors and bit selections are in `protocol_v3.json`.

| Frozen code family | Slice size | Eligible codes | Degree of `Tr(1/a)` | Degree of `Tr(1/(a+s))` | Degree-four monomial rank on eligible codes |
| --- | ---: | ---: | ---: | ---: | ---: |
| N131 low12 | 4,096 | 1,016 | 12 | 12 | 794 / 794 |
| N131 middle12 | 4,096 | 1,013 | 12 | 12 | 794 / 794 |
| N131 high12 | 4,096 | 998 | 12 | 11 | 794 / 794 |
| N41 nine-bit control | 512 | 151 | 9 | 9 | Degree-three rank 130 / 130 |

The complete N41 W11 code cube reproduced the independently archived set of **281 eligible codes** exactly. All five archived N131 constructed-control source codes passed the same predicates. The producer computed truth tables, applied the Boolean Möbius transform to get exact ANF coefficients, and transformed them back to check every truth-table bit. For each N131 slice, the evaluation matrix of all 794 monomials of degree at most four has full column rank on eligible codes. Thus a degree-four polynomial that vanishes on all eligible codes in any one of these slices has zero coefficient vector when restricted to that slice. This is a finite statement about the frozen slices; a target-dependent relation between several codes may have different structure.

An independent implementation used exponentiation for field inversion, recomputed the trace masks, verified the eligibility of **2,512 rank-pivot codes**, and rebuilt the full-rank evaluation certificates. It completed in 16.857 s with 21,446,656 B process peak RSS. The primary truth-table run took 0.813 s; the rank run took 0.237 s. Each used one process under a 120 s wall alarm. A macOS `RLIMIT_AS` call failed on the first attempt, so the 4 GiB memory limit was observed through the recorded process peak rather than enforced by that API. The initial resource-limit failure and the second attempt's constant-zero ANF degree error remain in `scratch/`; the corrected v3 producer treats a zero Boolean function as degree `-1`.

`candidate_id: null`. This is a source-encoding gate; it does not measure ordinary relation yield, final rank, target descent, or single-target online time. The next charged experiment should retain the existing factored product-inverse source equations and change how the target link constrains multiple free W33 codes. Its unpinned N41 positive control must return an independently replayed relation before promotion to the frozen N131 public point.

Run `python3 verify_terminal.py` here to check the protocol, source, result, failure, pivot-audit, and Lean hashes. The terminal status is `PASS_W33_INVERSE_TRACE_LOW_DEGREE_FALSIFIER`.
