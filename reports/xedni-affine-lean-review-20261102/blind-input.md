# Blind xedni affine-coset re-derivation

Let `u` and each `D_i` be integer vectors of the same finite dimension, let
`c_i` be arbitrary integers, let `B_j` be finitely many integer row vectors,
and let `q > 0` be an integer. Assume `B_j · D_i = 0` for every row and
direction and `D_i,k % q = 0` for every direction and coordinate. Derive the
strongest exact statement you can for `u + Σ_i c_i D_i`, including the effect
of arbitrary integer recombinations of the `D_i`. State precisely which
hypotheses are needed.

Try the controls `u=0`, `B=1`, `q=2`, `D=1`, `c=1`, and the same input with
`B=0`. Report what breaks if a premise is removed. Do not inspect the
producer's proof, Rust source, receipt, or report before filing your blind
derivation and read attestation.
