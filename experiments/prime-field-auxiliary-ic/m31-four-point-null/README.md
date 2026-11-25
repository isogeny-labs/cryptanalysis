# Expected four-point relation count in a uniform signed basis

Let the group be cyclic of prime order n > 7. Sample k distinct nonzero
sign orbits uniformly without replacement. Count signed sums of four distinct
basis elements equal to zero, identifying a sum with its global negative.
The expected count is exactly 8 choose(k,4)/(n−3).

Fix a nonzero group element t. The ordered summands a and t−a form an
eligible unordered pair when a avoids 0, t and t/2. Each eligible pair
therefore occurs twice among n−3 ordered choices. Its two summands have
different sign orbits because their sum is nonzero.

Choose two different eligible pairs with sum t. They cannot share a signed
element because each element has a unique complement. They share an unsigned
orbit precisely when one contains x and the other contains −x. Both x and −x
are eligible for (n−5)/2 choices of unsigned orbit: exclude the orbits of t
and t/2 from all (n−1)/2 nonzero orbits. Such an orbit determines one pair
of pairs. Two pairs cannot share two unsigned orbits since that would make
their sums negatives of each other. Hence exactly (n−5)(n−7)/8 choices
have four distinct orbits.

Use one representative of each of the (n−1)/2 possible sum orbits {t,−t}.
Each signed four-point relation occurs three times, once per partition of its
four terms into pairs. This gives (n−1)(n−5)(n−7)/48 relations in the population.
Dividing by choose((n−1)/2,4) gives 8/(n−3) per four-element subset.
Linearity of expectation then gives the stated formula without independence
assumptions between overlapping subsets.

For the M31 fixture, use group order 2147505293 and k = 500. The expectation
is 294060700/30678647, approximately 9.58519129. The frozen auxiliary and
plain bases have 10 and 14 relations respectively.

Expectation.lean checks the rational identities and the fixture value.
The bijections above are a written counting proof. Run python3 check.py to
check the count by exhaustive signed enumeration on ten small prime orders.
