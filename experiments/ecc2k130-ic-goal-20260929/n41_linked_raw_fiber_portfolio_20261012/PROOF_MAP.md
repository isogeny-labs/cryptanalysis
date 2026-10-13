# Proof and replay map

| Statement | Evidence | Scope |
| --- | --- | --- |
| The four slices cover all raw target preimages and preserve the source states | [Protocol](protocol.json), [exact byte-rebuild audit](audit_result.json), [verifier](verify.py) | The only formula change per slice is one target-fiber unit clause; all source selectors remain unpinned. |
| The known linked relation lies in fiber 3 | [Prior independent Sage audit](../n41_n131_linked_frobenius_pair_20261012/audit_result.json), [positive assignment check](audit_result.json) | Complete assignment satisfies every row of the fiber-3 formula. |
| Each public slice is censored at its cap | [Result](result.json), [solver logs](fiber3.stdout), [verifier](verify.py) | Four one-worker 38-second parent intervals, no terminal SAT/UNSAT lines. |

The experiment changes target selection and measures solver behavior; it introduces no new mathematical theorem. The underlying linked-Frobenius coefficient theorem and its concrete Sage bridge remain in the prior linked-pair proof map.
