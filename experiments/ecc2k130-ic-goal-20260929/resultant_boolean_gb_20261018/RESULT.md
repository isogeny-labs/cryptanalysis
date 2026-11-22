# Exact Boolean ANF and unpinned N41 Gröbner gate

The 13-term target resultant now expands exactly into Boolean
polynomials on both free source codes. The frozen verifier matched this
ANF to independent field evaluation on 17 constructed and 16 ordinary
N41 code pairs, plus 17 N131 code pairs with 16 first-code bits and all
32 second-code bits free. This establishes an exact input representation
for blockwise algebraic elimination. Direct PolyBoRi Gröbner reduction
on the unpinned 20-bit N41 positive, however, reached a 120-second cap
in both lex and degree-lex order. The degree-lex ordinary control also
reached its 120-second cap. The N131 48-bit Gröbner query was therefore
gated and not launched.

## Encoding and controls

Each source product is an affine binary combination of its code bits.
Characteristic-two squaring makes powers two and four linear; the cube
has only singleton and pair terms in a source's bits. Multiplying the
13 field monomials of the bivariate resultant gives Boolean degree at
most four across both sources. The [checked Lean expansion](../n131_w33_resultant_core_20261018/PROOF_MAP.md)
supports this reduction. Source-point validity remains a separate
check, so these Boolean equations are a sound relaxed filter.

| Input | Free first/second bits | Nonzero field ANF coefficients | Exact evaluations checked |
| --- | ---: | ---: | ---: |
| N41 constructed point | 10 / 10 | 3,046 | 17, including known zero `(253,63)` |
| N41 ordinary point | 10 / 10 | 3,046 | 16 |
| N131 constructed point, first upper 16 bits fixed zero | 16 / 32 | 71,857 | 17, including known zero `(3,16722)` |

The N41 positive ring construction yielded 41 equations containing
62,526 Boolean monomial occurrences. The N41 inputs use the exact
frozen 281-code source table and 25-target coefficients; the N131 input
uses the frozen W33 coefficients. `candidate_id: null` records that no
complete IC method entered a comparison.

## Bounded solver attempts

| Attempt | Terminal status | Parent wall | Sampled peak combined RSS |
| --- | --- | ---: | ---: |
| N41 positive, first lex launch | `MONITOR_FAILURE` before arithmetic: macOS denied recursive process inspection | 0.003 s | unavailable |
| N41 positive, lex, corrected monitor | `BOUNDED_UNKNOWN`, wall cap | 120.116 s | 723,091,456 B |
| N41 positive, degree-lex | `BOUNDED_UNKNOWN`, wall cap | 120.186 s | 873,299,968 B |
| N41 ordinary, degree-lex | `BOUNDED_UNKNOWN`, wall cap | 120.074 s | 740,245,504 B |

The corrected monitor samples its own process and the checked Sage
child, one worker under 4 GiB. The original monitor failure is kept
with its stdout, stderr, source and protocol. Each subsequent cap has
no terminal Gröbner basis, so it neither proves absence of a solution
nor supplies a valid decomposition. The constructed positive is known
to exist by the independent N41 finite-domain census and curve replay.

The direct ANF approach has no demonstrated block-solving advantage
over the earlier unpinned N41 XCNF control, which recovered the
constructed positive. The next elimination candidate must reuse
work across first-code families or derive a lower-degree necessary
condition; its promotion gate is an unpinned N41 witness-preserving
solve followed by an ordinary-query check within the declared cap.

Run `python3 audit.py` from this directory to check the frozen source,
protocol, solver-output and verification hashes. The checked-Sage
`verify_anf.py` produced the recorded random equivalence checks in
`verification_result.json`; rerun that producer in a fresh copy with
the protocol paths rehashed.
