# A constant branch-root signature has exponentially large local fibers

Completing the square rewrites the binary norm inverse as

\[
 R^2-fB^2=N,
 \qquad N=-uU_0.
\]

Reducing modulo the fixed curve polynomial \(f\) appears attractive:

\[
 R^2\equiv N\pmod f.
\]

Since \(\deg f=2g+1\), there are at most \(2^{2g+1}\) geometric square-root
residues.  This is constant at fixed genus.  It does **not** make the norm
solution constant-branching beyond the first residue.

Assume the generic coprime case \(\gcd(N,f)=1\), and fix one root
\(R_0\bmod f\).  For every choice

\[
 B\bmod f^{k-1},

\]

the element \(N+fB^2\) is congruent to the unit \(R_0^2\bmod f\).  Because
the derivative \(2R_0\) is invertible modulo \(f\), Hensel lifting gives a
unique

\[
 R\equiv R_0\pmod f,
 \qquad R^2=N+fB^2\pmod {f^k}.

Thus each first-level signature has exactly

\[
 p^{(k-1)\deg f}

\]

unrestricted local lifts.  Choosing enough precision to determine a
polynomial with \(\deg B\le d_B\) still leaves all
\(p^{d_B+1}\) bounded \(B\)-polynomials as candidates.  In the binary
construction \(d_B=\Theta(r)\), so the constant root signature does not
remove the growing-dimensional search.

All seven split panels satisfy \(\gcd(N,f)=1\).  Their first signature count
is bounded by 32, but it sits above 101, 101, 10,201, 10,201, 1,030,301,
1,030,301, and 104,060,401 degree-bounded \(B\)-candidates per signature.
The global polynomial identity and target congruence eventually select the
witness; local ramified lifting alone does not.

This closes only the naive \(f\)-adic Hensel strategy.  A global continued-
fraction, infrastructure, or Hilbert--90 method could correlate the local
digits, but it must do more than lift the constant branch-root residue.

~~~sh
python3 ramified_hensel_branching.py | cmp - ramified_hensel_branching.json
python3 -m py_compile ramified_hensel_branching.py
~~~
