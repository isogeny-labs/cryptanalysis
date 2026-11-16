# Follow-up eligibility audit

The first-hit protocol and its `result.json` were frozen before the initial
enumeration. This follow-up audit uses the recorded scalar and encoding rows
to check the newly formalized live/eligible prefix equivalence for every
prefix length 1 through 6. It does not change the original event definition
or rerank the stage results.

Falsifier: any row and prefix for which first-hit liveness differs from
pairwise eligibility of the reconstructed old affine forms.
