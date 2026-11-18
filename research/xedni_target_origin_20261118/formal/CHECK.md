# Formal verification receipt

The algebraic module was checked with Lean `v4.35.0-rc4` and Mathlib revision
`021c46bdd042f67b538b9f9871d556a93713a9a9`, reusing the pinned environment in
`research/xedni_plane_group_20261117/formal`.  Exact command and output are in
[`build-output.txt`](build-output.txt). [pcc:unverified]

The three declarations prove the target-chord source-equation expansion,
recovery under an explicit inverse for the effective coefficient, and the
zero-explicit-target-coefficient specialization.  The axiom audit reports only
standard Lean foundations and no `sorryAx`. [pcc:unverified]

The proof is algebraic.  It assumes the target/known chord residual has source
scalar `-(t+m_j)`; formalizing the concrete good-reduction geometric bridge
remains a separate obligation. [pcc:unverified]
