# Prime-field rational evaluation of the first Jacobian adjoint

Scientific standing unsigned. This is the reverse of the existing fixed
T0→T1 transfer, not a new isogeny family. It uses the written global
identifications in PRIME_FIELD_PSI_PROOF.md/78176c and
QUARTIC_PULLBACK_PROOF.md/4934b4, the accepted direct T1 norms18/c3a1a7,
and the accepted T0 pullbacks13/5143f5. Runtime acceptance is separate.
[pcc:unverified]

Write K_i for the sum of the two direct pullbacks from the elliptic product
to Jac(T_i), and H_i for the pair of direct norms. Under the old principal
polarizations these are adjoints, with H_i K_i=[4] on the product and
K_i H_i=[4] on Jac(T_i). The accepted old global transfer satisfies

    [4]Psi = K_1 alpha H_0.

Taking adjoints gives

    [4]PsiHat = K_0 alphaHat H_1.

The implemented rational groups all have order12317=109*113, so4 is
invertible. On the factors the public inverse4 scalars are82 modulo109
and85 modulo113. Therefore the rational-point algorithm is: evaluate both
T1 norms, multiply by the corresponding inverse4, evaluate alphaHat,
pull each point back directly to T0, and add the resulting balanced
classes. This identifies the old PsiHat on all rational inputs given the
stated global identities. It does not construct a global inverse of[4].
[pcc:unverified]

The first reverse elliptic Kohel kernels, low coefficient first, are
[58,26,58,1] on E109'=(26,58) and[29,88,45,1] on E113'=(69,50).
The normalized codomains are(78,72) and(99,68). Scaling
(x,y) to(29²x,29³y) returns the original models(1,46) and(44,21);
29=1/7 in F101. Both short-Weierstrass coefficient equations must be
checked before using that scale. Existing seven.rs certifies these dual
maps, their coefficient identities and both elliptic compositions[7].
The prototype compares the selected kernels/numerators/denominators/
domains/codomains/scale with that retained reference. [pcc:unverified]

For embedded elliptic source inputs the global relation also gives
PsiHat K1,j=K0,j alphaHat_j, by cancelling[4] in Hom. Thus one reverse
elliptic evaluation and one T0 pullback are the direct endpoint control
for this source. As in SOURCE_ENDPOINT_CONTROL_V2.md/c2b7c9, this is a
restricted input route, not an evaluation of arbitrary Jacobian classes
from one factor. [pcc:unverified]

The planned native acceptance retains all12317 exact olddual outputs,
bijection, fixed-partner sums, negations, identity, wrong-model rejection,
and both whole-domain composition identities[7], plus every109/113
reverse embedded-source endpoint. Constructors/evaluators use existing
F101 polynomial/elliptic/Kohel/Balanced engines; old Richelot/extension
fields occur only in the separately invoked reference checks. T1 split
pole cases remain included by the accepted norm adapter. [pcc:unverified]

Sources checked: the above accepted written maps and their primary
Picard/norm/dual sources; existing seven.rs normalized dual implementation;
external CT36/cryptanalysis PR1502 is relevant prior work for reverse7
normalization. KB/ecdb unavailable. No novelty, cost or timing claim is
made here, and geometric/Picard bridges remain written. [pcc:unverified]

## Actual consumer implementation and complete guard

The actual first-adjoint child from b297/ready1506 adds the accepted T1
norm data and standalone adjoint,while SevenChain.dual selects this API.
The exact original dual body remains dual_reference;the new complete
comparison explicitly calls that old reference. Original forward,
forward_reference,quarter,naive and old test suffix are unchanged.
The constructor/evaluator bodies match the accepted upstream24 source;
the moved endpoint test calls existing Pullback::fixed(1,i) directly.
Static/source02 custody ccfb25 and full03/d744cf bind the actual code.
[pcc:unverified]

Complete actual check.sh03 exits0 with25native/92reference unit+five
integrations/one historical ignored. Both new full-domain tests and
all original90 tests pass. All9source02 hashes remain unchanged;
whole136317-byte raw is standardXZ15244bytes with raw/archive hashes
and exact roundtrip. The failed private-field compile01/bb323e remains.
Parent1506 exactb297 focused43180569278 passes25/90+five;full decoded
CI log/API/custody64e1d9 is retained here. New child ownCI is separate.
[pcc:unverified]
