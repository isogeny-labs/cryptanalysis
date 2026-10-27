# Degree-5 Frobenius orbit traces add three class-row dimensions

On the frozen 20-point D=-79, conductor-2 class over F_83, five degree-5 Hecke fibers yield exact relations after tracing their nonrational neighbor orbits back to F_83. Adding those five class-only rows to the ten multiplicity-corrected degree-2 rows raises rational rank from **10 to 13**. Each accepted row is checked as an equality in `11a1(F_83)`, and an independent point-arithmetic implementation reproduces all five equalities and the rank.

| Degree-5 fiber status | Sources | Outcome |
| --- | ---: | --- |
| All orbit traces in the frozen class or identity | 5 | Five verified rows; combined rank 13 |
| A trace lands outside the frozen class | 14 | Rational trace recorded; no class-only row inserted |
| Repeated rational neighbor x-coordinate | 1 | Multiplicity-two x-root retained for a separate lift |

Every neighbor-x polynomial has splitting degree 4. Nineteen have factor pattern `(1)(1)(4)`; one has `(1)^2(4)`. In each squarefree case, the producer lifted all six neighbors to F_(83^4), solved their y-coordinates from the six Hecke `x^k y` moments, checked the curve and modular polynomial, and verified their group sum. The two rational neighbors form singleton Frobenius orbits; the remaining four form one orbit. Its trace is a frozen class point at four of the accepted sources and identity at one.

The accepted sources are `0, 1, 3, 6, 10`. Their exact rows, orbit sizes, trace points, and polynomial factor patterns are in [result.json](result.json). The [protocol](PROTOCOL.md) fixed the source set, degree, extension cap, and row acceptance rule before the run; [inputs.json](inputs.json) pins the matrices and Hecke builder. The [checked runtime receipt](sage-runtime-info.txt), successful [producer output](producer-output.txt), and [independent validator](verify.py) are retained. The validator uses separate Python arithmetic for the general Weierstrass group law over F_83, reconstructs every accepted row from the saved traces, checks each source's aggregate trace sum, and performs exact rational elimination. It returned:

```text
FROBENIUS_ORBIT_TRACE_PASS closed 5 rank 10 -> 13 statuses {'CLASS_CLOSED': 5, 'OUTSIDE_CLASS_TRACE': 14, 'REPEATED_X_UNLIFTED': 1}
```

The first producer attempt computed the same result but exited while serializing a diagnostic summary with tuple dictionary keys. Its failed stdout, stderr, and result are retained as `producer-attempt1-*` and `result-attempt1.json`; the successful rerun changes only that display formatting.

The [earlier scalar-fiber audit](../ecdlp-hecke-cross-discriminant-20261012/SCALAR_STRATA_RESULT.md) explains why another *complete rational* degree-5 fiber is unavailable at this conductor. Orbit tracing instead turns some degree-5 fibers into relations on the original rational class. The next experiment is a multiplicity-aware lift for source 18's `(1)^2(4)` fiber, followed by a closure audit for the fourteen outside-class trace points.

Reproduce from the repository root:

```sh
./sage --runtime-info > experiments/hecke-frobenius-orbit-20261027/sage-runtime-info.txt
./sage -python experiments/hecke-frobenius-orbit-20261027/run.py
python3 experiments/hecke-frobenius-orbit-20261027/verify.py
```
