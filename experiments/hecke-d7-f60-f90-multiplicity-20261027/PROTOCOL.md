# Frozen D=-7 conductor-60/90 multiplicity replay

The two inputs are the saved `D_K=-7` conductor-60 and conductor-90
class-walk matrices under `experiments/ecdlp-hecke-floor-rank-20261012/data/`.
Their SHA-256 digests are, respectively,
`39faa7734979733b3035fb6c25c39b1c0a5e389bd4c54a6c65965da1d8cce434`
and `4cb80fb8f8a10a138455dbf6be0c3fb229af6d6367f255000bf06ab9010f38b8`.
The fields are `F_6301` and `F_14431`, with 280/476 saved class points,
234/444 saved rows, and Hecke degrees 2, 3, and 5. The archived
rational ranks are 184 and 332.

Use the archived Hecke function source at
`experiments/ecdlp-hecke-floor-rank-20261012/tools/hecke11.py`, SHA-256
`7e66144e76bf62f7e645d87cc58be2bb0f7cc5e52601665650ef0706a6f715fb`,
and the generic multiplicity-aware collector at
`experiments/hecke-multiplicity-collector-20261026/multiplicity.py`,
SHA-256 `89a6cfd5951666587589834d8b8e288aaf0dfc48d9e310df62ef44c48f5bca1e`.

For every saved point and degree, count rational x-roots with
multiplicity, run the generic collector on repeated-root fibers, and
retain its explicit status. Preserve every archived complete neighbor
multiset. Admit a new row only when its full neighbor multiset lies in
the frozen point set, all x/y moments and the Hecke group sum hold, and
every neighbor passes the classical modular-polynomial test. Compare
integer row multisets before/after, exact rational and two modular
ranks, and closure under the Fricke involution. Independently replay
new group sums and rank changes with integer affine arithmetic and
sparse modular elimination. Preserve any failure or incomplete result.
