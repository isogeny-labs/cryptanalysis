# Initial mixed-projection proof attempt

Command: `lake build MixedProjection` with a single `by decide` over the universally quantified `Fin 5` characterization.

Status: failed. Lean 4.35.0-rc4 reported at `MixedProjection.lean:16:2`: `failed to synthesize Decidable (∀ (a b c : Fin 5), allowed a → allowed b → allowed c → ...)`. Its diagnostic `#print axioms` contained `sorryAx` because the theorem was unfinished. This attempt is excluded from the reported proof status.

The checked version introduces the three variables and hypotheses, splits each permitted residue into its three cases, and simplifies the resulting 27 concrete goals. The passing build and axiom printout are retained in `projection-build-output.txt` and `build-output.txt`.
