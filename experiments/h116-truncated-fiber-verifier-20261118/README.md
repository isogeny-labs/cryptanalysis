# H116 truncated Frobenius-fiber independent verifier

This lane independently reconstructs the H116 blinded target census and checks
the candidate/direct moment packet produced by `isogeny-labs/crypto#4630`.
It is process- and implementation-separated from the Rust producer: the
verifier is a Python 3 standard-library program with its own finite-field,
elliptic-curve, formal-series and packet code. [pcc:unverified]

The first gate is target admission. It recomputes the five seeded scalar
permutations, all 4560 affine points and SHA-256 target digests, then checks the
one-to-one join against a separately supplied scalar map. Only after that gate
and the verifier source gate pass may the crypto producer create an H116 moment
packet. [pcc:unverified]

The packet gate will independently reconstruct every extension, `ker(V-1)`,
section and direct fiber; recompute the normalized Laurent recurrence and all
16 moments; and require candidate/direct/A/A equality plus positive, negative
and mutation controls. Scalar labels are unavailable during this phase. The
label map may be joined only by a later scoring command after packet admission.
[pcc:unverified]

This finite verifier does not establish a scalar predicate, decoder, generic
curve algorithm, asymptotic advantage, or subexponential ECDLP result.
[pcc:unverified]
