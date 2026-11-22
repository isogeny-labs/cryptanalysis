# Priority audit for the degree-eight and degree-nine genus-five maps

The five coefficient families and their explicit low-degree maps are new to the local catalogue. Publication originality is not established. The verified mathematical claims are the coefficient conditions, exact maps, genus and simplicity proofs, complete subgroup transfers, and canonical-GHS baseline comparison.

## Novelty gate: comparison before further catalogue expansion

The user's objective is a previously unrecognized affected family or identifying criterion. Adding explicit examples before resolving the closest prior classifications does not establish that objective. No further examples should be presented as novelty candidates solely because they differ from canonical GHS or from existing catalogue rows.

There are three different priority questions: whether the source classes were already known to admit suitable covers, whether these particular low-degree maps were already known, and whether the recognition criterion or proof adds something to an earlier classification. A new explicit map to an already known affected source is not by itself a newly identified vulnerable family. Literal searches for the five minimal polynomials are insufficient: the comparison must allow coordinate changes, Frobenius, quadratic twists, isomorphisms and isogeny-assisted constructions.

The five entries in the theorem are five finite coefficient orbits in F1024. Their propagation to larger ambient fields uses base extension and simultaneous twisting. It is not a new family with full ambient coefficient degree tending to infinity, and the standard propagation step has no novelty claim.

### Direct check of Hess's broader split-pole construction

Re-read Hess (2004), Theorem 12, on 21 October 2026. This theorem already treats presentations

$$
w^2+w=\gamma/x+\alpha+\beta x,\qquad b=(\gamma\beta)^2,
$$

with both nonzero coefficients free, rather than only canonical GHS. For a degree-five extension K/k, the nonzero coefficient annihilators under Frobenius are $T+1$, $\Phi_5(T)=T^4+T^3+T^2+T+1$, or their product. The reason is that $\Phi_5$ is irreducible over F2. When the compositum has exact constant field K, put $m=\deg\operatorname{lcm}(m_\gamma,m_\beta)$. Hess's formula is

$$
g=2^m-2^{m-\deg m_\gamma}-2^{m-\deg m_\beta}+1.
$$

This gives the complete table of possibilities for the stated presentations:

| $\deg m_\gamma$ | $\deg m_\beta$ | m | g |
| ---: | ---: | ---: | ---: |
| 1 | 1 | 1 | 1 |
| 1 | 4 | 5 | 15 |
| 1 | 5 | 5 | 16 |
| 4 | 4 | 4 | 15 |
| 4 | 5 | 5 | 30 |
| 5 | 5 | 5 | 31 |

The first row has $b\in k$ and cannot contain our full-relative-degree-five coefficients. Thus the five genus-five maps are outside this **specific construction**, whose genus is at least fifteen here. This is a deduction from a published formula, not a new theorem-priority claim. It does not classify arbitrary covers, all nonsplit presentations, or useful quotients of a larger compositum. Hess discusses possible useful subfields in Section 8.3 and higher-index rational presentations in Section 8.4; excluding his Section 5 output is not the same as excluding those possibilities.

Primary reference: [Hess, *Generalising the GHS Attack on the Elliptic Curve Discrete Logarithm Problem*, LMS J. Comput. Math. 7 (2004), Theorem 12 and Section 8](https://doi.org/10.1112/S146115700000108X). The retained full text is `../sources/hess-generalising-2004.pdf`.

The exact-constant and descent requirements must also be imposed. Hess's Theorem 11 requires absolute trace zero of $\alpha$ or relative trace zero of at least one of $\gamma,\beta$. If absolute trace($\alpha$)=1 and both coefficient annihilators are $\Phi_5$, the compositum instead acquires quadratic constants. If both relative traces are nonzero and trace($\alpha$)=1, the required Frobenius lift fails. Thus a formal genus calculation is not a valid descent certificate for that twist.

The independent binary-field script `check_hess_prior_scope.py` exhausts all 1023 rescalings for each of the 220 source models, or **225,060 coefficient presentations**, and applies both conditions. The complete-class valid minima are:

| Seed b | Selected elliptic trace | Minimum valid genus in the published split-pole construction |
| ---: | ---: | ---: |
| 47 | -25 | 15 |
| 166 | 51 | 30 |
| 411 | -11 | 15 |
| 636 | -1 | 15 |
| 434 | -53 | 30 |

All five selected source classes therefore already admit a descent within this published framework. The potential research contribution is a lower-genus realization, its explicit maps, or a sharper recognition criterion; this is not evidence of their first-ever connection with Weil descent. The earlier claim of canonical genus fifteen or sixteen must be read as a **formal compositum** comparison. The updated catalogue marks whether its Frobenius lift exists and records the valid split-pole minimum. The saved raw character-count evidence is retained, with its corrected interpretation here.

### Scope of the characteristic-two classification comparison

Murai's public 2022 summary, Sections 2 and 3.2, explicitly constructs the compositum of conjugate quadratic extensions and imposes $g(C)=d g(C_0)$. Its Section 4.3 restricts the stated odd-degree ordinary construction to the appropriate $d=2^n-1$ cases. Its claimed completeness is within that covering setup. Our older Mersenne constructions were included in this framework, as the earlier inclusion calculation establishes. This does not automatically classify the new degree-eight/nine maps. Conversely, a different map degree alone does not prove that the **source curve** was previously unrecognized: it might admit another earlier map.

Tomaru's public 2024 summary likewise uses $(2,\ldots,2)$ composita and explicitly lists the case $g(C_0)=1,d=5,n=4$ without genus equality. Its displayed examples omit the detailed case-(b) classification. It must not be represented as a classification of every possible cover from a genus-five curve.

The primary 2006/347 Momose–Chao ePrint abstract was checked again. Its declared scope is Weil restrictions obtained by $(2,\ldots,2)$ coverings. The full PDF is still unread here. A ResearchGate record bearing that title instead displays an odd-characteristic cubic-extension paper from 2013; that mismatched upload is not evidence that the 2006 paper was read. The restricted Murai thesis is also unread. These limits must remain visible in any priority assessment.

Primary sources: [Murai public summary](https://chuo-u.repo.nii.ac.jp/record/16687/files/nenpou20N8100018H.pdf), [Tomaru public summary](https://chuo-u.repo.nii.ac.jp/record/2001304/files/nenpou22N8100017F.pdf), and [Momose–Chao 2006/347 metadata](https://eprint.iacr.org/2006/347).

**Gate outcome, 21 October 2026:** the exact maps and applicability proofs survive this comparison; publication novelty of a source family, map, or identifying criterion does not yet pass. The next research work is the remaining classification comparison, not more coefficient enumeration. The unresolved nonquadratic and useful-quotient possibilities cannot be excluded by the split-pole table above.

A further cyclic-three quotient idea was screened before constructing new examples. Its quadratic elliptic factors have split-pole coefficients $\gamma=\sqrt B\,\zeta$ and $\beta=A\zeta^2$, with $A,B\in k^*$ and $\zeta$ in the irreducible four-dimensional Frobenius module for a degree-five extension. Both coefficients are therefore annihilated by $\Phi_5(\sigma)$, and the trace-zero sources already fall in Hess's genus-fifteen family. A smaller quotient might improve a realization, but it does not pass the user's requirement of a newly identified source family. No new catalogue rows were generated from this idea.

The subsequent degree-eleven/thirteen search is recorded in [the branch-orbit proof](HYPERELLIPTIC_BRANCH_ORBIT.md). Targeted prior-art screening found the broader Artin–Schreier descent machinery in Hess and in Ballet–Rolland, [arXiv:2505.21656](https://arxiv.org/abs/2505.21656), and asymptotic gGHS bounds in Karabina–Menezes–Pomerance–Shparlinski, [*On the asymptotic effectiveness of Weil descent attacks*](https://math.dartmouth.edu/~carlp/WeilDescent-Product.pdf). Only the introductions and declared scopes of these two additional papers were checked here; no claim to have audited every theorem is made. The finite enumeration method is not claimed as new. The negative genus-floor checks add no candidate family and do not satisfy the user's positive-family objective.

The general method of mapping an elliptic DLP through a curve in its Weil restriction is prior work. Frey–Gangl, Galbraith–Smart, Hess's generalized GHS work, Diem–Scholten, and later covering classifications must be credited. The earlier [audit](GENUS5_PRIOR_ART.md) and [classification comparison](LITERATURE_COMPARISON.md) remain relevant. In particular, an odd-degree cover or a sparse Weil polynomial alone is not a publication-novel result.

## A previously missing primary source is now read

The Diem–Scholten report *Cover Attacks: A report for the AREHCC project* (29 September 2003) was recovered from an archived copy of the authors' PDF. Its current author endpoint returned 404 and a secondary mirror returned 503. The retained file is `../sources/diem-scholten-cover-attacks-2003.pdf`; the URL, byte count and SHA256 are in `genus5_multipole_prior_art.json`.

Relevant sections read in full are 3.1, 3.3, 4 and 5:

- Section 3.1 gives the binary Frobenius-module rank constraint and states that the minimum genus for quadratic GHS descent in relative degree five is seven. This supports the limited baseline comparison; it does not establish novelty of our maps.
- Section 3.3 already discusses nonquadratic Galois presentations and isogeny-assisted descent. Neither idea is claimed as new here.
- Section 4's genus-five construction concerns genus-two trace-zero sources in a cubic extension. That displayed construction does not identify the ordinary binary degree-five-extension sources proved here.
- Section 5 proposes an L-polynomial approach and explains that making the elliptic maps explicit is difficult. Its displayed Dickson/Mestre equations and general existence method are prior work. An explicit formula obtained after spectral filtering is a constructive result, but its priority requires further comparison.

Archive of the primary PDF: [2011 snapshot](https://web.archive.org/web/20110719105406id_/http://www.math.uni-leipzig.de/~diem/preprints/cover-attacks.pdf).

## What is concretely different from the earlier local results

The source coefficients have absolute degree ten over F2. The source traces $-25,51,-11,-1,-53$ lie outside the stated proper-subfield/twist-induced trace exclusion, so they are not the earlier F32 seed re-encoded in F1024. Their formal canonical compositum minima are fifteen or sixteen, while imposing the published split-pole descent conditions gives the fifteen/thirty comparison above. The new genus-five maps have degrees eight and nine, and direct target-Jacobian planted-log solves are verified. The degree-nine maps have odd degree and therefore are not the source projections of a quadratic GHS tower. This map-degree distinction alone does not establish a new source locus.

The general branch-orbit and two-torsion machinery used to reduce the search is also prior work; see Ballini–Lombardo–Verzobio (2025), Section 5.2, and Borodin–May (2025), Sections 2.1–2.4. The implementation uses rational interpolation and an exact Artin–Schreier coboundary test. No claim that these algebraic tools are themselves new is made.

Further screening on 20 October 2026 included Fan et al., [*Hyperelliptic Covers of Different Degree for Elliptic Curves* (2022)](https://doi.org/10.1155/2022/9833393), Sections 1.1–3.1. Its explicit constructions concern genus-two covers over quadratic extensions in an odd-characteristic setup; its Lemma 2 also states the prior simple-Jacobian/Weil-restriction principle. Those sections do not identify our exact binary degree-ten coefficients or maps. This limited comparison does not establish their absence from the full literature. The simultaneous-twist corollary uses a standard Artin–Schreier coordinate change and is not claimed as a new general principle.

Remaining priority work includes the useful-quotient and higher-index possibilities discussed by Hess, the full characteristic-two covering classifications, and later explicit elliptic quotient constructions. The restricted Murai thesis remains unread. Accordingly the catalogue label is **verified cover-attack applicability; publication priority unresolved**. The result establishes neither a newly discovered vulnerable field as a whole nor a cryptographic-size break.
