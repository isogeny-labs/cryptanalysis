# CT29 — F101 nondual degree-7 elliptic successor controls

**Scientific standing: [pcc:unverified].** Producer-local calculations only.

This is an independent bounded control for the CT24 continuation in [crypto PR #3877](https://github.com/isogeny-labs/crypto/pull/3877), without modifying the in-progress CT23 Richelot evaluator or the frozen consumer stack.

| C1 component | New nondual kernel h(x) | Normalized target (a',b') | Target j | Previous dual j |
|---|---|---|---|---|
| E109: (26,58) | x^3+75x^2+94x+99 | (59,27) | 47 | 12 |
| E113: (69,50) | x^3+40x^2+19x+53 | (23,7) | 89 | 58 |

Backtrack controls are h=x^3+58x^2+26x+58, target (78,72), j=12 for E109; h=x^3+45x^2+88x+29, target (99,68), j=58 for E113. The E113 forward kernel is a product of three linear factors over F101 (roots 61,53,48); never restrict the search to *irreducible* cubics.

## Exact CM cycle obstruction
Both ordinary Frobenius discriminants are fundamental:
- E109: D=-355. Reduced primitive positive binary forms: (1,1,89), (5,5,19), (7,-3,13), (7,3,13). Order of a prime ideal above 7 is 4; (27^2+355*5^2)/4=7^4; no earlier principal powers.
- E113: D=-283. Forms: (1,1,71), (7,-5,11), (7,5,11). Ideal order 3; (33^2+283)/4=7^3; no earlier principal powers.

Seven splits in both full CM rings. Thus the horizontal nonbacktracking j-cycles, starting at C1, are E109: **87,47,91,12,87** and E113: **92,89,58,92**. This yields a concrete next elliptic 7-hop but proves that repeated fixed-class horizontal steps recycle finitely many j-invariants. It is standard class-group/volcano theory, not a new general theorem.
