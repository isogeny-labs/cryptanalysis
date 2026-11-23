# Signed squaring for the complete lift census

At p=2^31−1 let H=floor(x²/2^31) and L=x² mod 2^31. Return H−(p−L) as a signed word on every square and normalize once at the end of the chain. The bit-clear instruction computes p−L directly from the low product. Inputs may be negative on later squarings.

Use Apple clang++ -O3 -std=c++17 -mcpu=native and the existing projected-character driver prefix, including its exact XOR-label table and original vector evaluator. Build from this directory:

```sh
sed '/^int main(/,$d' ../m31-projection-label/bench.cpp | cat - census.inc | clang++ -x c++ -std=c++17 -O3 -mcpu=native - -o /tmp/m31-balanced-square
/tmp/m31-balanced-square
```

Each timed call generates all positive 89-smooth integers below p (including even ones), evaluates x³+2x+14, computes the complete ordered lift bitmap as one word per coordinate, and counts its ones. Construct the lookup table inside every projected call. Six paths combine the 30-square direct and 15-square projected character methods with original, unsigned-minimum, and signed squaring. Six rounds use a balanced six-order crossover. Compare every label against the original direct evaluator after timing. Check scalar reference counts and retain all rows. This is a local warm-process comparison with fresh per-call data; compare like methods and the fastest canonical control.
