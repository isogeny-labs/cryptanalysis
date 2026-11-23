# Coverage of three signed terms in a cyclic group

The group here is additive modulo the archived subgroup order 2,147,505,293. The field characteristic is 2,147,483,647. Each basis contains 500 nonzero residues distinct up to sign. The abstract bases serve as controls for uniform-query coverage. The two archived curve bases have different construction rules.

| Seed | Distinct represented elements | Fraction of group | Largest possible relative coverage increase |
|---:|---:|---:|---:|
| 0 | 160,355,954 | 7.46708% | 3.93628% |
| 1 | 160,384,466 | 7.46841% | 3.91780% |
| 2 | 160,357,840 | 7.46717% | 3.93505% |

The last column rounds upward. It divides the [Lean upper bound](../m31-reflection-count/TripleCoverage.lean) of 166,668,000 by the enumerated coverage and subtracts one. Each row is an exhaustive count for one reproducibly generated basis. Counts include zero if a triple represents it. Both enumerators store presence bits and publish only cardinalities.

## Population bound under uniform sampling

Let N be the prime group order and M = 166,668,000. Choose an ordered list of 500 residues uniformly from the lists with no zero or repeated absolute sign class. With a sign class defined as the pair {x, −x}, this distribution also results from successive uniform choices among the remaining allowed residues.

The M canonical signed forms in TripleCoverage.lean give distinct integer coefficient vectors. The three cases can be read off a vector by its absolute coefficient sum and the signs of its entries: a single term has absolute sum one, a same-sign triple has absolute sum three and only one sign, and a mixed triple has two units of one sign and one unit of the other. Multiplicities within a sign recover the unordered indices. Every form can be realized by three signed terms, with a cancelling pair added to a single term.

Take two distinct forms and choose an index where their coefficients differ. Their difference at that index is a nonzero integer of magnitude at most six, hence invertible modulo N. Condition on the other 499 basis residues. The remaining residue is uniform on N − 999 choices, since zero and the 998 signed residues already used are excluded. At most one choice makes the two forms equal in the group. Thus their collision probability is at most 1/(N − 999).

In a fiber of size h ≥ 1, losing h − 1 distinct outputs relative to the number of descriptions costs at least h − 1 unordered colliding pairs, because h(h − 1)/2 ≥ h − 1. Summing this inequality over fibers and taking expectations gives

    E[distinct outputs] ≥ M − M(M − 1)/(2(N − 999)) > 160,200,440.

Consequently the expected uniform-query coverage exceeds 7.45983%. The universal coverage ceiling divided by this expected coverage is less than 1.04038. This ratio concerns population means and gives no lower bound on the coverage of every individual basis. The counting argument here is a mathematical derivation. The sibling Lean theorem certifies the universal upper bound.

## Replay

Build with a C++20 compiler and run locally.

    clang++ -O3 -std=c++20 -Wall -Wextra -Werror count.cpp -o /tmp/m31-sumset
    /tmp/m31-sumset

Seeds 0, 1 and 2 initialize the standard 32-bit Mersenne Twister. Rejection discards zero, out-of-range words, and previously used sign classes. One enumeration visits unordered triples drawn with replacement from all 1,000 signed terms. The second visits the canonical forms up to an overall sign and counts inversion orbits, correcting the singleton orbit of zero. The process checks both counts agree for each basis. The empirical trials use pseudorandom bases. The population argument assumes mathematically uniform sampling.
