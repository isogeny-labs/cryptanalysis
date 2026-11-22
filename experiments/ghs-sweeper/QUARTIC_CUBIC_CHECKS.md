# Ordinary cubic-bitangent quartic census, frozen 2026-10-25

Question: do the two F512 source trace classes +/-35 absent from the old
hyperelliptic sweep have ordinary nonhyperelliptic genus-three targets over F8
in the published O3 family? This is an exact finite census, not a performance
experiment or a new mathematical family. Publication priority and an explicit
prime-subgroup/log map remain separate requirements. No rho gate is imposed.

Baseline: Nart--Ritzenthaler, arXiv:math/0312366v2, section 1.4, O3 normal
models. Choose the deterministic F8 power basis (modulus 11) and cubic
extension basis F512 (modulus 515). Construct a root v of v^3+v^2=s,
its q-conjugates and the correctly oriented resolvent parameter t. Verify
the norm identity, resolvent relation and primary nonsingularity conditions.

Enumerate all 8^6=262,144 coefficient vectors Q in their published order
(a,b,c,d,e,f). The smooth vector count must be 228,481 and the number of
representatives under their stated cyclic order-three action must be 76,189,
matching the paper's formulas at q=8. No general isomorphism-deduplication
claim beyond that published O3 action is substituted.

Count projective points over F8 and retain N1=9; over F64 retain N2=65;
over F512 compute N3 for every survivor. Recover the exact cubic-restriction
trace t=(513-N3)/3, checking integrality, oddness and the Hasse interval.
The target counts for +/-35 are N3=408 and 618, respectively. All target
quartics and the first representative of each observed source trace are
retained. Hash ordered stage coverage so the full census can be replayed.
Do not treat a matching Weil polynomial as an evaluated elliptic map.

The fast counter uses Q=sqrt(R), quadratic-monomial lookup rows and
last-nonzero projective normalization. Independently replay every target
quartic plus the first witnesses for the three smallest observed traces
using raw carryless arithmetic, the expanded quartic equation and
first-nonzero projective normalization. Both counts share the same declared
field embeddings; replay their products with raw arithmetic. No external
independent implementation review is implied.

Controls: primary norm identity on all 512 F8 triples; nonsingularity versus
direct equation evaluation at all seven critical Fano points for 64 fixed
binary coefficient vectors; singular Q=0 and Q=x^2+y^2+z^2; a fixed smooth
Q=2*x^2; alternative projective counts on four fixed models; invalid
coefficient and thread values. Format, Clippy and all release tests must pass.
Run the complete census with two threads, retain raw successes/failures,
source hashes, exact commands, exits and execution durations as receipts.
No Sage, GPU, paid resource or older denominator job is needed or authorized
by this contract. Preserve all earlier frozen manifests and checkpoint data.

If a target appears, it is a new local spectral match for these two source
classes, pending published-priority comparison and explicit log transport.
If none appears, the conclusion is zero in the declared published O3 family;
any broader genus-three nonexistence statement needs its additional proof.
