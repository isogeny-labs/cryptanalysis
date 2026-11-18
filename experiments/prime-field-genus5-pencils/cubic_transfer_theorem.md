# Recognizing the paired-cubic Jacobian transfer

Repository proof status is unverified. [pcc:unverified]

## Result and prior work

Fix \(g\ge4\) and a finite field \(k=\mathbb F_q\) of characteristic greater than three. Let \(H/k\) be a genus-\(g\) hyperelliptic curve. The recognition test below finds a cubic map of its hyperelliptic base with the following properties, if one exists.

- The cubic is simply branched. Each of \(g+1\) distinct unramified fibers contains exactly two hyperelliptic branch points, accounting for all \(2g+2\) branch points.
- The norm of a function defining the double cover is a square in the function field of the cubic target.

For fixed genus the test has expected cost polynomial in \(\log q\). A qualifying cubic gives a rational correspondence to a nonhyperelliptic genus-\(g\) curve \(X\). The composition with the transpose correspondence acts as \([2]\) on \(J_H\). In particular, it preserves the order of any odd-order cyclic subgroup. With the existing nonhyperelliptic index-calculus bound the transfer gives expected time \(\widetilde O(q^{2-2/(g-1)})\), compared with the direct fixed-genus hyperelliptic bound \(\widetilde O(q^{2-2/g})\). The transfer and the resulting bound concern the paired-cubic family. [Nonhyperelliptic bound](https://www.math.uni-leipzig.de/~diem/preprints/plane-models.pdf) · [Direct class-group bound](https://doi.org/10.1090/S0025-5718-2010-02281-1)

Frey and Kani already describe the same \(S_4\) construction for arbitrary genus, the dimension-\((g+2)\) Hurwitz family, rational descent, and polynomial-time evaluation when the paired cubic is known. Their Remark 4 leaves finding the cubic from the input hyperelliptic curve open in general. Section 5.1 treats genus 3. Smith's genus-3 algorithm already uses the Klein quadric and four linear pair conditions. The addition here is that for \(g\ge4\) every admissible pairing forces **exactly five independent linear conditions**. This gives a uniform recognition procedure even when other pairings of the input points give lower-rank systems. It also gives an explicit quartic equation and a direct proof of subgroup retention. This is a recognition result for the existing family, with no further exponent decrease once a valid cubic is supplied. [Frey–Kani, §§4.3–4.6 and 5.1](https://www.queensu.ca/academia/kani/sites/acadkaniwww/files/uploaded_files/Papers/fkwarsawarticlerevised.pdf) · [Smith, §5](https://arxiv.org/abs/0806.2995) · [Donagi–Livné](https://arxiv.org/abs/alg-geom/9712027)

Donagi–Livné's obstruction concerns generic higher-genus Jacobians with Lagrangian quotients. Naranjo–Pirola rule out nonhyperelliptic isogenous targets for very general hyperelliptic Jacobians over \(\mathbb C\) in genus at least four. The paired-cubic construction starts in a proper locus, since its Hurwitz parameter space has dimension \(g+2<2g-1\) for \(g\ge4\). These generic obstructions are compatible with the family studied here. Boyer's separately circulating construction concerns genus-three hyperelliptic pairs. [Naranjo–Pirola](https://arxiv.org/abs/1705.10154) · [Boyer](https://www.normalesup.org/~iboyer/files/agct14Boyer.pdf)

## 1. Recovering the cubic from the source curve

Let \(V=H^0(\mathbb P^1,\mathcal O(3))\), with basis \(1,x,x^2,x^3\) on an affine chart. A cubic map up to changes of target coordinates is a two-plane in \(V\) spanned by relatively prime homogeneous forms \(N,D\). Write \(p=[N\wedge D]\in\mathbb P(\wedge^2 V)=\mathbb P^5\). A pair of distinct points \(x,y\) lies in one fiber exactly when

\[
\langle p,\operatorname{ev}(x)\wedge\operatorname{ev}(y)\rangle=0.
\]

After division by \(y-x\), the coefficients on the affine chart are

\[
(1,\ s,\ s^2-b,\ b,\ sb,\ b^2),\qquad s=x+y,\quad b=xy.
\]

Homogenizing in the coefficients of the binary quadratic with roots \(x,y\) shows that this map on \(\operatorname{Sym}^2\mathbb P^1\simeq\mathbb P^2\) is the quadratic Veronese map, composed with an invertible linear change of coordinates. The fiber-pair condition of a degree-three map is thus a conic in \(\operatorname{Sym}^2\mathbb P^1\).

For a simply branched cubic this conic is geometrically integral. Its off-diagonal part parametrizes unordered pairs in cubic fibers. Over the generic target point those pairs form a transitive \(S_3\)-set, since a simply branched degree-three cover has monodromy \(S_3\). The generic pair fiber is reduced because the cubic is generically étale. A component of off-diagonal pairs cannot be confined to one target value, whose fiber has finitely many points. The diagonal cannot be an extra component, since restriction of the divided equation to it is the numerator of the derivative of the separable cubic. This proves the conic is reduced and geometrically irreducible. [pcc:unverified]

Its Veronese image spans a projective four-space and is a rational normal quartic there. For example, the six quadrics on \(\mathbb P^2\) restrict to the five-dimensional complete system of degree four on the conic, with the defining conic equation as the kernel. Evaluations at any five distinct geometric points on this rational normal quartic are independent, by interpolation of degree-four polynomials. Any matching of \(g+1\ge5\) disjoint pairs admitted by a qualifying cubic therefore has rank five. Its one-dimensional common kernel is precisely the required Plücker point. In particular, a rank-deficient matching can be discarded without solving a positive-dimensional system.

To run the test, factor the geometric branch polynomial in a splitting field of bounded degree and enumerate its perfect matchings. The number of matchings depends only on \(g\). Retain matchings stable under \(q\)-Frobenius, since any rational cubic with the required distinct fiber values induces such a matching. For each matching, form the linear evaluation equations above. Expanding coefficients in a basis of the splitting field over \(k\) makes this a linear system over \(k\). A geometrically one-dimensional kernel for a Frobenius-stable matching descends to a one-dimensional kernel over \(k\).

When the rank is five, compute its kernel point and check the Klein quadric equation

\[
p_{01}p_{23}-p_{02}p_{13}+p_{03}p_{12}=0.
\]

Recover its rational two-plane and compute a basis \(N,D\). Check that the binary cubics have no common root, that the discriminant of the cubic fibers has four distinct roots, and that none of the paired values is a branch value of the cubic. These conditions are fixed-degree resultant and factorization tests. A cubic fiber cannot contain two disjoint pairs, so the matching fiber values are automatically distinct once the degree is exactly three.

For the descent check, choose the rational source point at infinity outside the preimages of the matched target values, then move its image to target infinity. There are at most \(3(g+1)\) excluded source points, so a bounded number of trials suffices for \(q\) large enough at fixed \(g\). The finitely many smaller fields at fixed \(g\) can use homogeneous norm computations directly. In these coordinates take \(N\) monic of degree three, \(\deg D\le2\), and \(F(x)=a\prod_w(x-w)\) with degree \(2g+2\), where \(w\) runs over the branch points. For \(x_1,x_2,x_3\) the roots of \(P_t(x)=N(x)-tD(x)\),

\[
\operatorname{Norm}_{k(x)/k(t)}F(x)
=a^3\prod_w D(w)\,\prod_{i=1}^{g+1}(t-t_i)^2.
\]

This follows by \(\prod_j(x_j-w)=-P_t(w)=D(w)(t-h(w))\), where \(h=N/D\). The descent check is therefore one square test on \(a^3\prod_w D(w)\in k^\times\). Retain the given source twist only when the test succeeds. Changing its leading scalar to enforce the test would change the source curve over \(k\).

All field extensions, polynomial degrees and matrix dimensions here are bounded for fixed \(g\). Finite-field factorization, linear algebra and square testing give the expected polynomial bound in \(\log q\). The test decides eligibility for this specified simply branched, paired and square-norm construction. Other isogenies can exist outside this criterion.

The five-pair uniqueness also gives a shorter search. At each of five levels, take the first unused branch point in a chosen ordering and try each unused partner. Solve the rank-five system at each leaf, then evaluate the recovered cubic on all branch points to reconstruct and validate the complete pairing. The partial pairing may fail to be Frobenius-stable, so test rationality of its unique projective kernel before descending. Every valid complete matching appears on at least one such path. This uses at most \((2g+1)(2g-1)(2g-3)(2g-5)(2g-7)\) leaves, which is 135,135 in genus seven. The required splitting field still has degree bounded in terms of \(g\).

## 2. The nonhyperelliptic target and its correspondence

Assume the test succeeds and write \(r(t)^2=\operatorname{Norm}F(x)\). For a generic value \(t\), choose one \(y_j\) above each \(x_j\), with \(y_j^2=F(x_j)\) and \(y_1y_2y_3=r(t)\). There are four such unordered triples. The square-norm equality makes the four-choice cover and the incidence with \(H\) rational over \(k\).

The geometric monodromy of the two-cover over the cubic lies in the even signed permutation group \(V_4\rtimes S_3\), which acts as \(S_4\) on the four triples. The projection onto \(S_3\) is surjective. Inertia at any paired branch value acts by flipping two signs, hence gives a nonzero element of \(V_4\). The three nonzero elements of \(V_4\) form one conjugacy orbit under \(S_3\), so the geometric group is the whole \(S_4\). This also forces the arithmetic group to be \(S_4\), as it lies in the same signed permutation group. At a cubic branch value, inertia has order two and projects to a transposition. It acts on the four triples as a transposition. At each of the \(g+1\) paired branch values it acts as a double transposition. Other values are unramified. Riemann–Hurwitz gives

\[
2g(X)-2=-8+4+2(g+1)=2g-2.
\]

The normalized target \(X\) therefore has genus \(g\). Its degree-four map to \(\mathbb P^1_t\) is primitive because the point stabilizer \(S_3\) is maximal in \(S_4\). If \(X\) were hyperelliptic, its degree-two and degree-four maps would jointly be birational onto their image. Any nontrivial common intermediate covering would have degree two and make the degree-four map imprimitive. Castelnuovo–Severi would therefore give genus at most three, contradicting \(g\ge4\).

An explicit plane equation for the normalization is obtained from \(z=y_1+y_2+y_3\). Let \(s_1(t)=\sum_j F(x_j)\) and \(s_2(t)=\sum_{i<j}F(x_i)F(x_j)\), which can be computed by the trace and the second characteristic coefficient of multiplication by \(F\) in the cubic algebra. Then

\[
z^4-2s_1(t)z^2-8r(t)z+s_1(t)^2-4s_2(t)=0.
\]

The four sums are distinct generically. A collision would force two of the \(F(x_j)\) to be equal as elements of the geometric splitting field, so the \(S_3\)-action would force all three to be equal. In that case \(F\) descends to \(k(t)\) after base change, incompatible with its branch valuations on a fiber with two marked branches and one unmarked branch. The quartic thus presents the correct function field. For a generic source point \((x,y)\), its two target points satisfy

\[
(z-y)^2=s_1(t)-F(x)+2r(t)/y,\qquad t=h(x).
\]

Take the closure and normalization of the incidence of a source point with a target triple containing it. Pull-push along this incidence gives a map \(\phi:J_H\to J_X\). The reverse incidence gives \(\psi:J_X\to J_H\). For a generic source point \(P\), two triples contain \(P\). Summing the points in these two triples gives \(2P\) and a whole hyperelliptic fiber above each of the other two cubic roots. Whole hyperelliptic fibers are linearly equivalent to each other, so taking differences yields \(\psi\phi=[2]\) on \(J_H\). This shows \(\phi\) is an isogeny, without a simplicity assumption. Standard bounded-degree function-field normalization and pull-push on divisors handle the excluded fibers and allow evaluation in expected time polynomial in \(\log q\) for fixed \(g\). [Function-field evaluation and transfer](https://www.queensu.ca/academia/kani/sites/acadkaniwww/files/uploaded_files/Papers/fkwarsawarticlerevised.pdf)

For any cyclic subgroup generated by \(G\), \(\ker\phi\cap\langle G\rangle\) has order at most two. Thus a DLP solution on \(\langle\phi(G)\rangle\) has at most two lifts modulo \(\operatorname{ord}(G)\), which can be checked on \(H\). For odd order there is one lift. For the even-order case with only the ambient order \(N\) supplied, let \(D=H_0-x_0G\) be the error for a solution \(x_0\) to the image problem with target \(\phi(H_0)\). When \(D\ne0\), it is the unique nonzero two-torsion point in \(\langle G\rangle\). Write \(N=2^eM\) with \(M\) odd. Repeated doubling of \(MG\) determines its order \(2^j\), and \(x_0+2^{j-1}M\) solves the source problem. This costs \(O(\log N)\) group operations. The Jacobian orders over \(k\) coincide by isogeny, so the supplied source order suffices for the target solve. [pcc:unverified]

## 3. Explicit inputs and the genus-four quintic

One way to generate inputs in this family is to set \(N=x^3+x\) and \(D=x^2+2\). The derivative numerator is \(x^4+5x^2+2\) and has four distinct roots in characteristic greater than three different from \(17\). Its roots avoid the simple poles, and infinity is unramified. Two ramified points cannot have the same image under a cubic, so these are four distinct branch values.

Choose \(m=g+1\) rational points \(u_i\) away from the poles and ramified fibers and with distinct \(t_i=h(u_i)\). Put

\[
Q_i(x)=\frac{N(x)-t_i D(x)}{x-u_i},\quad
c=\prod_i D(u_i)/2^m,\quad F(x)=c\prod_i Q_i(x).
\]

Each \(Q_i\) accounts for the other two geometric roots of the cubic fiber. They may be conjugate. The values satisfy \(\operatorname{Norm}D(x)=2\) for this cubic, so \(\operatorname{Norm}Q_i(x)=2(t-t_i)^2/D(u_i)\), and \(r(t)=c\prod_i(t-t_i)\) gives the rational four-choice cover. The rational omitted-root bounds are constant at fixed genus, so these inputs exist over sufficiently large finite fields of the stated characteristics.

In genus four, any rational point \(P\in X(k)\) gives a degree-five birational plane model by projecting the canonical curve through \(P\). The three-dimensional space of sections of \(K_X(-P)\) has no base point, by very ampleness of the canonical embedding. The plane image is nondegenerate and the product of the map degree and image degree is five. Hence the image has degree five and the map is birational. This gives a quintic construction even if the explicit resolvent equation above has higher plane degree. In characteristic greater than five the quintic is reflexive. The general nonhyperelliptic model theorem supplies the same exponent in the remaining admissible characteristic. This realizes the existing \(\widetilde O(q^{4/3})\) genus-four target bound. A lower plane degree is impossible since a plane quartic has arithmetic genus three. [Diem's plane-model bound](https://jtnb.centre-mersenne.org/articles/10.5802/jtnb.815/)

In genera 4–7 the transferred class-wide exponents are \(4/3,\ 3/2,\ 8/5,\ 5/3\). The target is tetragonal, so a genus-seven target does not meet the \(W^1_4=\varnothing\) hypothesis of the higher-genus pencil argument. Obtaining a lower-degree target plane model or a suitable different pencil family would be an additional problem for this transfer.

## 4. A certified genus-five target with a stronger bound

There is a paired-cubic example over \(\mathbb F_{19}\) to which the [genus-five two-hop theorem](genus5-bridge.md) applies. Use the cubic in §3 with omitted roots \((18,8,10,14,5,16)\) and values \((12,5,14,17,2,18)\). The source polynomial's coefficients in ascending degree are

\[
(15,14,1,11,1,5,1,4,5,0,16,5,8).
\]

For this source, Sage computes the Weil polynomial

\[
T^{10}-6T^9+35T^8+24T^7-514T^6+4988T^5-9766T^4+8664T^3
+240065T^2-781926T+2476099.
\]

It is irreducible modulo \(31\), so the source Jacobian is simple over \(\mathbb F_{19}\). To certify absolute simplicity, let \(a\) be a root of its reduction in \(\mathbb F_{31^{10}}\). Two distinct complex roots \(\pi_i,\pi_j\) of the Weil polynomial generate a field of degree at most \(10\cdot9=90\). If \(\pi_i/\pi_j\) had order \(m\), this would give \(\varphi(m)\le90\) and hence \(m\le 16200\) by \(\varphi(m)\ge\sqrt{m/2}\). The certificate tests all 173 such \(m\ge2\) and finds that \(a^m\) lies in none of the proper subfields \(\mathbb F_{31^j}\), \(j=1,2,5\). Indeed \(a^{m(31^j-1)}\ne1\) in each case. Thus every candidate power has degree ten modulo \(31\). An integer characteristic-zero power with a minimal polynomial of smaller degree would give a smaller-degree relation after reduction. This excludes every collision of Frobenius eigenvalue powers. The Weil polynomial stays irreducible over every finite base-field extension, since the Galois action on the distinct powered roots remains transitive. The source Jacobian is therefore absolutely simple.

### Certification of the pencil locus

For the normalized quartic target, the three canonical quadrics have affine common-zero cone dimension two. Their projective intersection is a complete intersection of degree eight and contains the degree-eight nonhyperelliptic canonical curve, so it equals the curve. It follows that the target is nontrigonal. Clifford's theorem also rules out \(W^2_4\), which would have Clifford equality on a nonhyperelliptic curve. These tests use geometric dimensions and the conclusions persist after field extension.

Write \((U,V,W)\) for coordinates on the canonical net. Its determinant quintic is irreducible over \(\mathbb F_{19}\), and \([1:0:14]\) is a smooth rational point. This proves geometric irreducibility. An irreducible quintic over the ground field could split geometrically only into five conjugate lines, in which case every rational point would lie on all the lines and be singular. On the \(U=1\) chart the singular ideal has Gröbner basis \((V+8,W+3)\). The net quadric at \([1:11:16]\) has rank three and the determinant curve has an ordinary node there, as its two-variable Hessian determinant at that point is \(11\). [pcc:unverified]

The two possible plane rulings of a rank-four net quadric give the two degree-four pencils over a generic point of this quintic. Conversely, a degree-four pencil \(L\) and its residual pencil \(K_X-L\) give the quadric from the four products of their sections. The base-point-free pencil trick gives four independent products when \(L\ne K_X-L\), yielding the two rulings of the rank-four quadric. In the self-residual case the three symmetric products give a rank-three quadric. The rank-three quadrics in an integral determinant curve occur at finitely many points, and each gives at most one pencil. This description identifies the reduced pencil curve birationally with the ruling double cover. The dimension bound \(\rho(5,1,4)=1\) for every component excludes isolated extra pencil components. The full determinantal scheme is also reduced. Since every pencil and its residual have exactly two sections, the local rank equations reduce to the four entries of a \(2\times2\) block. The locus has the expected codimension four and is a local complete intersection. It is generically smooth by the pencil trick and the Petri tangent criterion, so Cohen–Macaulayness and generic reducedness imply reducedness. These arguments apply after base change to the algebraic closure. [Genus-five Brill–Noether and rank loci](https://www.math.stonybrook.edu/~roblaz/Reprints/Lazarsfeld.BNP.pdf)

The ruling cover is geometrically connected because it branches above the ordinary rank-three node. To see this, at that node split off a nonsingular \(3\times3\) block in the symmetric quadric matrix. The remaining Schur complement is a \(2\times2\) symmetric matrix vanishing at the node. The determinant of its linear part is the nodal tangent cone up to a unit. Along either of the two normalized branches, the first-order residual matrix is rank one and nonzero. A one-dimensional nondegenerate subspace of that residual form contributes exactly one power of the local uniformizer to the determinant of a nondegenerate rank-four quotient. The two rulings of a rank-four quadric are distinguished by the square root of that quotient determinant. The resulting square class has odd valuation, so the ruling cover remains a field extension over the algebraic closure. This certifies geometric integrality of \(W^1_4\).

Finally, the rank-four net quadric at \([1:7:17]\) supplies a simply branched pencil. In the canonical basis used by the certificate, the ratio of the following two forms gives its map.

\[
(1,0,1,16,0)\big/(0,1,13,16,17).
\]

The square-free branch polynomial factors into degrees seven and nine. Their coefficients in ascending order are \((12,16,11,5,2,7,2,1)\) and \((17,5,3,7,13,2,8,0,18,1)\), respectively. The degree-four map has 16 ramification points of multiplicity one and maps them to these 16 distinct geometric branch points.

The target therefore satisfies the hypotheses of the genus-five two-hop theorem even though the determinant quintic is singular. The correspondence then gives expected \(\widetilde O(q^{4/3})\) for this source family, improving the \(\widetilde O(q^{3/2})\) proved class-wide bound on genus-five nonhyperelliptic targets used by the older transfer. The exponent \(4/3\) was known heuristically for genus-five pencil methods. The result here supplies geometric certificates for this concrete application. [Genus-five graph proof](genus5-bridge.md) [pcc:unverified]

The [reproduction instructions](README.md#reproduce-the-fixture) check the frozen record using the repository Sage launcher.

The script checks the source and target polynomial data, the absolute-simplicity test, the exact ranks and Hessian, and the simply branched map. The recorded run covers these algebraic certificates. [pcc:unverified] [Certificate code](cubic_pencil_witness.py) · [Recorded certificate](cubic_pencil_witness.json)

### An open set of target parameters

The genus-five target hypotheses hold on a nonempty open of the six-dimensional space of omitted-root parameters for the fixed cubic \(h\) in §3. Take this parameter space over \(\mathbb Z[1/(2\cdot3\cdot17)]\), with the distinctness, unramified-fiber and denominator conditions of §3. The hyperelliptic polynomials are square-free over this open. The parity cover gives a smooth proper family of target curves, as can be checked étale-locally on the target line. At a paired branch value the two vanishing square roots have the local form \(\sqrt{(t-t_i)u_j}\) with \(u_j\) a unit. After extracting square roots of units étale-locally, the two sign flips give two simple double covers of the local line. At a cubic branch value the hyperelliptic functions are units and the cubic has one simple ramification, giving one double cover and two unramified sheets. Away from these divisors the parity cover is finite étale. These local normalizations are smooth over the parameter base.

At every point of \(W^1_4\) over the \(\mathbb F_{19}\) witness, the four local rank equations form a regular sequence on the smooth degree-four Picard fiber. The criterion for flatness of a quotient by a fiberwise regular sequence makes the relative \(W^1_4\) flat there. Properness of the relative Picard variety permits shrinking to a neighborhood of the witness on which the whole pencil locus is flat. Geometric integrality of its fibers is open for a flat, proper, finitely presented family. The absence of the smaller Brill–Noether loci is open by properness as well. The simply branched pencils form an open in the relative \(W^1_4\), and its image in the parameter base is open by flatness. This image contains the witness. [EGA IV₃, Théorème 12.2.4](https://www.numdam.org/articles/10.1007/BF02684343/)

The parameter base is integral, so the resulting nonempty open also has a nonempty characteristic-zero fiber. Spreading out gives a nonempty open for all sufficiently large prime characteristics. The target bound applies to that open. The separate absolute-simplicity certificate concerns the specified \(\mathbb F_{19}\) source.
