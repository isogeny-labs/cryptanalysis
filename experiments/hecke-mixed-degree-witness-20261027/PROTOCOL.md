# D=-7 conductor-14 mixed-degree dependency protocol

Freeze the archived and repeated-root-corrected class matrices at p=347, along with the checked collector implementation and the prior one-step boundary result, by SHA-256 in `inputs.json`. Treat the archived 17 rows as the baseline. The corrected matrix contributes two degree-2 rows and one degree-7 row.

First, compute exact rational ranks for all subsets of the three new rows. Then reconstruct complete Hecke fibers and search the same degree/source ordered one-step commutator anchors as the boundary experiment. Retain every commutator with a nonzero source-25 degree-2 coefficient and report all nonarchived terms. If one such identity involves only that row and the new degree-7 row, save its exact integer coefficients; otherwise save the availability trace.

Separately solve for an exact rational dependency of the source-25 degree-2 row using the new degree-7 row and archived rows. Use a fixed lexicographic row order and canonical rational elimination; clear denominators and divide by the coefficient gcd. Verify every column independently using integer arithmetic. This certifies a span relation, not minimum support. Preserve all exact coefficients and input hashes.
