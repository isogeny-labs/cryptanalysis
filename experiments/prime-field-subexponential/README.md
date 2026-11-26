# Prime-field subexponential index-calculus research

The [research note](prime_field_subexponential.md) gives written arguments for an embedding-degree-one family of absolutely simple genus-two Jacobians and an order-free complexity bound for growing imaginary hyperelliptic genus. It also proves a coverage threshold for sums over a small random factor base and reduces fixed-genus index calculus to finding those sums. The general inversion algorithm remains open. The genus-two pairing reduction is classical, and the family argument assumes that the curve and subgroup are supplied. [pcc:unverified]

| Fixture | Scope |
| --- | --- |
| [Frey–Rück script](frey_ruck_witness.py) and [output](frey_ruck_witness.txt) | Point counts, pairing, bilinearity and discrete logarithm in one subgroup of order seven over $\mathbb F_{29}$ |
| [Evaluation-code script](subexp_code_check.py) and [output](subexp_code_check.json) | Evaluation-code rank versus direct Jacobian addition on 3,906 subsets of a fixed point list over $\mathbb F_{29}$ |

## Reproduce the exact checks

Use the checked Sage launcher from the repository root. For a source checkout without the launcher, follow the [Sage release instructions](../../docs/SAGE_RELEASE.md).

```sh
fixture_dir=experiments/prime-field-subexponential
replay_dir="$(mktemp -d)"
./sage -python "$fixture_dir/frey_ruck_witness.py" > "$replay_dir/frey_ruck_witness.txt" &&
  diff -u "$fixture_dir/frey_ruck_witness.txt" "$replay_dir/frey_ruck_witness.txt"
./sage -python "$fixture_dir/subexp_code_check.py" > "$replay_dir/subexp_code_check.json" &&
  diff -u "$fixture_dir/subexp_code_check.json" "$replay_dir/subexp_code_check.json"
```

The two frozen outputs are retrospective producer fixtures from the research workspace, using Conda SageMath 10.10 and Python 3.14.10. The scripts pin their random seeds. Both scripts were replayed in that environment before the import, with byte-for-byte agreement against the frozen outputs. The repository’s patched Sage launcher was unavailable for that replay. The outputs cover exact finite-field arithmetic with no timings. The evaluation-code script uses exhaustive enumeration. [pcc:unverified]

## Proof status

The written proofs and their hypotheses are in the research note. A Lean formalization remains open. It would need the abelian-surface classification and pairing results for the genus-two family, the character estimates and Riemann–Roch evaluation for the coverage result, and the small-place generation and exact subgroup relation arguments for the growing-genus bound. The mathematical claims and finite fixtures have unverified PCC standing. [pcc:unverified]


## Fixed-genus oversampling controls

The [oversampling regularity note](oversampling_regular_limit.md) tests whether deliberately creating multiple transverse branch-product solutions lowers Macaulay stabilization degree. The large-field controls plant up to ten solutions over $\mathbb F_{101}$, exhaust every branch assignment, and record the cumulative quotient through degree six. They do not establish an asymptotic solving-degree bound or a subexponential algorithm. [pcc:unverified]

The [semi-regular branch analysis](semiregular_branch_barrier.md) compares those degrees with the Hilbert/Krawtchouk prediction and records genus 2–7 ledgers for branch degrees two through four. It identifies the low-degree-syzygy requirement for a successful direct algebraic attack; it is a model calculation, not a lower bound. [pcc:unverified]

```sh
fixture_dir=experiments/prime-field-subexponential
python3 "$fixture_dir/high_density_branch_regular.py" |
  diff -u "$fixture_dir/high_density_branch_regular.json" -
python3 "$fixture_dir/multiplanted_branch_regular.py" |
  diff -u "$fixture_dir/multiplanted_branch_regular.json" -
python3 "$fixture_dir/semiregular_krawtchouk_ledger.py" |
  diff -u "$fixture_dir/semiregular_krawtchouk_ledger.json" -
python3 "$fixture_dir/semiregular_branch_degree_ledger.py" |
  diff -u "$fixture_dir/semiregular_branch_degree_ledger.json" -
```
