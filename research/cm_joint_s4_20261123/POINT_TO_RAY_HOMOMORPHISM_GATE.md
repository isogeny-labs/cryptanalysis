# Additive point-to-class bridges on P-192

## Exact order obstruction

Let `E(F_p)=<G>` have prime order `r`, let `K=Q(pi)` have maximal
imaginary-quadratic order `O_K`, and put `n=(pi-1)`. The norm of `n`
is `r`. When `O_K^*={+1,-1}`, the standard ray-class exact sequence
gives

```text
|Cl_n(O_K)| = h_K * (r-1)/2,
|Cl(O_K)|   = h_K.
```

If `r` does not divide `h_K`, neither target group has `r`-torsion.
Consequently **every group homomorphism** from the additive group
`E(F_p)` to either `Cl(O_K)` or `Cl_n(O_K)` is constant at the identity.
Indeed, the image of `G` must have order dividing both `r` and the
target-group order. This also rules out a map satisfying
`F([a]P)=F(P)^a` for every integer `a`, even if additivity between
different points was not separately assumed. [pcc:unverified]

For the exact P-192 parameters below, `r` does not divide `h_K`
without computing the class group. Write `q=|D_K|`, where the
fundamental discriminant is `D_K=t^2-4p`. The imaginary-quadratic
[class-number formula](https://math.mit.edu/~drew/sutherland-phd.pdf)
for `D_K<-4` gives

```text
h_K = sqrt(q)/pi * L(1,chi_D).
```

The primitive nonprincipal character `chi_D` has period `q` and zero
sum over one period. The first `q` terms of its Dirichlet series have
absolute sum at most `H_q < log(q)+1`. Partial sums starting after a
whole period have absolute value at most `q`; summation by parts
bounds the remaining tail by `q/(q+1)<1`. Thus
`0<L(1,chi_D)<log(q)+2`. The exact parameters give `q<2^194` and
`r>2^104`. Since `log(2)<1` and `pi>3`,

```text
h_K < (2^97/3)*196 < 2^104 < r.
```

This loose strict bound is enough for the group-order argument; it
does not estimate the actual class number. The ray exact sequence is
the one recorded in the [ray-kernel audit](RAY_KERNEL_RESIDUE_GATE.md).
[pcc:unverified]

Reproduce the integer checks without a class-group computation:

```sh
python3 - <<'PY'
p=6277101735386680763835789423207666416083908700390324961279
r=6277101735386680763835789423176059013767194773182842284081
t=p+1-r
D=t*t-4*p
q=-D
assert D < -4 and q < 2**194
assert 196*2**97 < 3*2**104 < 3*r
print({'trace':t, 'discriminant':D, 'q_bits':q.bit_length(),
       'r_bits':r.bit_length(), 'certified_h_upper_power':104})
PY
```

## What remains possible

The desired assignment `[d]G -> d mod {+1,-1}` lives on the
nonidentity points modulo sign and takes values in the **multiplicative**
group `F_r^*/{+1,-1}`. It is not a homomorphism from point addition:
the identity point has no nonzero label, and addition of point labels
corresponds to addition modulo `r`, not multiplication of ray residues.
The obstruction above therefore does not rule out a nonlinear,
coordinate-dependent orientation map or a point-decomposition
relation. It does rule out obtaining such a map merely by asking an
additive point-to-ideal-class construction to preserve the group law.
[pcc:unverified]

A successor must state the nonadditive operation that reads the
coordinates of a supplied `Q`, produce a verifiable relation in its
unknown scalar, and demonstrate an isogeny-specific gain in relation
yield or full cost against the same-target rho baseline. [pcc:unverified]
