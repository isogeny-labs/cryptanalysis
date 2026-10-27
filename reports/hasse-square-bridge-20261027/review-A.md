# Blind review A: Hasse-square natural-number bridge

## Scope and verdict

The stated implication **holds** for all `p,r,n,m,k,l : Nat`. The strict threshold `16*p < r^2` is sharp for the unrestricted natural-number statement: replacing `<` by `≤` **breaks** it at the supplied equality example. The premises are satisfiable with every variable positive. Applying the statement to any particular elliptic curve remains **inconclusive** until the curve-specific facts listed below are supplied.

## Independent derivation

Put `c = p+1`, `a = delta(n,c)`, `b = delta(m,c)`, and `d = delta(n,m)`. The absolute-difference triangle inequality gives `d ≤ a+b`; this holds also when either natural subtraction would truncate, because `delta` selects the nonnegative difference by cases. Hence

```text
d^2 ≤ (a+b)^2 ≤ 2(a^2+b^2) ≤ 2(4p+4p) = 16p.
```

The middle inequality is `2ab ≤ a^2+b^2`. From `16p < r^2`, we get `r>0`. If `n≠m`, the equations `n=k*r` and `m=l*r` make `d` a positive multiple of `r`: for example, if `n>m`, then `k>l` and `d=(k-l)*r≥r`; the other order is symmetric. Thus `r^2≤d^2≤16p<r^2`, a contradiction. Therefore `n=m`. No primality or positivity assumption on `p` is used.

## Satisfiability and zero cases

* All six variables can be positive: `p=17`, `r=17`, `n=m=17`, `k=l=1`. Here `delta(17,18)^2=1≤68` and `16p=272<289=r^2`.
* `r=0` is impossible, since the strict threshold would say `16p<0`.
* If `p=0`, both square bounds force `n=m=1`. Since `r>0` and both are multiples of `r`, necessarily `r=1` and `k=l=1`. This gives a valid arithmetic example with zero `p`.
* If `n=0` or `m=0`, its Hasse-square bound is `(p+1)^2≤4p`, equivalent to `(p-1)^2≤0`; hence `p=1`. Uniqueness then forces `n=m=0`, and `r>0` forces `k=l=0`. Any `r≥5` works; for instance `p=1,r=5,n=m=0,k=l=0`. Conversely, a zero `k` or `l` is equivalent to a zero corresponding `n` or `m`, since `r>0`.

## Threshold and premise controls

Under the weakened threshold `16p≤r^2`, take `p=1,r=4,n=0,m=4,k=0,l=1`. Both values are multiples of `4`; their distances from `p+1=2` are `2`, so both squares equal `4=4p`; and `16p=r^2=16`. Yet `n≠m`. Thus strictness is necessary for the unrestricted Nat theorem.

The equality failure is confined to this arithmetic boundary, up to swapping `n,m`: if distinct multiples existed under `16p≤r^2`, every inequality in the proof would be equality. Thus `d=r`, `r^2=16p`, `a=b=2√p`, and the two values would be the opposite Hasse endpoints. Writing `r=4s`, `p=s^2` gives endpoints `(s-1)^2` and `(s+1)^2`. Divisibility of the lower endpoint by `r` implies `s | (s-1)^2`, hence `s|1`, so `s=1`. Therefore `p=1,r=4` and the endpoints are `0,4`. In particular, for `p≥2` the weak threshold still suffices; if `p` is prime, equality `16p=r^2` is impossible already because a prime is not a square.

The other premises are independently material. Each line below keeps the strict threshold and every premise except the one named:

| Omitted premise | Assignment `(p,r,n,m,k,l)` | Reason conclusion fails |
|---|---|---|
| `n=k*r` | `(1,5,1,0,0,0)` | Both square bounds hold, but `1≠0`. |
| `m=l*r` | `(1,5,0,1,0,0)` | Symmetric case. |
| Bound on `n` | `(1,5,5,0,1,0)` | `delta(5,2)^2=9>4`, while `m` satisfies its bound. |
| Bound on `m` | `(1,5,0,5,0,1)` | Symmetric case. |
| Strict threshold | `(1,4,0,4,0,1)` | Equality-bound counterexample above. |

These examples are arithmetic controls; they do not claim realization as elliptic-curve orders.

## Obligations for a concrete elliptic-curve use

1. Specify a nonsingular elliptic curve (or two curves, if two orders are being compared) over the same finite field of size `p`, with `p` prime for `F_p`. For an extension field, use its size `q` in every occurrence of `p` instead. A field of size `1` does not exist.
2. Identify `n` and `m` as the proposed finite rational-point counts and prove **each** Hasse-square inequality relative to that same field size: `delta(n,p+1)^2≤4p` and `delta(m,p+1)^2≤4p`. If an order is represented by a trace, prove the conversion to this natural-number form.
3. Prove the common divisibility facts independently: exhibit natural `k,l` with `n=k*r` and `m=l*r`. An actual subgroup or point of exact order `r` in each relevant group, together with Lagrange's theorem, can provide these facts. Divisibility of only one candidate is insufficient.
4. Establish the numerical threshold `16p<r^2` (or, with prime `p`, `16p≤r^2` and the impossibility of equality). If `r` is introduced as a point or subgroup order, identify that integer with the same `r` used in both divisibility statements.

Only after these obligations hold does the arithmetic bridge yield `n=m`. The abstract implication alone neither verifies a candidate curve order nor supplies the subgroup/divisibility evidence.

## Provenance and review protocol

* Actual task material read: `/tmp/cryptanalysis-hasse-square-20261027/reports/hasse-square-bridge-20261027/blind-brief.md` only. No public Nat/Lean documentation was needed.
* Sibling access: none. I did not read producer source, proof map, review plan, receipts, repository history, sibling output, or parent conversation.
* Owned joint: independent mathematical implication, satisfiability and zero controls, threshold and missing-premise controls, and concrete elliptic-curve transfer obligations. I did not assess a Lean implementation or any producer artifact.
* Deviations: none. No repository edits or heavy build were performed. This report is the sole written review artifact.
