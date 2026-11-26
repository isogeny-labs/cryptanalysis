# Pair-transversal spans do not merge before saturation

The paired evaluation formulation asks for one row from each conjugate pair
such that the selected rows do not span the homogeneous section space. A
natural colorful dynamic program stores only the row span of a partial
transversal, merging assignments with the same reduced row space.

The exact control reconstructs the two rows in every slot of the seven
genus-two binary panels. For each partial assignment it computes a canonical
reduced-row-echelon representative over \(\mathbb F_{101}\). It tests the
natural slot order, every balanced slot subset, every subset one row short
of ambient rank, and the first depth at which full rank is possible.

## No balanced-prefix merging

Every balanced prefix is injective:

| Slots | Balanced slots selected | Slot subsets | Assignments per subset | Distinct spans per subset |
| ---: | ---: | ---: | ---: | ---: |
| 3 | 1 | 3 | 2 | 2 |
| 4 | 2 | 6 | 4 | 4 |
| 5 | 2 | 10 | 4 | 4 |
| 6 | 3 | 20 | 8 | 8 |
| 7 | 3 | 35 | 8 | 8 |
| 8 | 4 | 70 | 16 | 16 |
| 9 | 4 | 126 | 16 | 16 |

Thus neither a favorable slot ordering nor canonical row-space hashing
reduces the meet-in-the-middle frontier on these controls.

## Merging begins only next to full rank

Let \(h=m-g+1\) be the ambient homogeneous rank. At depth \(h-1\), the
number of distinct spans is still close to all \(2^{h-1}\) assignments:

| Slots | \(h-1\) | Assignments | Range of distinct spans over all slot subsets | Largest multiplicity |
| ---: | ---: | ---: | ---: | ---: |
| 3 | 1 | 2 | 2 | 1 |
| 4 | 2 | 4 | 4 | 1 |
| 5 | 3 | 8 | 7--8 | 2 |
| 6 | 4 | 16 | 15--16 | 2 |
| 7 | 5 | 32 | 29--32 | 2 |
| 8 | 6 | 64 | 60--64 | 2 |
| 9 | 7 | 128 | 120--127 | 4 |

At depth \(h\), most assignments reach the full ambient span and can be
discarded permanently: adding more rows cannot restore nonspanning. Across
the nine possible eight-slot subsets of the nine-slot panel, only 2--9 of
256 assignments remain nonfull. Each survivor has its own span. This late
collapse is useful for pruning after enumeration but does not find the
survivors without processing the essentially injective earlier frontier.

At the binary coverage scale, \(h=m-O_g(1)\) and \(2^m=p^{g+o(1)}\).
Consequently a forward span-state DP still pays the full positive exponent
before saturation. This is a finite diagnostic, not a lower bound on every
paired-transversal algorithm. It leaves algebraic methods that identify the
rare nonsaturating branches without enumerating their predecessor spans
open.

~~~sh
python3 paired_span_state_control.py | cmp - paired_span_state_control.json
python3 -m py_compile paired_span_state_control.py
~~~

