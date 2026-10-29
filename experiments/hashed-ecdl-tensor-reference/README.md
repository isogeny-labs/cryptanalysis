# Certicom ECC2K-130 and ECCp-131 tensor references

**The Certicom ECC2K-130 discrete logarithm has not been recovered by this work.**
**The added ECCp-131 discrete logarithm has not been recovered either.**

The user-requested prime-field counterpart is officially named **ECCp-131**
in [Certicom's parameter list](https://www.certicom.com/en/curves-list), rather
than ECCp-130. Its exact published P and Q are in [eccp131.json](eccp131.json).
`eccp.py` implements prime-field arithmetic and canonical point compression;
`tensor_prime.py` composes integer Fourier multiplication, bounded modular
quotient/remainder constraints, all point-addition cases, fixed-cofactor image
witnesses and affine hash membership with the shared tensor engine.

```bash
python eccp.py validate
python eccp.py demo --fixture-scalar 7 --backend tensor_indexed --output /tmp/eccp-demo.json
python eccp.py verify --certificate /tmp/eccp-demo.json
python tensor_cli.py challenge --instance eccp131 --slots 2 --output /tmp/eccp-tensor.json
python -m unittest -v test_ecc2k test_tensor_contraction test_tensor_encoding test_eccp
```

The combined suite passes 39 development tests, including all 361 point pairs
on the 19-point prime-field fixture and 16 independent OpenSSL multiples of the
published ECCp-131 points. The actual two-slot prime-field network compiles to
1,564,506 edges, 654,523 variables and maximum degree 1,032. Default contraction
again selects u_0=0 and rejects exact summation under the configured budget.
See [the prime-field validation report](prime-development/README.md) for source,
commands, raw outputs, the diagram/PDF and remaining requirements. These are
correctness diagnostics, with no performance comparison or theorem proof.

The scalar (ell=1) tensor-contraction engine and a coordinate relation encoder
are now implemented. The engine includes unramified extension-ring arithmetic,
packet packing, Cauchy deformation, weighted modes, recursive child networks,
interpolation, tapered Hermite recovery, and creation-time canonical lifting.
This is the scalar case needed for exact Boolean counts and relation witnesses;
the general truncated V-polynomial case ell>1 is outside this implementation.
The earlier meet-in-the-middle backend remains separately selectable.

The implementation and its tests do not formally verify the external theorem,
and no practical subexponential speedup is claimed.

## Tensor engine and coordinate encoder

```bash
python tensor_cli.py recursive-check --output results/recursive-tensor-check.json
python ecc2k.py demo --degree 13 --secret 1427 --slots 2 --backend tensor_indexed \
  --output results/tensor-demo13.json
python ecc2k.py verify --certificate results/tensor-demo13.json
python tensor_cli.py challenge --slots 2 --output results/challenge-tensor.json
python run_experiments.py --tensor-only --output-dir results-reproduced
```

`recursive-check` exercises the recursive path with explicitly marked small
experimental parameters and compares its answer with an independent exhaustive
sum. Tests also cover two recursive levels and creation-time lifts. Experimental
parameters do not inherit the manuscript's asymptotic cost bound.

`tensor_indexed` is an executable end-to-end validation backend using a Boolean
network over indices into explicit factor-base lists. It recovers the demo scalar
through tensor witness extraction and relation elimination. Its generating scalar
is not passed to the solver. At these small sizes it uses exact leaf search; this
indexed encoding does not have the compact coordinate construction's guarantee.

`tensor_coordinates` is the coordinate backend for the relation collector.
The standalone `tensor_cli.py challenge` command constructs its implicit network
directly from hash seeds without enumerating the challenge factor bases. It uses
the actual published Q. Finding a decomposition would still be only the first
step toward collecting enough relations to extract the challenge scalar.

The full two-slot graph compiled with 2,694,680 edges, maximum degree 1,032, and
1,195,386 Boolean variables. At this size, the manuscript's lambda is 22 and
u_0=floor(lambda/131072)=0. The engine therefore enters the manuscript's exact
summation fallback and reports that its operation budget would be exceeded.

The source is in `tensor_ring.py`, `tensor_network.py`, `tensor_contraction.py`,
`tensor_encoding.py`, `tensor_relations.py`, and `tensor_cli.py`. The tensor engine
does not call meet-in-the-middle. See [TENSOR_IMPLEMENTATION.md](TENSOR_IMPLEMENTATION.md)
for the construction, binary-field adaptation, source mapping, and limits.

The measurements and limits of the completed runs are recorded in
[RESULTS.md](RESULTS.md). To reproduce them in a new directory:

```bash
python run_experiments.py --output-dir results-reproduced
```

## Run

Python 3.10+ and SymPy are required. The tests optionally compare against a system
OpenSSL library with binary-field support; there is no SageMath or GPU dependency.

```bash
cd experiments/hashed-ecdl-tensor-reference
python -m pip install -r requirements.txt
python -m unittest -v test_ecc2k test_tensor_contraction test_tensor_encoding
python ecc2k.py validate --output results/challenge-validation.json
python ecc2k.py demo --degree 19 --secret 114415 --slots 3 --output results/demo19.json
python ecc2k.py verify --certificate results/demo19.json
```

The demo constructs a separate, explicitly labeled target over GF(2^19), in a
prime-order subgroup of order 130873. Its generating scalar is **not** passed to
the solver. The solver obtains it from hashed-factor-base relations and verifies
the result by multiplication. The complete certificate records every relation
and the coefficients that cancel the factor-base columns. `verify` rechecks the
point encodings, membership predicates, subgroup membership, relations,
cancellation, and the recovered scalar.

There is also a GF(2^13) demo with subgroup order 2003:

```bash
python ecc2k.py demo --degree 13 --secret 1427 --output results/demo13.json
```

## Published challenge

The parameters in [challenge.json](challenge.json) are transcribed from
[Certicom's curve list](https://www.certicom.com/en/curves-list).

- Field: GF(2)[z] / (z^131 + z^13 + z^2 + z + 1).
- Curve: y^2 + xy = x^3 + 1.
- Prime subgroup order: 680564733841876926932320129493409985129 (130 bits).
- Cofactor: 4.
- Target: the **published** P and Q, with no known scalar supplied.

`validate` checks irreducibility, prime subgroup order, curve membership, [n]P =
[n]Q = O, point-encoding round trips, [4]U = P and [4]V = Q from the published
auxiliary points, and the full curve order using the Koblitz Frobenius recurrence.
Tests compare multiplication of both published points against OpenSSL on several
independent scalars, including the subgroup order.

## Hashed factor bases

For nonidentity points with x != 0 the encoding is

    enc(A) = 2*x(A) + low_bit(y(A)/x(A)).

**This binary-curve encoding differs from low_bit(y) on odd-prime-field curves.**
The x = 0 point has its unique canonical selector zero and is discarded by the
odd-prime-subgroup membership check.

Each slot uses an independent affine permutation modulo a prime s > 2^132:

    H_i(z) = (alpha_i*z + beta_i) mod s
    F_i = { A != O : [n]A = O and H_i(enc(A)) < threshold }.

Enumeration inverts H_i for each accepted hash output and decodes the resulting
candidate point; it does not enumerate all field elements or use known scalar
multiples to construct the factor base. Decompression uses half trace, so this
reference implementation supports odd extension degrees.

Relation collection picks independent u,v and searches for

    [u]P + [v]Q = A_1 + ... + A_m,  A_i in F_i.

The relation finder receives the target point and the bases, not u,v. A dependency
among the resulting matrix rows produces [U]P + [V]Q = O and k = -U/V mod n.

## Challenge-sized limits and bounded searches

```bash
python ecc2k.py estimate --slots 2
python ecc2k.py estimate --slots 3
python ecc2k.py hashed --slots 3 --output results/challenge-hashed-preflight.json
python ecc2k.py bsgs --bound 0x100000000 --seconds 45 --output results/challenge-bsgs.json
python ecc2k.py rho --steps 100000 --seconds 30 --seed 1 \
  --checkpoint results/challenge-rho-checkpoint.json --output results/challenge-rho.json
```

At m = 2, each factor base is expected to contain about 2.61e19 points. Even
storing only 17 bytes per point would require about 4.43e20 bytes per base before
indices, Python object overhead, or linear algebra. At m = 3, enumeration alone
requires about 2.11e14 candidate decodings and subgroup checks; the larger
meet-in-the-middle half has about 7.74e25 entries. The default budgets reject
these configurations before allocating their tables.

Increasing m makes each base smaller. The implemented tensor engine follows the
paper's recursion, but its default parameters still select exact summation at
the challenge's size. The paper addresses prime fields. The binary-polynomial
Fourier encoder here is an adaptation, independently tested against reference
arithmetic; it does not establish a formally verified binary-field theorem.

`bsgs` searches only 0 <= k < bound; `not_found_in_interval` says nothing about
other scalars. The interval's upper endpoint is exclusive. `rho` is a resumable
reference 16-adding walk with Floyd collision detection, without the published
Koblitz automorphism acceleration. Its budget counts walk additions, excluding
jump precomputation and validation. Checkpoints include the instance fingerprint,
seed, counters, points, and scalar coefficients; coefficient invariants are
checked on resume. Reuse the same command to continue a saved walk. Time and
entry limits are configurable.

Exit code 0 means a verified result, valid parameters, or an estimate. Exit code
2 means the configured budget or search interval was exhausted, not that the
ECDLP has no solution. Results always identify the backend used.

The small real-challenge factor-base sample in
`results/challenge-factor-base-sample.json` exercises enumeration and relation
search on the actual curve with deliberately small bases. Failure to decompose Q
over these particular bases is not a statement about other decompositions.

## Sources

- [Certicom curve parameters](https://www.certicom.com/en/curves-list).
- [A Subexponential Time Algorithm for Elliptic Curve Discrete Logarithm,
  version 0.2, October 29, 2026](https://github.com/bochum-crypto/subexponential-ecdl/blob/main/subexponential-ecdl.pdf).
- [Original ECC2K-130 distributed attack project](https://ecc-challenge.info/).

The small demonstrations and tests validate this implementation's outputs. They
do not validate the external tensor-contraction theorem or constitute a solution
to the full Certicom challenge.
