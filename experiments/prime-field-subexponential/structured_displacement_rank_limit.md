# Standard displacement structure does not compress the residual tables

The conjugate-center quotient turns genus-two signed-Hankel inversion into
two residual truth tables. Arithmetic and geometric progression abscissae
do not lower their balanced flattening ranks. This control asks a different
question: can those same tables still be represented by a low-rank Stein or
Sylvester displacement?

Use every one of the 41 structured split-fiber panels over
\(\mathbb F_{101}\) from the tensor-width census, together with its 41
length-matched random controls. On the natural balanced split of the sign
variables, test

1. diagonal and antidiagonal Stein displacements;
2. diagonal and antidiagonal Sylvester displacements;
3. both nilpotent and cyclic shifts; and
4. every pair of binary, Gray, bit-reversed, and Gray-bit-reversed row and
   column orders.

This gives 128 exact displacement ranks for each of the two residual tables
in every panel.

## Results

| Slots | Flattening shape | Structured panels | Structured minimum displacement ranks | Random minimum displacement ranks |
| ---: | ---: | ---: | --- | --- |
| 7 | \(8\times16\) | 30 | rank 8: 30 | rank 8: 30 |
| 8 | \(16\times16\) | 9 | rank 14: 5; rank 15: 4 | rank 14: 7; rank 15: 2 |
| 9 | \(16\times32\) | 2 | rank 16: 2 | rank 16: 2 |

At seven and nine slots the best displacement has full row rank. At eight
slots the original truth-table flattening has rank ten, but applying the
standard shift displacements raises the minimum to fourteen or fifteen.
The progression arm is not better than the random arm.

Consequently, arithmetic/geometric progression structure does not expose a
small generator through these standard one-dimensional displacement
operators or the tested binary/Gray layouts. In particular, ordinary
Toeplitz-, Hankel-, or circulant-like generator algorithms do not compress
these finite residual tables.

This is finite negative evidence, not an asymptotic lower bound. It does not
rule out a multilevel displacement tied directly to the Boolean cube, a
curve-specific transform outside the tested orderings, or an algorithm that
works on the determinant circuit without materializing its truth table.

## Reproduction

~~~sh
python3 structured_displacement_rank.py |
  cmp - structured_displacement_rank.json
python3 -m py_compile structured_displacement_rank.py
~~~

