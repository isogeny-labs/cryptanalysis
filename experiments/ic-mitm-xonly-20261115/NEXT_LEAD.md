# Prefix denominator reuse after the abscissa-only comparison

The current three-arm x-only panel must be measured as frozen. Its native
kernel still batch-inverts a denominator for every selected pair. A separate
unimplemented specialization can exploit the already-declared prefix base.

For coordinates x_i,x_j in V=<1,z,...,z^(d-1)>, each ordinary-add denominator
x_i+x_j lies in V. Thus there are at most2^d-1 distinct nonzero denominators
although the pair table emits quadratically many entries. One bounded prefix
inverse table, prepared by the existing Gf2::batch_inv, could replace repeated
batch inversion work with a lookup per pair. The affine core already uses a
bounded inverse-square cache; this is ordinary inverse reuse in table setup.
No new algebraic attack or asymptotic reduction in table entries is asserted.

Require d<=12 and verify all operand abscissae are within the declared prefix;
otherwise retain the existing complete generic batch path. Exceptional equal-x,
identity and inverse pairs keep exact handling. Charge cache allocation and
construction, every table allocation and all computation to cold setup. Retain
original packed x+1 keys, loop order and exact first witnesses. No lookup cache
is allowed to hide setup or return a fabricated point.

First compare complete tables/returned witnesses on all registered targets and
cache-boundary cases, then use fresh frozen inputs and one binary to compare
against the strongest applicable measured same-base control. The current
unqualified negative/mixed rows and missing-lookup-pricing correction remain
part of the evidence. This is a source-derived hypothesis, not measured speed.
