# Blind arithmetic review input

Work from this statement alone. Do not read repository files, producer proofs,
archived results, Git history, or another reviewer's output. Derive or refute
each assertion independently, give witnesses or counterexamples for nearby
false statements, and record all sources read in an attestation.

Let `a,b,c` and `F` be natural numbers. Check these five assertions:

1. If `a,b,c <= 24` and `a+b+c=72`, then `a=b=c=24`.
2. If `a+b+c=12`, at least one of `a,b,c` lies strictly between 0 and 24.
3. If `a,b,c <= 24` and `a+b+c=48`, at least two are positive.
4. `6*1 + 60*1 + 6*2 = 78`.
5. If `79 <= F <= 217`, then `791 <= 1008-F <= 929` using natural-number subtraction.

Also test what happens to (1) at sum 71, (3) without the cap 24, and (2)
at sum zero. A separate source review will handle whether the hypotheses
describe a concrete geometric census; do not infer that from these statements.
