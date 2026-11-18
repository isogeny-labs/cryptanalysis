# Subexponential index calculus over prime fields

> Research note with written arguments and retrospective Sage fixtures. PCC standing is unverified. [pcc:unverified]

Write \(J=\operatorname{Jac}(C)(\mathbb F_p)\), \(N_0=p^g\), and \(L_X(\alpha,c)=\exp((c+o(1))(\log X)^\alpha(\log\log X)^{1-\alpha})\). The input is \(P,Q=sP\) and the prime \(r=\operatorname{ord}(P)\). The fixed-genus target is \(p^{o(1)}\), including setup, relation search and linear algebra. The growing-genus target \(N_0^{o(1)}\) has a different scale.

| Regime | Result |
| --- | --- |
| Genus 2, embedding degree one | An ordinary absolutely simple family with a rigorous \(L_p(1/2,O(1))\) solve through a pairing on subgroups of size \(p^{\Omega(1)}\) |
| Fixed genus, arbitrary prime-field Jacobians | A small random factor base covers almost every class at a sharp length scale. A subexponential inversion of these decompositions would complete the algorithm |
| Hyperelliptic genus \(g\to\infty\), rational ramification point | An explicit \(\exp(O(\log p+\sqrt{g\log p\log(2g)}))\) bound for a given prime-order subgroup without the ambient group order |

The [genus-five pencil result](https://github.com/isogeny-labs/cryptanalysis/pull/1757) gives a fixed positive exponent in \(p\) on a different family. Enge, Hess and Diem already prove subexponential bounds in growing-genus regimes. In particular, Diem's uniform fixed-cutoff bounds give \(N_0^{o(1)}\) for \(g\to\infty\). The calculation below gives a direct order-free subgroup proof and explicit joint parameters for the stated hyperelliptic inputs. [pcc:unverified] [Enge](https://doi.org/10.1090/S0025-5718-01-01363-1) · [Hess and Diem, background and §3.4](https://citeseerx.ist.psu.edu/document?doi=48e7ef85941e7ee5a60739b09d80bc6a924ce490&repid=rep1&type=pdf) · [Diem, published](https://doi.org/10.1090/S0025-5718-2010-02281-1)

## An absolutely simple genus-two family

For primes \(p\ge11\) with \(p\equiv2\pmod 3\), consider
\[
F_p(T)=T^4+T^3+(p-5)T^2+pT+p^2.
\]
The two real traces satisfy \(t^2+t-p-5=0\) and lie strictly between \(-2\sqrt p\) and \(2\sqrt p\). The discriminant \(4p+21\) is \(2\bmod 3\). Each root of \(F_p\) is nonreal and generates a field containing its real trace field of degree two, so \(F_p\) is irreducible. Its middle coefficient is prime to \(p\). The ordinary case of Honda–Tate realizes the polynomial as the Weil polynomial of an ordinary simple abelian surface. With \(a=1\) and \(b=p-5\), the identities \(a=0\), \(a^2=p+b\), \(a^2=2b\), and \(a^2=3b-3p\) all fail. Howe–Zhu's Theorem 6 therefore gives absolute simplicity. The coefficients avoid all ordinary simple exceptions in Howe–Nart–Ritzenthaler's Table 1.2, giving a genus-two Jacobian over \(\mathbb F_p\) in the isogeny class. [Howe–Zhu, Theorem 6](https://arxiv.org/abs/math/0002205) · [Howe–Nart–Ritzenthaler, Theorem 1.2, Table 1.2 and Appendix](https://www.numdam.org/item/10.5802/aif.2430.pdf)

The order is \(F_p(1)=(p-1)(p+3)\). For odd prime \(r\mid p-1\), the reduced Tate pairing
\[
e_r:J[r](\mathbb F_p)\times J/rJ\longrightarrow\mu_r(\mathbb F_p)
\]
is nondegenerate. Given a curve in the class, choose \(D\) with \(e_r(P,D)\ne1\). For sufficiently large \(p\), choose a rational point \(A\) uniformly and take \(D=[A-P_0]\). Each of the \(r-1\) nontrivial powers of \(D\mapsto e_r(P,D)\) has average \(O(p^{-1/2})\) on these point differences by the unramified character estimate below. Orthogonality gives \(\Pr[e_r(P,D)=1]\le 1/r+O(p^{-1/2})\). At fixed genus the pairing can be evaluated in time polynomial in \(\log p\) by divisor arithmetic and a Miller chain. Since \(e_r(Q,D)=e_r(P,D)^s\), prime-field index calculus gives expected \(L_p(1/2,O(1))\) total time including precomputation. Verify the result in the source Jacobian. [Frey–Rück](https://doi.org/10.1090/S0025-5718-1994-1218343-6) · [Pomerance, rigorous prime-field index calculus](https://math.dartmouth.edu/~carlp/disclog.pdf#page=11)

There are infinitely many parameters with \(r\ge p^{1/L-o(1)}\) for an absolute constant \(L\). For each prime \(r\ge5\), take the least prime in the reduced progression \(p\equiv1\pmod r\), \(p\equiv2\pmod3\). Linnik's theorem bounds it by \(O((3r)^L)\). Thus the algorithm is subexponential in subgroup size too. This specifies isogeny classes and applies when a curve and subgroup are supplied. Efficient construction of curve equations across the family remains open. The pairing reduction itself is classical. [Linnik bound, Heath-Brown](https://doi.org/10.1112/plms/s3-64.2.265)

### Exact prime-field witness

For \(C:y^2=x^5+16x^4+20x^3+14x^2+12x+4\) over \(\mathbb F_{29}\), the point counts over \(\mathbb F_{29}\) and \(\mathbb F_{29^2}\) are 31 and 889. They give \(F_{29}(T)=T^4+T^3+24T^2+29T+841\) and \(\#J=896\). For \(r=7\) the witness uses the Mumford generator \((x^2+3x+26,17x+7)\) and \(D=[(0,2)-(0,27)]\). Its reduced pairing is \(23\) of order 7. The target pairs to \(16\), and finite-field index calculus with base \(2,3,5\) gives exponent 3. The script checks all six nonzero multiples for bilinearity and verifies the recovered exponent on \(J\). This run measures correctness on one small input. [pcc:unverified] [Sage script](frey_ruck_witness.py) · [Exact output](frey_ruck_witness.txt)

## A fixed-genus decomposition target

Fix \(g\ge2\). Choose a rational base point \(P_0\) and \(B\) independent uniform rational points, with \(\log B=o(\log p)\) and \(\log B/\log\log p\to\infty\). Let \(\mu\) be the empirical distribution of the classes \([A-P_0]\). A bounded-degree map to \(\mathbb P^1\) permits uniform point sampling in expected time polynomial in \(\log p\). Try a uniform target fiber and sample from its rational points with acceptance proportional to its size.

For any nontrivial character \(\chi\) of \(J\), the unramified character sum on the rational points has magnitude at most \((2g-2)\sqrt p\). Hoeffding bounds on the real and imaginary parts of the empirical coefficient and a union bound over \(\#J=p^{g+o(1)}\) characters give, with probability \(1-o(1)\) over the base,
\[
\max_{\chi\ne1} |\widehat\mu(\chi)|=O_g\left(\sqrt{\frac{\log p}{B}}\right).
\]
For \(m=\lceil(g+\varepsilon)\log p/\log B\rceil\) and fixed \(\varepsilon>0\), Plancherel and Cauchy–Schwarz give
\[
\|\mu^{*m}-U_J\|_{\mathrm{TV}}
   \le\tfrac12\sqrt{\#J}\max_{\chi\ne1}|\widehat\mu(\chi)|^m
   \le p^{-\varepsilon/2+o(1)}.
\]
Repeated sampled labels in one sum have probability \(O(m^2/B)\), and repeated points in the base have probability \(O(B^2/p)\). Almost every class is therefore a sum of \(m\) distinct sampled points. The \(B^m\) upper bound on reachable classes rules out positive-density coverage at \(m\le(g-\varepsilon)\log p/\log B\). This gives a sharp leading-order threshold. [Farashahi, Fouque, Shparlinski and Tibouchi, §4](https://www.normalesup.org/~tibouchi/papers/welldistributed.pdf)

### The inversion problem

Given \(Z\in J\), use the degree-\(m\) line bundle \(Z+mP_0\). Eventually \(m\ge2g-1\), so its space of sections has dimension \(m+1-g\). Evaluate the sections at the \(B\) distinct base points using local trivializations. A nonzero section has \(m\) geometric zeros counting multiplicity. Its evaluation word has weight \(B-m\) exactly when it gives \(m\) distinct rational zeros in the base. Their classes sum to \(Z\). Thus inversion reduces to finding a word that attains the evaluation code's designed distance. For \(B=L_p(1/2,1)\) the target length is approximately \((g+\varepsilon)\sqrt{\log p/\log\log p}\). Subset enumeration at this threshold has \(p^{\Theta(1)}\) cost. Uniform section sampling also fails at this scale. There are \((p^{m+1-g}-1)/(p-1)\) projective sections and at most \(\binom{B}{m}\) sections whose zeros are \(m\) distinct base points. The success probability is at most \(p^{g-m+o(m)}\).

For imaginary hyperelliptic models there is also a compact encoding of this search. Generate point labels from \(k\)-wise independent \(x\)-coordinates and independent \(k\)-wise sign bits, using degree-\((k-1)\) polynomial evaluations with \(k\) an even integer of order \(\log p\). Reject nonsquare fibers and one of the two sign bits for a zero root, so every affine point has equal acceptance probability. The \(k\)-th moment of each centered real or imaginary character sum agrees with the independent case and is at most \((O(k)B)^{k/2}\). Applying Markov's inequality and a union bound at a sufficiently large multiple of \(\sqrt{kB}\) gives the same Fourier bound for the accepted list, whose size is concentrated around \(B/2\). Its lookup and Abel–Jacobi sum have circuit size polynomial in \(\log p\). A solving-degree bound \(o(\log p/\log\log p)\) for a complete Macaulay method on a polynomial-size bounded-degree circuit encoding would suffice for a \(p^{o(1)}\) inversion. Establishing this bound, or finding another subexponential inverter, remains open.

The Sage check used an 11-point list and 12 target classes on the \(\mathbb F_{29}\) curve. It discarded points in the support of the target Mumford polynomial when evaluating the sections as fractions. The rank criterion and direct Jacobian addition agreed on all 3,906 degree-five subsets tested, including 11 decompositions. The run used exhaustive subset enumeration. [Code check](subexp_code_check.py) · [Recorded output](subexp_code_check.json)

### End-to-end reduction from inversion

Sample a mask \(U\sim\mu^{*m}\) with known coefficient vector \(u\in\mathbb Z^B\). Draw \(\alpha,\beta\) independently and uniformly modulo \(r\), and ask the inverter to represent \(R=\alpha P+\beta Q+U\). For every fixed \(\alpha,\beta\) the input law is exponentially close to uniform in \(\log p\). An inverter succeeding on a \(p^{-o(1)}\) fraction of uniform inputs retains that rate up to negligible relative loss. For each output \(v\), check its group identity and keep \(\rho=v-u\). With \(B+1\) accepted columns, exact rational elimination gives a nonzero integer kernel vector \(\lambda\). Divide out its coordinate gcd so it is primitive and \(\lambda\not\equiv0\bmod r\). This exactly cancels the factor-base classes, including when \(P\in rJ\), without using the ambient group order.

The input, acceptance and matrix depend on \(u\), \(\alpha+s\beta\) and inverter randomness. The hidden \(\beta\)'s remain uniform and independent conditional on all that data. Thus \(\langle\lambda,\beta\rangle\ne0\) with probability \(1-1/r\). Recover \(s=-\langle\lambda,\alpha\rangle/\langle\lambda,\beta\rangle\bmod r\) and check it on \(J\). Linear algebra and verification cost \(B^{O(1)}\operatorname{poly}(\log p)\). A \(p^{o(1)}\) inverter with \(p^{-o(1)}\) success would therefore yield a full subexponential solve. This requires inversion on a typical constructed base, or on a constant fraction of bases with a bounded-restart policy. [Classical relation framework, Enge–Gaudry](https://doi.org/10.4064/aa102-1-6)

### Limits of uniform sampling and of a class-wide claim

- **Uniform reduced-divisor trials.** On an imaginary hyperelliptic model the number of classes whose reduced representative contains any fixed place of degree \(h\ge1\) is \(O_g(p^{g-h})\), by the effective-divisor count below. The same bound holds for a label that identifies conjugate places. If each trial conditional on its history is uniform on any subset of \(p^{g-o(1)}\) classes, the chance that any place repeats in \(T\) trials is \(O_g(T^2p^{-1+o(1)})\). Condition on the at most \(gT\) exposed labels and apply the fixed-place bound to the next trial. The probability of drawing the empty divisor in \(T=p^{o(1)}\) trials is negligible as well. With high probability the nonempty rows have disjoint supports and cannot cancel, even if one promotes an observed place to the base. The calculation applies to independent uniform sampling and the stated conditional distributions. Deliberately correlated sampling and long-sum inversion remain open.
- **A class-wide fixed-genus solver includes elliptic DLP.** For an elliptic curve \(E:y^2=f(x)\) with squarefree cubic \(f\), the genus-two curve \(y^2=f(t^2+c)\) has a degree-two map to \(E\) whenever \(f(c)\ne0\) in odd characteristic. Pushforward after pullback is multiplication by two. More generally fix \(g\ge2\), take \(d=\lceil(g+1)/2\rceil\) and \(k=2g+2-3d\), so \(0\le k\le d\) and \(k\equiv d\pmod2\). Choose a degree-\(d\) rational map \(h\) with \(k\) odd poles. Use \(h(t)=t^d\) if \(k=0\), or the reciprocal of a polynomial with \(k\) distinct rational roots of multiplicities \(d-k+1,1,\ldots,1\). For \(p\) sufficiently large relative to \(g\), try \(O_g(1)\) shifts \(c\) to make \(h+c\) unramified above the three roots of \(f\). Each geometric critical value forbids at most three shifts. The normalized pullback has \(3d+k=2g+2\) hyperelliptic branch points and hence genus \(g\). It maps to \(E\) in degree \(d\), and \(\pi_*\pi^*=[d]\). For every elliptic prime-order subgroup of order exceeding \(d\), this gives an injective lift computable in time polynomial in \(\log p\). The implication applies to a solver that covers Jacobians with elliptic factors and elliptic-size subgroups.

## An order-free bound for growing hyperelliptic genus

Let \(y^2=f(x)\) be squarefree of degree \(2g+1\) over \(\mathbb F_p\) for odd prime \(p\), with unique point at infinity \(P_0\). Take
\[
d=\max\left\{\left\lceil\log_p(256(g+1)^2)\right\rceil,\
              \left\lceil\sqrt{g\log(4g)/\log p}\right\rceil\right\}.
\]
For large \(g\), uniformly in \(p\ge3\), \(d\le g\). Use all split and ramified prime places of degrees at most \(d\) as the factor base, keeping formal labels for distinct places. These \(M=O(p^d)\) classes generate \(J\) by Enge's small-place generation bound. Enumerating monic irreducible base polynomials and factoring over their residue fields costs \(p^{O(d)}\operatorname{poly}(g,\log p)\). [Enge, Corollary 4.2](https://citeseerx.ist.psu.edu/document?doi=99abbb70b7c40cd361095a4743722f58b3664e39&repid=rep1&type=pdf)

Let \(S_d\) be the number of monic irreducibles of degree \(d\) at which \(f\) is nonzero and square in the residue field. The quadratic character sum on \(\mathbb F_{p^d}\) has magnitude at most \(2g p^{d/2}\), there are at most \(2g+1\) roots, and at most \(\sum_{i\le d/2}p^i\) elements have degree below \(d\). The definition of \(d\) gives \(S_d\ge p^d/(4d)\). Put \(k=\lfloor g/d\rfloor\). Choose \(k\) distinct such polynomials and one prime above each by a fixed sign convention. Each selection gives a distinct reduced divisor of degree \(kd\le g\). The number of distinct smooth classes is at least \(\binom{S_d}{k}\ge(p^d/(4g))^k\).

Every class has an effective degree-\(g\) representative relative to \(P_0\), by Riemann–Roch. The hyperelliptic map gives \(\#C(\mathbb F_{p^j})\le2(p^j+1)\) for all \(j\). The effective-divisor generating function is therefore bounded coefficientwise by \((1-z)^{-2}(1-pz)^{-2}\), by taking logarithms, bounding coefficients and exponentiating. In particular \(\#J\le(g+1)p^g/(1-1/p)^2\). The inverse uniform smoothness probability is at most \(\exp(O(d\log p+(g/d)\log(4g)))\).

Use the exact kernel step above with \(M+1\) accepted rows and a different mask. Choose the coefficient of each base class independently and uniformly in \([0,K)\), where \(K\) is the least power of two at least \(2M U^2\) and \(U=(p+1)^{2g}\) is an explicit Weil upper bound. Reduction of a coefficient modulo the order of its base class differs from uniform by at most \(U/K\) in total variation. Independence and generation make the mask statistically within \(MU/K\le1/(2U)\) of uniform on \(J\). The identity is smooth, so the actual acceptance probability is at least half the uniform probability. Coefficients have \(O(g\log p+\log M)\) bits. Exact linear algebra and the final source verification require neither the ambient order nor a subgroup complement.

Collection and polynomial-time exact linear algebra both fit
\[
\exp\bigl(O(d\log p+(g/d)\log(4g))\bigr)\operatorname{poly}(g,\log p)
 =\exp\bigl(O(\log p+\sqrt{g\log p\log(2g)})\bigr).
\]
This is \(N_0^{o(1)}\) along every sequence \(g\to\infty\) and \(L_{N_0}(1/2,O(1))\) when \(\log p=O(g\log g)\). The split-divisor lower bound and effective-divisor upper bound also give \(\log\#J=(1+o(1))\log N_0\) in this regime of growing genus.

## Reproduce the exact checks

The [reproduction instructions](README.md) give the checked Sage launcher commands and record the runtime used for the frozen outputs.
