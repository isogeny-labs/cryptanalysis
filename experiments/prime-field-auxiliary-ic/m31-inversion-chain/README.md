# Inversion by concatenating all-one exponents

For p = 2³¹ − 1 the inversion kernel first constructs x raised to 2²⁹ − 1. Two squarings and a multiplication by x then give exponent p − 2. A block of length a represents exponent 2ᵃ − 1. Concatenating a previously computed pair of lengths a and b costs b squarings and one further multiplication. It yields length a+b by the identity in Chain.lean.

The current C++ recursion constructs lengths 1, 2, 3, 6, 7, 14, 28, 29. This takes 28 squarings and seven further multiplications. Including the final exponent adjustment gives 30 squarings and eight further multiplications per inversion.

Chain.lean enumerates strictly increasing length lists starting from 1, permitting each next length to be the sum of any two previously constructed lengths, including a repeated operand. It checks reachability of 29 after at most six and seven additions. Sorting by length covers every straight-line construction in this model because both operands of a positive length sum are strictly smaller than its result. Duplicate lengths can reuse the first result. Values above 29 cannot contribute to 29. The checked results certify that the current seven concatenations attain the minimum for this construction.

At width 64 the binary product tree uses 63 multiplications upward and 126 downward. Including the root inversion gives 227 modular products if a square is counted as one product. Saving one root product through another inversion method would remove 1/227 of that count. Elapsed time also depends on critical-path latency, parallelism, loads and reductions. This certificate covers concatenations for the 29-bit intermediate. Other inverse algorithms, other intermediate exponents and whole-program timings lie outside its scope.
