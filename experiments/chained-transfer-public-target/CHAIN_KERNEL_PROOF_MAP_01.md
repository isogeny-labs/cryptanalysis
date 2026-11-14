# Geometric chain-kernel and collapse proof map

2026-11-13. Native29830a, written2e21d5; unsigned, partially formalized.
Both unchanged original4.35/4.34.1 gates audit three declarations/zero
trusted. Exact local original PCC bindings pass; no holes, custom axioms
or unverified native evaluation. [pcc:unverified]

| Obligation | Exact declaration | Binding and actual hypothesis |
| --- | --- | --- |
| Kernel invariant-factor equations | ChainKernels223.kernel_type_from_order_and_two_torsion | cbaaa0; Nat2a+b=6,a+b=3+d |
| Free4 iffdisjoint | ChainKernels223.free_four_kernel_iff_disjoint | 580339; same two equations |
| Repeated-product collapse | ChainKernels223.same_product_two_steps_collapse | 0cc751; actual dual[2] factorizations for interior/final nodes |

The two arithmetic lemmas use standard propext/Classical.choice/Quot.sound;
the functional identity uses no axioms. These are faithful implications,
with the actual geometric hypotheses stated separately. [pcc:unverified]

Remaining Lean bridges: actual abelian/Picard maps, etale degree/cardinality,
the exact restriction N0:J0[2]→Gold, full geometric kernel structure,
finite-abelian exponent4 classification, polarization descent and actual
identification of the two derived free kernels. No J[4] coordinate basis
or signed execution result is supplied. [pcc:unverified]

All135 intersection dimensions and all9x9 actual A[2] vector tables are
native data. The128 actual map equalities support the global written
collapse proof; they do not replace it or establish a cost comparison.
All product/twist/literal controls remain preserved. [pcc:unverified]
