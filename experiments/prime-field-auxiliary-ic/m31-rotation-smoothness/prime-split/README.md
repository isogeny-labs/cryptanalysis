# Cost of a two-list product search

A candidate product of two odd representatives below p has size at most Q=(p-1)^2. Consider assigning each allowed odd prime to one of two lists and materializing **all** smooth integers up to Q on each side, including one on both sides. A residue join can then find reciprocal products. Before implementing the join, compare just the total number of list entries with the number of odd smooth integer representatives below p in the existing search.

For each exact prime support of cardinality at most d, count positive exponent vectors whose product is at most Q. The subset sum transform aggregates those counts for every possible side of a partition. Minimize the sum of complementary side counts over all assignments. This is a lower bound for the full lists because every omitted support has a nonnegative count. At each bound try d=3,4,5 and stop once the minimum exceeds the representative count. The minimizing mask refers to the partial sum at the reported depth. This counts entries before filtering or joining and gives no timing bound for other algorithms.

## Bounded-list follow-up

After the full-list count, test a cheaper incomplete search at bound 83. For each of the five bits of the zero-based index of an odd prime, separate primes with a set bit from the others. Cap both integer lists at p-1. Use the five partitions exactly as specified, retaining repeated list construction in the total. Join reciprocal 31st-power residues and compare the union of products with the existing 24-product catalog. Report the covered orbit pairs as a set union via divisor replay. Record partial coverage and total entries even when coverage is low. This diagnostic uses a previously observed catalog.
