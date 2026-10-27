# Frozen Fricke certificate transport

`transport_inputs.json` pins the six completed exact-dependency
certificate files before this compression pass. For each of the five
conductors 60, 70, 90, 150, and 210, first verify that the archived
integer row multiset is Fricke-closed under `P ↦ T−P` with
`T=(16,−61)`. The two recovered degree-2 rows must map to each other.
Choose the certificate with the smaller nonzero support, breaking a
tie by source-column order. Map every archived row in that
certificate through the Fricke column permutation to an archived
row with the same integer vector, preserving its coefficient.

The transported certificate is accepted only after a fresh full
integer vector equality check against the partner target. Store its
support, denominator, row-index mapping, and any failure. Conductor
42 is kept on its original exact certificates because its archived
row multiset is not Fricke-closed. This is a finite certificate
compression step, not a claim about arbitrary Hecke matrices.
