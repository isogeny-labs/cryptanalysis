# N131 d13 adjacent-union arity screen

The exact d13 adjacent-union source supports a twelve-leaf official-point
XCNF with **414,775 variables, 378,221 clauses, and 302,885 native XOR
rows**. The complete [formula](official_q_union_m12.xcnf) is 17,906,127
bytes. A full [planted assignment](planted_result.json) with original
and adjacent-image branches satisfies every clause and XOR row, and an
[independent Sage replay](sage_result.json) checks all twelve selected
points, ten partial sums, and four cofactor endpoints. The source and
target remain the exact degree-131 challenge instance.

| Arity | Exact formula variables | Clauses | Native XOR rows | Conditional uniform subgroup mean per raw endpoint |
| ---: | ---: | ---: | ---: | ---: |
| 10 | 337,789 | 309,161 | 246,591 | about 561–562 |
| 11 | 376,282 | 343,691 | 274,738 | about 9.28–9.29 million |
| 12 | 414,775 | 378,221 | 302,885 | about 153.51–153.58 billion |

The last column divides exact four-torsion-class tuple counts by the
subgroup order under an assumed uniform distribution within each class.
It is a model of ordinary target multiplicity, not measured SAT yield or
the number of independent relation rows. The [result](result.json)
retains exact integers and decimal ratios for all four target classes.
The source has 16,536 raw point choices per distinct Frobenius position;
the expanded projected factor base has 2,166,216 subgroup-usable points
before folding and 4,134 log columns.

Relative to ten union leaves, twelve leaves increase variables and XOR
rows by about 23%, while the conditional mean grows by roughly
273 million times. Relative to the earlier original-source twelve-leaf
formula, the expanded-source XCNF is larger, but the same simple
uniform full-curve model gives roughly 4,096 times as many labeled
raw tuples. The next gate is a one-worker, 4-GiB, 615-second unpinned
ordinary query on the frozen official point. Any SAT model must pass
source-bound curve-group replay before it counts as a relation. The
method remains a proposal with `candidate_id: null`.
