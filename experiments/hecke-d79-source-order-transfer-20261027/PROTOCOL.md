# Fresh-class transfer of a retained source certificate

Select the first two eligible 40-point D79 conductor-four classes after the earlier series (odd v from 341 to 501, p=v²+316). Eligibility is prime p, 5 dividing the curve order, 5 not dividing p−1, and largest curve-order prime factor at least 53. Retain every eligible class inspected and any construction error. Recompute its direct signed support-at-most-four rows and rank before degree-13 lifting.

Freeze three complete source orders for each selected class before any degree-13 output:

1. Ascending index 0..39.
2. Prior-certificate-first: source indices from the sealed p103357 12-source certificate in ascending order, then remaining indices ascending.
3. SHA order: sort indices by SHA-256 of `d79-order-transfer-v1:<p>:<index>`, with index as tie-breaker.

The certificate indices were learned from the prior class; their transfer to unseen classes is the hypothesis. SHA order is a deterministic control. Lift all 40 sources once in ascending execution order, preserving every status and interval. For each frozen virtual order, independently enumerate signed outside-trace cancellations of distinct support at most four and record rank over that class's largest-prime field for prefixes 0..40. Compare first rank-39 source count only where the full 40-source pool attains rank 39; otherwise retain a censored rank-goal result and compare the full prefix sequences without treating failure to reach rank 39 as a policy win.

An independent Sage audit must recheck source group equations, Hecke rows, baseline and prefix ranks from sealed output. Source-lift times are measured component costs. The virtual order replay does not measure a live scheduler, and `candidate_id` and `target_online_ms` remain null.
