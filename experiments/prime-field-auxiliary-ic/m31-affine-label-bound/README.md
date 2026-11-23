# Predicting one M31 lift label from another under affine coordinate changes

Fix p = 2147483647 and f(X) = X³ + 2X + 14. Sample x uniformly from the whole base field. For any fixed a ≠ 0 and b with (a,b) ≠ (1,0), a Boolean function of the single label “f(x) is a square” predicts whether f(ax+b) is a square with accuracy below 50.00432%. The rule may be chosen separately for each affine transformation. This population differs from the restricted smooth-coordinate graph.

## Derivation

The archived root-exclusion certificate proves that f has no field root. Hence its cubic is irreducible, as is the monic normalization of f(aX+b). If the normalizations agreed, comparing quadratic coefficients would give b=0, and comparing linear and constant coefficients would give a²=a³=1, hence a=1. For every nonidentity map the two irreducible cubics are distinct and coprime. Over this finite field both are separable, so their product is a separable sextic.

In odd characteristic the smooth projective model of y²=f(x)f(ax+b) thus has genus two. The degree-two map to the projective line branches simply at the six finite roots. In the infinity chart v=y/x³ the equation at infinity is v²=a³. Write χ for the quadratic character and S for the sum of χ(f(x))χ(f(ax+b)) over x. The point count is p+1+S+χ(a³). Hasse–Weil gives (S+χ(a³))² ≤ 16p. [Poonen, Lectures on rational points on curves](https://math.mit.edu/~poonen/papers/curves.pdf)

Any Boolean rule is constant, copy, or complement. Copy and complement give signed agreement ±S. The constants give ±21645 because ax+b permutes the field and the target elliptic curve has 2147505293 points. Dividing the corresponding count of correct predictions by p gives the bound above. Because the two marginals coincide, the same identities also give at least 536813749 points in every one of the four source/destination cells. A zero-error rule given just the source label must abstain for both labels. Uniform negation of either nonzero character (a quadratic twist) merely exchanges Boolean labels. A rule that also sees x, or a nonuniform query distribution, has more information than this result covers.

## Exact translation check

For a=1 and b=1, the four counts in translation.csv give S=51595 and optimal accuracy 50.00120129%. The census includes x=p−1 followed by zero. translation.cpp uses repeated field squaring; verify_translation.cpp independently tabulates squares using one representative for each ±y pair. Compile each with a C++17 compiler and run without arguments. The second route uses a 256 MiB bit table. Compare each stdout byte-for-byte with translation.csv.

## Formal scope and replay

AffinePair.lean proves the degree and separability statement, the count on the two sets of fibers, and the numerical Boolean-rule bound under the genus-two Hasse–Weil inequality and the stated marginal balance. The geometric genus formula and Hasse–Weil theorem are external mathematical inputs. The complete translation table is a native enumeration.

From the project's mathlib environment set SRC to the absolute path to experiments/prime-field-auxiliary-ic, then use:

```sh
build=$(mktemp -d)
lake env lean --root="$SRC" -o "$build/M31FixtureObstruction.olean" "$SRC/M31FixtureObstruction.lean"
lake env sh -c 'export LEAN_PATH="$1:$LEAN_PATH"; lean "$2"' sh "$build" "$SRC/m31-affine-label-bound/AffinePair.lean"
```
