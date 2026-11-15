# Complete correction and descent: conditional proof scope

`ChainDescent.lean` strengthens the earlier conditional norm-halving argument:
half-choice independence uses full kernel transport and does not assume an
already-correct target map. Its final theorem combines norm-kernel membership,
equivariance, the Frobenius cube law on two-torsion and squared fixedness to
derive a rational two-torsion correction. Averaging the three conjugates gives
a rational preimage because three acts as one on two-torsion.
[pcc:unverified]

The eight lemmas concern arbitrary functions and integer modules. They do
not encode the elliptic curves, Weil restrictions, polarized HLP quotients,
finite fields or Picard algorithms. Required geometric bridges remain:
the dual norm identity and its two-torsion image kernel; the cube law on
the actual restriction's two-torsion; equivariance and squared fixedness of
the norm-half difference; transport of the entire fixed kernel; and the
identification of Frobenius-fixed canonical classes with the required base
field. Native two-torsion and origin checks support specific program inputs
without discharging those geometric bridges. [pcc:unverified]

The fixed model masks and all Phase B–D populations remain exactly those
in the published protocol5caf67. This proof source does not claim that the
complete Jacobian chain has run, that a finite panel proves universal
correctness, or that any operation vector has a calibrated cost.
[pcc:unverified]
