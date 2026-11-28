# Fixed-residual inversion is split-prime orientation in the Jacobian

Once the residual polynomial is prescribed, the norm right-hand side is fully
factored.  In the quadratic function field of (C:y^2=f(x)), each split
linear factor has

\[
 (X-x_i)=\mathfrak p_i^+\mathfrak p_i^-,
 \qquad
 \mathfrak p_i^\pm=(X-x_i,y\mp y_i).
\]

Conjugation exchanges the two primes and negates their degree-zero divisor
classes.  Fix the plus orientation and write (P_i=[\mathfrak p_i^+]).  A
sign flip changes its contribution by

\[
 [\mathfrak p_i^-]-[\mathfrak p_i^+]=-2P_i.
\]

After absorbing the target and prescribed residual into a fixed class (T),
the norm equation is therefore the orientation equation

\[
 \sum_i z_i(-2P_i)=T-\sum_iP_i,
 \qquad z_i\in\{0,1\}.
\]

For a chosen orientation, principal-ideal testing and generator recovery are
ordinary Riemann--Roch, extended-Euclid, or polynomial-Cornacchia operations.
They do not select the orientation.

This formulation rules out a tempting (2)-descent shortcut.  Every flip
increment lies in (2J), so all (2^m) orientations have exactly the same
image in (J/2J).  On an odd prime-order subgroup, multiplication by two is
an automorphism, and the displayed equation is an ordinary subset-sum equation
after scaling by (-1/2).  Thus neither rational two-torsion nor a Selmer-style
parity label separates the branches relevant to the cryptographic component.

The seven full genus-two panels exhaust 1,016 orientations.  They verify the
affine subset-sum identity for every orientation, the (-2P_i) flip formula,
and a unique target orientation in each panel.

The result does not prove average-case hardness for the structured points
(P_i).  It identifies the exact task that a direct norm or ideal algorithm
must beat: simultaneous orientation selection, not principal-ideal
reconstruction after the choices are supplied.

~~~sh
python3 split_prime_orientation_control.py |
  cmp - split_prime_orientation_control.json
python3 -m py_compile split_prime_orientation_control.py
~~~
