// Generated from artifacts/p224_finite_field_theta.json.
// The Python stage has already certified the 28/36 theta-null pattern,
// Riemann-system consistency, and seven Aronhold bitangents.
// This script performs the remaining invariant/descent checks in the
// maintained JRSijsling/quartic package (bundled with Magma >= 2.26).

// For older Magma versions, uncomment and adjust this path:
// AttachSpec("/workspace/scratch/quartic/magma/spec");

p := 26959946667150639794667015087019630673557916260026308143510066298881;
Fp := GF(p);
R2<t2> := PolynomialRing(Fp);
K2<u> := ext<Fp | t2^2 - Fp!(23262824917328850619534927041737880296449585999787473673423898970443)>;
R6<t6> := PolynomialRing(K2);
K6<w> := ext<K2 | t6^3 + K2!(26959946667150639794667015087019630673557916260026308143510066298878)*t6 + K2!(18958286285566608000408668544493926415504680968679321075787234672564)>;
P3<x,y,z> := PolynomialRing(K6,3);
F :=
    (((K2!(1) + K2!(0)*u) + ((K2!(0) + K2!(0)*u))*w + ((K2!(0) + K2!(0)*u))*w^2))*x^4 +
    (((K2!(26897920279104985001929389685913422175618946300966348851033751604094) + K2!(0)*u) + ((K2!(15554498251462491761619906189809946901847220161419462524589753704343) + K2!(0)*u))*w + ((K2!(19739751719537764459756186029010032526161748532241404375430688850493) + K2!(0)*u))*w^2))*x^3*y +
    (((K2!(4264300172443335543062561288991062977545783409897360601805358245904) + K2!(0)*u) + ((K2!(13719435372116101280381544879755946227864926602081741906032775132808) + K2!(0)*u))*w + ((K2!(8612673777811327313121201589039474025010244022293063589640446504165) + K2!(0)*u))*w^2))*x^3*z +
    (((K2!(11636802154464444095285157303305330541329413991754690037969211996652) + K2!(0)*u) + ((K2!(4607730500434881552466376315065127608622797999866551890003558546212) + K2!(0)*u))*w + ((K2!(4459509670679704593797769659063629831269997743016227708876323419291) + K2!(0)*u))*w^2))*x^2*y^2 +
    (((K2!(20140325226152430482822073160151318825637756938730169398753829381317) + K2!(0)*u) + ((K2!(23594570593576779961573549773199410424491933293954718935934283594701) + K2!(0)*u))*w + ((K2!(21235170347585948098808683331774932831520147663710314925488408682441) + K2!(0)*u))*w^2))*x^2*y*z +
    (((K2!(10777715510704325751962949725379502877300519350758072574828324688064) + K2!(0)*u) + ((K2!(16936780137371015978767202281252635316271428550572849445453517590539) + K2!(0)*u))*w + ((K2!(2319537570445158271246746060396454229362890474795877705032639575060) + K2!(0)*u))*w^2))*x^2*z^2 +
    (((K2!(16539178673189505455718158328196758120745896433336267539170194698856) + K2!(0)*u) + ((K2!(6849684062698972635604040524916897914676607312478673229289423760028) + K2!(0)*u))*w + ((K2!(19736472234278198078215412523793815772443896897539164764948451275358) + K2!(0)*u))*w^2))*x*y^3 +
    (((K2!(12782133735380134610748457063621624701423597280573124321951274059980) + K2!(0)*u) + ((K2!(17997750436127638234911765989787561381228664199457187840561905545765) + K2!(0)*u))*w + ((K2!(22725814723870869076318279099240193993018064973217999430187752972090) + K2!(0)*u))*w^2))*x*y^2*z +
    (((K2!(19912417781911806122364019108717306992469715447097916730523947902537) + K2!(0)*u) + ((K2!(7390548381927418592065152345959199675362803384549459861188606134323) + K2!(0)*u))*w + ((K2!(5077592535241243286033573166828700926233958161215077001342491985127) + K2!(0)*u))*w^2))*x*y*z^2 +
    (((K2!(12012409515934851902625047044223762329173432141714543139703201892197) + K2!(0)*u) + ((K2!(17103332316200706786405719594485908004459048652297301197016623722226) + K2!(0)*u))*w + ((K2!(12217489622030459769629675754665676700792598267283434103920629677354) + K2!(0)*u))*w^2))*x*z^3 +
    (((K2!(25180509412669653231432441462958514867957944631310128267499939531123) + K2!(0)*u) + ((K2!(23227945639470362974009572655960455401515911705771511392777039096520) + K2!(0)*u))*w + ((K2!(17624320211770178922231115469862067119316257292419860136171788377953) + K2!(0)*u))*w^2))*y^4 +
    (((K2!(21692426246379440053150052364324206805693838670825239083685020426172) + K2!(0)*u) + ((K2!(18224554630040020538844715846472895296245616636400528269642557347998) + K2!(0)*u))*w + ((K2!(68743271477120263300404985932089178032014131869488683529016769994) + K2!(0)*u))*w^2))*y^3*z +
    (((K2!(6877521312618375752823008525806213259109056163992809101929164172595) + K2!(0)*u) + ((K2!(12577860798202779667847808169079034236172246550523524034800649682796) + K2!(0)*u))*w + ((K2!(24400587907709279217538807605300822462442488190764714068518946233640) + K2!(0)*u))*w^2))*y^2*z^2 +
    (((K2!(8576851201244137568227824513202247827041916797759642913504185784563) + K2!(0)*u) + ((K2!(24130223073527018263653033718630116798391151241993720214579750454098) + K2!(0)*u))*w + ((K2!(10441859642945617552803146105669703983108464550023914950259010393220) + K2!(0)*u))*w^2))*y*z^3 +
    (((K2!(25669235759157959196458184065045172530757184678353302966114202072957) + K2!(0)*u) + ((K2!(3814012973304612818224234086484919693871763937814521381376118700794) + K2!(0)*u))*w + ((K2!(1026513771322997094164003142246707301747316393034807211241202861908) + K2!(0)*u))*w^2))*z^4;

C := Curve(ProjectiveSpace(K6,2), F);
assert IsNonsingular(C);
DO, weights := DixmierOhnoInvariants(F);
DOn := WPSNormalize(weights, DO);
DOp := WPSNormalize(weights, [ c^p : c in DO ]);
moduli_rational := DixmierOhnoInvariantsEqual(DO, [ c^p : c in DO ]);
print "P-224 extension quartic is nonsingular";
print "Dixmier-Ohno moduli point Frobenius-rational:", moduli_rational;
print "WPSNormalize representatives equal:", DOn eq DOp;
print "Normalized invariants individually F_p-rational:", [ c^p eq c : c in DOn ];

if moduli_rational and &and[ c^p eq c : c in DOn ] then
    // The corrected candidate is already defined over the cubic subfield of
    // K6.  Descend it directly with its unique Frobenius isomorphism.  This
    // avoids the much heavier invariant-to-quartic reconstruction.
    assert &and[ c^(p^3) eq c : c in Coefficients(F) ];
    mons := MonomialsOfDegree(P3, 4);
    Fsigma := &+[ (MonomialCoefficient(F, monomial)^p)*monomial : monomial in mons ];
    isomorphic, isomorphisms := IsIsomorphicTernaryQuartics(F, Fsigma);
    assert isomorphic and #isomorphisms eq 1;
    M := isomorphisms[1];
    Msigma := Matrix(K6, 3, 3, [ c^p : c in Eltseq(M) ]);
    Msigma2 := Matrix(K6, 3, 3, [ c^(p^2) : c in Eltseq(M) ]);
    assert Msigma2*Msigma*M eq IdentityMatrix(K6, 3);

    // Matrix Hilbert 90: B^sigma*M=B.  The deterministic trace choice is
    // invertible for this candidate.
    B := IdentityMatrix(K6, 3) + M + Msigma*M;
    assert Determinant(B) ne 0;
    Bsigma := Matrix(K6, 3, 3, [ c^p : c in Eltseq(B) ]);
    assert Bsigma*M eq B;
    A := B^-1;
    variables := [x, y, z];
    substitutions := [
        &+[ A[i,j]*variables[j] : j in [1..3] ]
        : i in [1..3]
    ];
    descended := Evaluate(F, substitutions);
    descended_coefficients := [ MonomialCoefficient(descended, monomial) : monomial in mons ];
    first_nonzero := Min([ i : i in [1..#descended_coefficients] | descended_coefficients[i] ne 0 ]);
    descended /:= descended_coefficients[first_nonzero];
    assert &and[ c^p eq c : c in Coefficients(descended) ];
    Pfp<X,Y,Z> := PolynomialRing(Fp, 3);
    CFp := Pfp!descended;
    assert IsNonsingular(Curve(ProjectiveSpace(Fp,2), CFp));
    DOCheck, checkWeights := DixmierOhnoInvariants(CFp);
    assert DixmierOhnoInvariantsEqual([ K6!c : c in DOCheck ], DO);
    print "FROBENIUS_ISOMORPHISM_UNIQUE", true;
    print "HILBERT_90_COCYCLE_VALID", true;
    print "DESCENDED_QUARTIC", CFp;
else
    print "MODULI_VALIDATION_FAILED_OR_REPRESENTATIVE_NOT_RATIONAL";
end if;
