# Both relative quartics have Klein-four Galois group and explicit Kummer rank two

The two monic irreducible quartic factors over `L = K(sqrt(2))`, where `K` is the frozen degree-18 field, each define a degree-four **Klein-four Galois extension of `L`**. Their fields have absolute degree 144. For each quartic, three exact cubic-resolvent roots lie in `L`; its polynomial discriminant has an exact square root in `L` from the preceding certificate. The three corresponding radicands have independent square classes of rank two, giving an explicit presentation

`F = L(sqrt(Delta_0), sqrt(Delta_1))`.

The exact coefficients of `Delta_0` and `Delta_1`, the third radicand, all three resolvent roots, and the square root of `Delta_0 Delta_1 Delta_2` are serialized in `kummer_result.json`. The ordering refers to the frozen factor rows in that file.

| Quartic side | Cubic-resolvent factor degrees over `L` | Individual radicands square in `L` | Pair products square in `L` | Triple product square in `L` | Galois group |
| --- | --- | --- | --- | --- | --- |
| left | `[1,1,1]` | none | none | yes, exact root retained | `V4` |
| right | `[1,1,1]` | none | none | yes, exact root retained | `V4` |

## Construction and proof

For a monic quartic `g(x) = x⁴ + a x³ + b x² + c x + d`, the frozen resolvent is

`R(y) = y³ - b y² + (a c - 4 d)y + (4 b d - a² d - c²)`.

Its roots in a splitting field are the three pair products `r₁r₂+r₃r₄`, `r₁r₃+r₂r₄`, and `r₁r₄+r₂r₃`. `run_sage.py` verifies exact quartic irreducibility, `disc(R)=disc(g)`, exact square-root witnesses for both discriminants, and three distinct linear factors of each resolvent. An irreducible quartic gives a transitive subgroup of `S₄`. Its square discriminant places that subgroup in `A₄`; three resolvent roots in `L` make it fix all three pair partitions, placing it in the kernel `V₄` of the partition action. Transitivity then forces the subgroup to equal `V₄`.

For a resolvent root `y_j`, define `Delta_j = a² - 4b + 4y_j`. If `S` and `T` are the two pair sums, `S+T=-a` and `ST=b-y_j`, so `Delta_j=(S-T)²` in the splitting field. `kummer_sage.py` tests the three exact square classes and their products. Each `Delta_j` is nonsquare in `L`, every pair product is nonsquare, and the triple product is an exact square. Hence any two radicands are independent in `L×/(L×)²`; their two square roots generate an extension of degree four. They already lie in the quartic splitting field, so that extension equals `F`. `replay_sage.py` independently reconstructs the serialized resolvent roots, radicands, and triple square-root witnesses and checks the exact identities. `audit.py` pins inputs and receipts and checks both `V4` and rank-two rows.

The checks took 44.816 seconds for resolvent factoring and 22.106 seconds for square-class testing on the recorded checked-Sage runtime. These times describe the algebraic diagnostic only.

## Proof map

`formal/CubicResolvent.lean` proves that all three pair products are roots of the stated cubic and proves `Delta_j=(S-T)²` for the first pairing. All four declarations build and have only standard Lean foundations in their `#print axioms` output (`formal/lean-check.txt`). The full Lean theorem remains open at the exact number-field and quartic encoding, the Galois action on four roots and pair partitions, and the degree-four Kummer extension/isomorphism bridge. The complete mathematical argument and its exact computational witnesses are retained above and in the JSON certificates.
