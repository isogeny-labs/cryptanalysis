# Proof map

Toolchain: `leanprover/lean4:v4.34.1`. Run `lean QuadraticNorm.lean` in this
directory. `lean_build.exit`, `lean_build.stdout`, and `lean_build.stderr`
preserve the checked result and `#print axioms` output. The three declarations
use only `propext`, `Classical.choice`, and `Quot.sound`.

| Result | Lean declaration | Exact scope |
| --- | --- | --- |
| Reciprocal `S3(t,u,q)` is quadratic in `u` with leading coefficient `1+(tq)^2` | `QuadraticNorm.s3AsQuadratic` | Every commutative ring with `2=0`, including the exceptional zero-leading-coefficient case |
| Dividing that quadratic by an invertible leading coefficient preserves its zero | `QuadraticNorm.normalizeQuadratic` | Every commutative ring with an explicit inverse law `A*inverse=1`; the nonexceptional branch used by the circuit |
| A shared root of the quadratic and a linear reduced equation makes the quadratic norm zero | `QuadraticNorm.commonRootImpliesNormZero` | Every commutative ring with `2=0`, given the two root equations |
| The three-source norm reduces to the pair `r0+r1*u` in the quotient algebra and its norm equals the generated circuit | Open | Needs a formal quadratic-algebra implementation, norm tower, and circuit semantics |
| Every circuit model gives an exact six-pair group relation | Open | Needs source-root extraction, exceptional-case handling, point signs, distinct usable columns, and exact group replay |

The finite-field witness check is in `field_audit.json`; the bit-circuit
witness check is in `build_result.json`. They establish the fixed N41 control
and do not replace the open universal bridges.
