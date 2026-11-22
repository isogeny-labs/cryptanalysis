# N41 nonlinear sign-norm box certificate

The product of the 32 determinant values over the five sign bits gives one field element per root-choice tuple. A binary linear functional that takes value one on every such product excludes every sign assignment in the box. On eight frozen ordinary N41 boxes, each containing 32 root choices, one functional certified all 1,024 assignments. A constructed relation was retained as a positive control: its product vanished, so the same exclusion test did not suppress the witness.

For a fixed five-root tuple \(r\), write \(D(r,s)\) for the six-point \(L(6O)\) determinant with sign vector \(s\in\mathbb F_2^5\), and \(N(r)=\prod_s D(r,s)\). If a binary linear functional \(\lambda\) satisfies \(\lambda(N(r))=1\), then \(N(r)\neq0\), hence every factor is nonzero. The eight ordinary boxes each had 32 nonzero norms of binary rank 32 and admitted a common mask. The constructed box had one zero at root/sign pair `[0,30]`, rank 31 among its norms, and no common mask.

The checked-Sage audit recomputed 288 products and 9,216 determinant factors. Its monitored parent wall time was 4.866 s, with 262,209,536 B sampled combined peak RSS, under the frozen 120 s and 4 GiB caps. [The terminal verifier](verify_terminal.py) binds the result, audit, source scripts, and Lean output by SHA-256. The immutable run retains the initial version in which positive-row rank metadata was recorded before the inconsistent system finished; `result_v2.json` computes full rank. Both versions agree on the products and decisions.

This construction compresses a finite rejection record. Its measured value for search depends on obtaining a certificate before enumerating the root tuples; that cost question is tested on N131 in the linked transfer experiment.

`candidate_id: null` because this experiment is a point-decomposition component, not a complete IC pipeline.
