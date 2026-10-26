# Branch-orbit constraint at the dimension bound

This is a derived structural lemma. It uses standard facts about ordinary Jacobians and their geometric two-torsion. Its publication originality has not been established. In particular it does not replace the earlier sparse-Weil-polynomial criterion with a claimed new general descent principle.

The characteristic-two Frobenius/two-torsion machinery is explicitly discussed in Ballini–Lombardo–Verzobio, [*On the L-polynomials of curves over finite fields*](https://doi.org/10.1017/prm.2025.7), Section 5.2 and Remark 5.5. The orbit-forcing step below is a short consequence specialized to a simple odd-degree Weil restriction.

Borodin–May, [*On Weil Polynomials of Hyperelliptic Curves over Finite Fields of Characteristic 2*](https://arxiv.org/abs/2508.16886), Sections 2.1–2.4, also explicitly use branch-orbit partitions, two-rank and Frobenius point-count congruences, including arbitrary genus. This is close prior art for the constraint's method, not evidence for a new general construction family. Both primary PDFs are retained locally.

**Theorem.** Let $k=\mathbf F_q$ have characteristic two, let $N\ge3$ be odd, put $K=\mathbf F_{q^N}$, and let $E/K$ be ordinary. Suppose $W=\operatorname{Res}_{K/k}E$ is $k$-simple. If a hyperelliptic curve $C/k$ of genus $N$ admits a nonconstant map $C_K\to E$, then its hyperelliptic branch divisor has exactly two Frobenius orbits: one rational point and one orbit of length $N$.

Consequently $C$ has a model

$$
w^2+w=Ax+c+R(x)/H(x),
$$

where $A\in k^*$, $c\in k$, $H\in k[x]$ is monic irreducible of degree $N$, and $0\ne R\in k[x]$ has degree less than $N$. Thus searching this form is exhaustive for hyperelliptic realizations attaining the dimension bound, under the stated hypotheses.

**Proof.** Write $t=q^N+1-\#E(K)$. The map induces a nonzero homomorphism $J_C\to W$ by Weil-restriction adjunction. Simplicity and equality of dimensions make it an isogeny. Hence $J_C$ is ordinary and its Frobenius polynomial is

$$
P(T)=T^{2N}-tT^N+q^N.
$$

Ordinarity gives $t$ odd. The characteristic polynomial on the geometric étale two-torsion $J_C[2](\bar k)$ is therefore $T^N+1$: reduce $P$ modulo two and remove the $T^N$ factor belonging to the connected part.

An ordinary hyperelliptic curve of genus $N$ in characteristic two has $N+1$ geometric branch points, each with reduced Artin–Schreier pole order one. Let $B$ be this set. Its two-torsion is the augmentation representation

$$
J_C[2](\bar k)\simeq
\ker\bigl(\mathbf F_2^B\xrightarrow{\text{sum}}\mathbf F_2\bigr).
$$

For completeness, choose any $P_0\in B$. An even subset $S\subseteq B$ maps to the divisor class $\sum_{P\in S}P-|S|P_0$. Differences of branch points are two-torsion, so this is independent of $P_0$ and is Galois equivariant. It is injective: if such a divisor were principal, the function would be fixed by the hyperelliptic involution and hence come from the quotient line, whose valuations at branch points are even. A nonempty even subset gives an odd valuation at some branch point other than $P_0$. Both spaces have dimension $N$, so this is an isomorphism.

If the branch-orbit lengths are $e_1,\ldots,e_s$, the permutation characteristic polynomial consequently satisfies

$$
\prod_i(T^{e_i}+1)=(T+1)(T^N+1)
\quad\text{in }\mathbf F_2[T].
$$

Because $N$ is odd, there is a primitive $N$th root of unity in $\bar{\mathbf F}_2$. It is a root on the right, so some $e_i$ is divisible by $N$. Since $\sum e_i=N+1$ and $N\ge3$, that orbit has length $N$, leaving a single orbit of length one.

The hyperelliptic quotient is a rational curve over the finite field. Move the rational branch point to infinity. Reducing the Artin–Schreier equation leaves a nonzero linear polynomial part and simple poles at an irreducible degree-$N$ polynomial, giving the asserted model. $\square$

This is a necessary geometric constraint, not a sufficient test of vulnerability for an elliptic coefficient $b$. It assumes a simple restriction and genus exactly $N$; it does not constrain arbitrary higher-genus covers or nonhyperelliptic covers. Even when a Jacobian realization is proved, an efficient explicit correspondence and prime-subgroup preservation require further work.

The finite checks in `genus5_f4_branch_checks.sage.py` enumerate all branch partitions for eight odd values of $N$, including composite $N=9,15,21$. They supplement the proof; they are not its justification.

## Complete negative checks over F2 in degrees eleven and thirteen

**Computer-assisted proposition.** Let $N=11$ or $13$, let $K=\mathbf F_{2^N}$, and let $E/K$ be ordinary with $\operatorname{Res}_{K/\mathbf F_2}E$ simple. If a hyperelliptic curve $D/\mathbf F_2$ admits a nonconstant map $D_K\to E$, then $g(D)\ge N+1$.

The dimension argument already excludes $g(D)<N$. If equality held, the preceding branch-orbit theorem would give

$$
w^2+w=x+c+R/H,
\quad c\in\{0,1\},\quad H\text{ monic irreducible of degree }N,
\quad 0\ne R\in\mathbf F_2[x],\quad\deg R<N.
$$

The sparse Frobenius polynomial forces $\#D(\mathbf F_{2^j})=2^j+1$ for every $1\le j<N$, by Newton identities. The complete enumerations below find no such model. The substitution $x\mapsto x+1$ pairs the possible H freely: in odd degree it changes the next-to-leading coefficient. It maps R and c bijectively within the enumerated parameter set.

| N | Irreducible H | Representatives under translation | Normalized models, including both twists | Matches through degree N−1 |
| ---: | ---: | ---: | ---: | ---: |
| 11 | 186 | 93 | 380742 | 0 |
| 13 | 630 | 315 | 5160330 | 0 |

For N=11, two normalized models survive through extension degree nine and both fail degree ten. For N=13, two survive through degree ten and both fail degree eleven. No trace value or elliptic isogeny class has been selected in obtaining these negative results.

`binary_prime_spectral.py` enumerates the models and computes character sums using a Walsh transform. `binary_prime_direct.cpp` independently enumerates irreducible polynomials and computes the character sums directly, using a separate finite-field implementation without a Walsh transform. The complete candidate sets and the number surviving at every stage agree. The genus-five positive control recovers six normalized models with traces $\pm1,\pm3$, including the previously published target used earlier in this workspace. These are correctness controls, not new affected-curve claims.

This obstruction applies to **every hyperelliptic cover degree** under the stated hypotheses, beyond the particular GHS/gGHS construction. It does not exclude nonhyperelliptic targets of genus N, hyperelliptic targets of larger genus, or supply a cost lower bound. The branch-orbit machinery is prior work as cited above. Publication priority of this particular finite-field proposition is not established. It is a negative research result, not fulfillment of the user's request for a novel affected family.

Reproduce the checks with `bash theory/reproduce_binary_prime_spectral.sh`. Exact records are `binary_prime_genus{5,11,13}_{spectral,direct}.json`; the combined evidence is `binary_prime_status.json`. No new catalogue entries are added.
