# Controlled coordinate-system comparison

Status: **source and pre-data protocol preparation; experiment not launched**. User requested the actual growing-instance comparison, including time per usable relation, memory, rejection and total collection cost. The earlier exploratory archive does not fulfill this request. [pcc:unverified]

[Plan](PLAN.md) · [protocol](protocol.json) · tracking [PR #1767](https://github.com/isogeny-labs/cryptanalysis/pull/1767).

## Controlled variable

Use three summands throughout. The eliminated arms solve S4 plus membership polynomials in Montgomery u, Edwards y or the torsion-invariant z. The retained-point arm solves two S3 constraints with an intermediate coordinate and a separate infinity branch. Every applicable arm receives the same geometric base, target and ordinary query stream. Backend settings are fixed at SymPy f5b/lex. [pcc:unverified]

Cofactor-1 controls are short-Weierstrass elimination/retained-point/A-A comparisons. They cannot be given the source's rational-torsion models over the same field. One control family matches the field; the other matches the prime subgroup order across a different field. No causal torsion-only comparison is claimed. [pcc:unverified]

## Recorded quantities

Per attempted query: equation build, Groebner solving, root extraction, sign lifting and point checking, failures, timeouts, candidate rejection, ordinary usable rows and rank increments. Per collector: contiguous observed wall/CPU interval, complete-collection time or null when censored, same-point rho reference, OS child peak RSS, CPU affinity, placement limitations, cgroup counters and pressure. The cost-per-usable-row denominator remains null if there are no rows. Collector process RSS includes interpreter/controls; it is not an incremental solver allocation measurement. [pcc:unverified]

The collector interval includes query construction, per-query audit and artifact snapshots; reusable fixture/base preparation, exact oracle setup, process import and the separately timed rho reference are excluded and cannot be silently treated as a fully charged cold algorithm. Ordinary-host timing status remains exploratory. [pcc:unverified]

## Checks and admission

`make test` exercises fixed published toy fixtures only: planted sums, a cancellation path through infinity, a genuine one-point-base UNSAT case, rank consistency, the same-point rho reference and censored/zero-denominator analysis. This is producer unit validation, not a signed PCC verdict. [pcc:unverified]

`export_panel.py` adapts actual captured rows through the canonical unified exporter, retains raw-file hashes and leaves independent verification/timing qualification unset. No export has been produced before execution. [pcc:unverified]

`run_panel.py` refuses an unfrozen/modified protocol or changed source. Normal execution requires the repository checkpoint and GPU-host admission. A CPU-only/Git-checkpoint alternative additionally requires the user's actual explicit exception; `admission.example.json` is deliberately not an authorization. The asynchronous clarification question is pending. No held-out panel inputs, observations or measured comparisons have been produced in this continuation. [pcc:unverified]

The source is ready for an admitted bounded panel, not certified as a production F4 implementation. Full performance qualification, canonical identity promotion and signed independent scientific review remain separate gates. [pcc:unverified]

## Commands after admission

The canonical protocol tool is `crypto-autoresearcher:tools/experiment_protocol.py`. Validate/freeze and commit the source/protocol before generating the panel, then execute through the applicable checkpoint/measurement workflow. For an explicitly authorized CPU/Git exception, the runner takes an admission file binding that authorization and the current source commit. [pcc:unverified]

```sh
make -C experiments/curve-representation-controlled-20261118 test
# Only after actual admission and protocol freeze:
python experiments/curve-representation-controlled-20261118/run_panel.py \
  --admission /path/to/actual-admission.json --out /path/to/new-run-directory
```

Do not manufacture the admission fields, an isolation receipt, checkpoint success or a signed standing. Preserve every failure and report full-collection cost as unknown when the original stopping condition is not met. [pcc:unverified]
