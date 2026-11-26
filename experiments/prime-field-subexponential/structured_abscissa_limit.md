# Arithmetic-progression abscissae do not lower the measured norm-inversion degree

This control tests whether specially arranged split fibers expose a lower-degree
inverse for the genus-two binary norm system.  It is a finite exact experiment,
not an asymptotic lower bound.

Work on

\[
y^2=x^5+16x^4+20x^3+14x^2+12x+4
\quad\text{over }\mathbb F_{101}.
\]

For each section dimension \(r=4,5\), enumerate every distinct set of
\(g+r\) split abscissae that can be written
\(x_i=a+bi\) with \(b\ne0\).  For each set, sample signs, form the negative
Jacobian target, reconstruct the normalized section, and build the exact
quadratic norm-coefficient system.  Compare with the same number of seeded
random split-fiber panels.  The certificate degree is the first degree whose
Macaulay span contains every planted parameter linear form.

| Variables \(r\) | Tail slots | Progression sets | Progression degrees | Random controls | Random degrees |
| ---: | ---: | ---: | --- | ---: | --- |
| 4 | 6 | 41 | degree 4: 41 | 41 | degree 4: 41 |
| 5 | 7 | 15 | degree 4: 15 | 15 | degree 4: 15 |

Thus the complete \(\mathbb F_{101}\) progression census has the same measured
certificate degree as its random control.  Progression structure can greatly
reduce the cyclic span of the abscissae (to 16 and 19 in the two panels), but
that does not produce an ordinary early Macaulay rank surplus here.

The search also exposed and fixed a diagnostic bug: when a planted parameter
was zero, the sparse target row retained an explicit zero constant entry.  The
row reducer treated that entry as a monomial and could falsely miss the final
linear form.  The minimal regression system \(z=0\) now certifies at degree one,
and all four pre-existing certificate fixtures replay without a diff.

The result rules out only this direct specialization: arithmetic-progression
split abscissae plus ordinary static elimination on this curve and field.  It
does not rule out FFT-like operators, displacement-rank solvers, other fields
or curves, adaptive elimination, or a proof that exploits progression
structure without forming the Macaulay span.

Reproduce with:

```sh
python3 certificate_zero_regression.py
python3 structured_abscissa_search.py
```

The frozen output is in `structured_abscissa_search.json`.
