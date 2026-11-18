# Genus-five paired cubics over prime fields

The proof notes give an expected $\widetilde O(p^{4/3})$ discrete-logarithm bound for a genus-five hyperelliptic family over $\mathbb F_p$. A paired-cubic correspondence transfers the problem to a nonhyperelliptic target, where a graph of degree-four pencils supplies the relations. The statement applies on a specified nonempty open of the paired-cubic parameter space in sufficiently large prime characteristic, with the Jacobian order supplied or computed by fixed-genus point counting. The baseline $\widetilde O(p^{3/2})$ uses the same transfer and the class-wide genus-five target algorithm. [pcc:unverified]

The exponent previously appeared heuristically in work on genus-five pencils. The proof notes supply the graph argument and certify its geometric hypotheses on a concrete paired-cubic family. The general prime-field hyperelliptic problem remains open. [pcc:unverified]

| Evidence | Scope |
| --- | --- |
| [Transfer and prime-field family](cubic_transfer_theorem.md) | Recognition of an admissible cubic, the rational correspondence, and the geometric hypotheses for the target |
| [Genus-five graph argument](genus5-bridge.md) | Coverage, graph construction, and the final discrete-logarithm reduction |
| [Exact Sage fixture](cubic_pencil_witness.py) and [frozen output](cubic_pencil_witness.json) | One source curve over $\mathbb F_{19}$, its absolute-simplicity check, and its target pencil locus |

## Reproduce the fixture

From the repository root, follow the [Sage release instructions](../../docs/SAGE_RELEASE.md) to select the checked build. With the repository launcher installed, compare a fresh record with the frozen fixture.

```sh
witness_output="$(mktemp)"
./sage -python experiments/prime-field-genus5-pencils/cubic_pencil_witness.py > "$witness_output" &&
  diff -u experiments/prime-field-genus5-pencils/cubic_pencil_witness.json "$witness_output"
```

The frozen output comes from a retrospective producer run in the research workspace, using the conda SageMath 10.10 and Python 3.14 environment. The working directory was `/workspace/index-calculus-research` and the run exited zero. The historical command was `PATH=/tmp/ic-sage/bin:$PATH /tmp/ic-sage/bin/python cubic_pencil_witness.py > cubic_pencil_witness.json`. This run covers the exact algebraic checks. An end-to-end discrete-logarithm implementation and timing comparison remain open.

## Proof status

The mathematical argument is in the two linked notes. A Lean formalization remains open. It would need the relative Brill–Noether rank locus and the ramification and monodromy results used to bound codegrees, as well as a formal statement of the final relation algorithm. The Sage fixture supplies finite-field calculations for one input. Repository standing is unverified. [pcc:unverified]
