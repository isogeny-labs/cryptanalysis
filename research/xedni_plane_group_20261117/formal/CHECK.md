# Formal verification receipt

The pinned Lean `v4.35.0-rc4` and Mathlib revision
`021c46bdd042f67b538b9f9871d556a93713a9a9` built `ChordOrigin.lean`
successfully with 9,040 jobs.  The exact output is retained in
`build-output.txt`. [pcc:unverified]

The four declarations prove the arbitrary-origin translation identity, the
chord-origin source-scalar identity, algebraic isolation of one target, and
target recovery when its coefficient is nonzero.  Their `#print axioms`
outputs contain only standard Lean foundations (`propext`,
`Classical.choice`, and `Quot.sound` as applicable), with no `sorryAx`.
[pcc:unverified]

Reproduce from this directory with:

```sh
lake build ChordOrigin
```

The proof assumes the source chord residual has scalar `-(m_j+m_k)`; the
geometric good-reduction bridge establishing that premise for a concrete
plane cubic remains separate. [pcc:unverified]

