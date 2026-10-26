# Global Fricke identification protocol

Fix the genus-one modular curve `X_0(11)` with the Weierstrass model
`y²+y=x³−x²−10x−20`, origin cusp infinity, and cusp zero
`T=(16:-61:1)`. These coordinates are fixed by the cited modular-curve
reference before computing the output. Check the model, modular degree,
order of `T`, rational automorphism exception invariant, and weight-two
Fricke eigenvalue through the repository Sage launcher. The theorem target
is the identity `W_11(P)=T−P` over `Q`; for good reduction it descends to
every characteristic other than 11. The finite-field group-law checks are
corroboration, not the proof of the modular identity.

The mathematical proof uses the moduli definition of `W_11` as dualizing a
cyclic 11-isogeny, so it exchanges the two cusps. Any automorphism of the
genus-one curve is translation by its image of the origin, followed by an
origin-preserving automorphism. For this curve, the latter is `±1` over
`Q`. Since `W_11` also maps `T` to the origin and `T` has order five, the
`+1` case would give `2T=0`, a contradiction. Prove the conditional
group-theoretic step in Lean, and state explicitly the modular-curve bridge
that has not been formalized there.
