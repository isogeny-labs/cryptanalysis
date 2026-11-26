# Frozen same-point Edwards coordinate panel

This protocol is frozen before the `msolve` comparison. It tests the supplied
twisted Edwards y-coordinate summation polynomial against a short
Weierstrass x-coordinate summation polynomial on **the same rational point
set and targets**. The curve has composite order, so this is a coordinate
model check and does not transfer the result to a prime-order target or to
the missing L20/L24/L28 systems. All local output has producer-only standing
`[pcc:unverified]`.

## Exact curve and birational map

- Field: `F = GF(10007)`. Edwards equation:
  `3*x^2 + y^2 = 1 + 2*x^2*y^2`.
- Set `A=2*(a+d)/(a-d)=10`, `B=4/(a-d)=4`, with `a=3,d=2`.
  Map an ordinary Edwards point `(x,y)` to Montgomery
  `u=(1+y)/(1-y), v=u/x`, then to short Weierstrass
  `X=B*u+A*B/3, Y=B^2*v`.
- The resulting Weierstrass model is `Y^2=X^3+6154*X+1933`, with
  `#E(F)=9920`. Abort if the curve, map, or order does not verify exactly.
  Exceptional points are excluded from the selected factor base and targets.

## Same point set and controls

- Edwards factor-base y-roots are `[4,5,10002,10003]`, namely `±4,±5`.
  Include both Edwards x signs for each root. Its eight points map to an
  eight-point Weierstrass base with x-roots `[3343,5348,6678,6682]`.
  Both bases are closed under group negation. The Edwards base is also
  closed under translation by `(0,-1)`, which changes `(x,y)` to `(-x,-y)`.
- Order the eight Edwards points by integer `(y,x)`. The positive target
  is the sum of points at indices `0,2,4`, mapped to Weierstrass
  `(5348,6496)`. The negative target is `(4990,52)` on the Weierstrass
  curve, the first generator returned by Sage and outside the three-sum
  set. Assert both target identities before generating inputs.
- Enumerate all ordered three-point sums on the eight-point base and
  compare their coordinate triples to the polynomial systems. The positive
  control has 16 distinct coordinate triples and the negative has zero in
  each model; abort if this changes.

## Native solver systems

Construct `S4^TE(y1,y2,y3,yR)` by eliminating `z` between the supplied
`S3^TE(y1,y2,z)` and `S3^TE(y3,yR,z)`. Construct the short Weierstrass
`S4^W(X1,X2,X3,XR)` by the corresponding `f3` resultant. Add one
factor-base polynomial per variable, the product of its four coordinate
roots. Run `msolve -v 2 -t 1` once per model/control pair, retaining exact
inputs, raw compressed logs and outputs, input/output hashes, exit codes,
wall/CPU time, ideal degree, every F4 round, maximum round degree, and
matrix sizes. Check solver solutions against the independently enumerated
group-law triples and report multiplicity or extraneous-solution differences.

The systems have identical point-set and target identities but different
coordinate variables and polynomial sizes. A one-run timing ratio is a
diagnostic only. A claimed eightfold benefit requires a matched invariant-
coordinate solver implementation and stable repeated measurements.
`[pcc:unverified]`
