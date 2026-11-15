# Original-model prepared sampler proof boundary

Reuse the exact existing NormAssistedSampling223 source and its three roots:
norm_half_roundtrip, prepared_sample_exact and omitted_half_rejected.
The first uses the ordinary inverse2 witness modulo2773073 and the stated
actual norm/scalar identities. The second derives sample(r)=[r]G from scalar
equivariance and the verified prepared identity. The third excludes an
omitted inverse2 for nonzero G under the norm-double and cancellation laws.
These are conditional implications; no desired program identity is added.
[pcc:unverified]

The new constructor computes the public prepared source and checks its
source group/order and actual Phi(u)=G. The full test compares225 samples
with original Picard multiplication and1125 full triples, plus every paired
IC result against both target and original source. Known-initial-point,
actual alternate-P0, actual cross-target and omitted-inverse2 controls are
separate tests. They do not silently instantiate every geometric/Picard/
scalar/program/order bridge in Lean or establish solver completeness.
[pcc:unverified]

Both unchanged original Lean gates audit the three-root old source with
zero trusted assumptions; exact original claims789d94/a9a7af/ed533b retain
their dates and original scope. Full raw gates and binding verdicts are
recorded with compiled-source evidence. Existing NewTargetIC/InducedFullTransfer
results retain their scopes. Complete primitive/setup/nested-decode/source
verification/known-point-reference costs and live admission remain open;
no calibrated ratio, ECDLP advantage, novelty or signed standing.
[pcc:unverified]
