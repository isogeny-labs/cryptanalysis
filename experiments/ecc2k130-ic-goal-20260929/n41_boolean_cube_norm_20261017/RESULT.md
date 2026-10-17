# Boolean selector-cube norm on the N41 public eliminant

The exact nine-selector-bit norm preserves the archived N41 public witness
and rejects two frozen zero-free blocks. Its symbolic ANF is **fully dense:
512 nonzero coefficients in each of three all-valid affine-flat triples**.
Constructing and eliminating one block uses **172,911–172,914 measured
`GF(2⁴¹)` multiplications**, compared with **38,896** for direct evaluation
of its 512 code triples. The first norm step alone requires **65,536**
coefficient-pair multiplications in this implementation. This is an exact
operation-count obstruction for the tested expanded-ANF route; the source
tensor's factored circuit and other representations remain separate design
choices.

## Target-conditioned source and method

The instance is `EC1N41Ckb1h7d5e80d3c4d0` over
`GF(2)[t]/(t⁴¹+t³+1)` with `y²+xy=x³+1`. The frozen
[all-valid affine-flat census](../n41_valid_affine_flat_target_20261017/RESULT.md)
contains eight three-dimensional flats of the canonical W8 source codes.
The [interpolated eliminant](../n41_first_product_interpolated_eliminant_20261017/RESULT.md)
has 213 `(q,r)` terms, with polynomial coefficients in the first product
`p`; it is conditioned on the archived public-relation residual after four
fixed signed source states. The panels were fixed in
[`protocol.json`](protocol.json) before measurement:

| Frozen tensor and flat indices | Code triples | Exact zero assignments | Norm result |
| --- | ---: | ---: | --- |
| Public witness, `(0,3,1)` | 512 | 1: masks `(153,215,64)` | zero |
| Public witness, `(0,0,0)` | 512 | 0 | nonzero |
| Negative residual, `(0,0,0)` | 512 | 0 | nonzero |

Each product `p,q,r` is affine in its flat's three selector bits. The
producer substitutes those three affine charts into the target-conditioned
tensor, reduces modulo `xᵢ²=xᵢ`, and obtains a 512-term field-valued ANF.
For a selected bit, write `F=F₀+xᵢF₁` and replace it by
`F₀²+F₀F₁`. Nine such steps yield the product over every source-valid code
triple, so a zero norm retains every actual root. The readable proof and
checked conditional Lean declarations are in the [proof map](PROOF_MAP.md).

## Frozen measurements and independent replay

The three panels used one checked-Sage worker with a 180-second alarm and
4-GiB observational RSS boundary. The [runtime receipt](sage_runtime_info.json)
was saved first. Both routes share the measured power-table precompute for
the exact same eight products in each slot. The comparison below starts
after that precompute and excludes the earlier target-conditioned tensor
interpolation. The host has no CPU isolation receipt; operation counts and
exact values are the main diagnostics.

| Panel | Direct evaluation | ANF construction + norm | Direct field multiplications | Symbolic field multiplications | Initial ANF terms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Witness `(0,3,1)` | 11.786 ms | 143.670 ms | 38,896 | 172,911 | 512 |
| Witness `(0,0,0)` | 8.837 ms | 111.286 ms | 38,896 | 172,914 | 512 |
| Negative `(0,0,0)` | 8.672 ms | 203.721 ms | 38,896 | 172,914 | 512 |

The shared source-and-tensor loading took 119.264 ms; each block's
power-table preparation, direct route, ANF construction, norm, and value
audit have separate nanosecond fields in [`result.json`](result.json).
The producer's peak self RSS was 256,147,456 bytes. It compared all 512
direct values per block with the archived grid, evaluated its ANF at all
512 bit assignments, and checked the final norm against the direct product
of those values. The independent [integer-field audit](audit_result.json)
read the frozen grids, recomputed all 512 ANF coefficients, replayed every
norm stage with separate shift-and-XOR multiplication, and matched the three
zero sets and norm values. Its [protocol](audit_protocol.json) hashes the
producer result and source grids before the run. Both raw stderr files are
empty.

The witness zero is position 314 in the producer's `p`-outer, `r`-inner
enumeration, corresponding to flat-local indices `(4,7,2)` and source masks
`(153,215,64)`. The prior checked group-law witness binds this zero to the
ordinary N41 public point. This component retains `candidate_id: null`.

## Next design decision

For every tested cube, the expanded ANF fills all 512 positions before
elimination. Its first coefficient-pair product already exceeds the direct
route's complete field-multiplication count. This ends the expanded
Boolean-coefficient norm as an early-rejection candidate for these source
flats. The next N41 test should keep the target-conditioned six-pair
determinant in a **factored source-code circuit**, derive a nonlinear
whole-family rejection without expanding its truth table or ANF, and charge
its setup plus all tested families against the direct point-join control.
An independently replayed unpinned N41 relation and a source-bound N131
one-worker/600-second/4-GiB projection remain the promotion gates before
another frozen N131 public-point run.
