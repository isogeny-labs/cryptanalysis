# What a smooth principal ideal supplies in the ray-class kernel

## The exact sequence

Assume the ordinary curve has maximal CM order `O_K`, its rational group has prime order `r != p`, and `n = (pi - 1)` has norm `r`. Then `n` is a prime ideal and `O_K/n = F_r`. For the P-192 discriminant and for the `D=-19` control below, `O_K^* = {+1,-1}`. The standard ray-class exact sequence specializes to

```text
1 -> F_r^* / {+1,-1} -> Cl_n(O_K) -> Cl(O_K) -> 1.
```

[Sutherland, *18.785 Number Theory I*, Theorem 21.8](https://ocw.mit.edu/courses/18-785-number-theory-i-fall-2021/mit18_785f21_full_lec.pdf) gives the general exact sequence and the residue-ring identification. The displayed specialization follows because `n` is prime of norm `r` and the unit group here has order two. It identifies the information forgotten by projection from the pointed ray class to the unpointed CM class group; it does not provide an algorithm for assigning that information to an arbitrary finite-field point. [pcc:unverified]

For a principal ideal `(alpha)` coprime to `n`, the ray-kernel coordinate is the residue of `alpha` modulo `n`, up to sign. In particular, if `alpha = a + b*pi`, then

```text
alpha mod n = a + b mod r,
[alpha]P = [a + b]P  for P in E(F_p).
```

Thus a smooth-norm principal-ideal relation gives an explicit **known** ray residue and a known scalar action. Multiplying such relations combines known residues. To connect an arbitrary `Q = [d]G` to this list, an additional operation must determine which residue class sends the marked `G` to `Q`, or at least evaluate a nontrivial character of that class from `Q`'s coordinates. The exact sequence alone does neither. [pcc:unverified]

## A smooth noninteger control

Use the earlier `D=-19` curve `E/F_47: y^2 = x^3 + x + 38`, with `#E(F_47) = r = 61` and `G=(2,1)`. Its Frobenius trace is `t=-13`, so `O_K` has discriminant `-19` and class number one. Let `alpha=1+pi`. Then

```text
Norm(alpha) = 1 + t + p = 35 = 5 * 7,
alpha mod (pi-1) = 2 mod 61,
[alpha]G = [2]G,   x([2]G) = 3.
```

Both `5` and `7` split in `Q(sqrt(-19))`, so this is a genuine noninteger smooth-norm horizontal relation. Because `Cl(O_K)` is trivial, the relative ray group has order `(61-1)/2 = 30`. Its quadratic character gives `chi_61(2) = -1`, consistent with the [resolvent control](RAY_LABEL_CHARACTER_GATE.md). These checks exhibit a relation with a **known** scalar; choosing the control target `[2]G` does not show how to label a separately supplied `Q`. [pcc:unverified]

The integer checks are reproducible with `p=47`, `r=61`, `t=p+1-r`, `D=t*t-4*p`, `1+t+p=35`, `pow(2,(r-1)//2,r)=r-1`, and `kronecker_symbol(D,5)=kronecker_symbol(D,7)=1`. The group and class-number checks are in the [ray-class reduction audit](RAY_CLASS_REDUCTION_AUDIT.md). [pcc:unverified]

## What would move the boundary

The quadratic ray quotient is well-defined on x-coordinates here because `r = 1 mod 4`, so `chi_r(-1)=1`. An oriented evaluator of `chi_r(d)` from `(E,G,Q)` would be a point-dependent relation. The existing quadratic resolvent constructs exactly such a relation but needs `(r-1)/2` terms in its direct evaluation. The next candidate must specify a compact evaluation that uses CM data to beat that direct cost and the full same-target rho benchmark, including setup and any class-field or modular-function computation. This is a requirement on a proposed algorithm, not an assertion that the ray sequence prevents one. [pcc:unverified]

Producer claim: `PCC-20261124-01af6e` (unverified). [pcc:unverified]
