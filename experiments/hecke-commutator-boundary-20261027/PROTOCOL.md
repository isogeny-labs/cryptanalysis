# Cross-discriminant local commutator boundary

The experiment tests whether newly recovered degree-2 relation rows in two archived class walks admit the same one-step Hecke-commutator certificate as the D=-7 conductor census. The frozen inputs and source hashes are in `inputs.json`.

For each case, retain the archived matrix exactly and identify degree-2 target rows by multiset subtraction from the corrected matrix. Reconstruct complete fibers using the frozen multiplicity collector. Search partner degrees greater than 2 in ascending order and anchor point indices in ascending order. A certificate requires both first-step fibers, a nonzero target coefficient, every other commutator row present in the archived matrix, and exact integer cancellation. Save a first valid certificate, or `NO_ONE_STEP` with probe and availability counts.

Measure the rational rank of the archived matrix and of each degree-2 target added individually and together. Check every reported integer identity and rank independently. The experiment compares certificate availability for these fixed records; failure of this bounded search is not a general impossibility result.
