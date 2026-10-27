# Proof map for cached degree-13 functions

The new result is exact implementation equivalence: one canonical rational-function artifact decodes to the same `(funcs,jfun)` as an independent checked-Sage `H.build([13])`, and four separate loaded processes reproduce the exact source-prefix fibers, cancellations and ranks. The independent build audit compares every coefficient; the loaded replay guards against invoking `H.build`. The content digest and all four process receipts are checked by `verify.py`.

The mathematical rank statements are unchanged from [the prefix proof map](../hecke-d79-source-prefix-20261027/PROOF_MAP.md) and its pinned Lean modules `RankPrefixP8597` and `RankPrefixP12197`. Their checked kernel and inverse-minor certificates apply to the same 40-column row matrices revalidated here. The general Lean rank implication and curve-to-Lean bridge remain open there. No new mathematical theorem is asserted from the cache timing.
