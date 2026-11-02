# Xedni affine-coset proof map

The executable seven- and ten-coefficient xedni lift optimizer validates every
input direction before searching. For each exact point-incidence row `B`, it requires
`B D_i = 0`; when a modulus `q > 0` is supplied, it also requires every
coefficient of `D_i` to have remainder zero modulo `q`. It then applies LLL
to the direction list. Its candidate loop forms `u* + sum_i c_i D_i` from the
resulting list for arbitrary integer coefficients, including those chosen by
Babai and the bounded neighborhood search.

[`XedniAffineCoset.lean`](XedniAffineCoset.lean) defines finite integer vectors,
the exact dot product, the affine candidate, and the list of coefficient and
direction pairs produced by the loop's `zip`. Its central theorem
`XedniAffineCoset.candidate_preserves` states, for **every** direction satisfying
the exact row and residue hypotheses and every integer search coefficient,
that all incidence dot products equal
their values at `u*` and that every candidate coefficient differs from `u*`
by zero remainder modulo `q`. The theorem `direction_span_closed` proves that
arbitrary integral combinations of such directions still satisfy both
hypotheses, the algebraic fact needed for an LLL basis change. The helper
`candidate_preserves_divisibility` states the equivalent divisibility form.
The proof covers both coefficient dimensions because `n` is quantified and the
Rust validator checks dimensions before constructing candidates.

## Reproduce

The theorem is a standalone Lean `Init` module at the repository's pinned
`leanprover/lean4:v4.34.1`. From the repository root:

```sh
python3 research/xedni_lift_optimizer_20261101/lean/check.py
```

The [receipt](receipt.json) pins this Lean source, `lean-toolchain`, and
`suite/src/cryptanalysis/xedni_lift.rs` by SHA-256 at source commit
`545de2e1c91a301b342b45317f402be4497647ba`. The checker runs Lean and
compares all three `#print axioms` lines with the receipt. The accepted axioms are
`propext` and `Quot.sound`; `sorryAx`, custom research axioms, and unverified
native evaluation are absent. The dedicated GitHub Actions job reruns the
same check on PRs and on relevant `main` changes.

## Scope of the bridge

The theorems establish the affine-coset invariant and closure under integer
basis changes. The Rust bridge is conditional on its post-LLL basis being
integral combinations of validated input directions. This module does not
prove the Rust parser, the validator's control flow, the LLL implementation
and its output-span invariant, Babai, the discriminant formula, the ranking
rule, or the later `certify` call. Those are separate source and implementation
obligations. The frozen p=67 diagnostic in the parent report
still has no run rows because its checkpoint upload gate failed; this proof
does not turn that unexecuted comparison into a measured result.
