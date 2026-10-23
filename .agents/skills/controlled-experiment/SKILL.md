---
name: controlled-experiment
description: Decide whether a claim needs an experiment and what makes it able to fail - classify each claim, build negative, positive and A/A control arms, isolate confounders in a variable ledger, freeze the protocol before data, and report by rank and effect size with uncertainty. Pointer to the canonical skill in aburan28/crypto (.claude/skills/controlled-experiment); use it before any comparative or statistical sentence about a candidate, curve, solver or factor base in this repository.
---

# Controlled experiment (pointer)

The canonical skill is `aburan28/crypto`,
`.claude/skills/controlled-experiment/SKILL.md`. Read it and follow it;
this pointer adds no rule and lowers none. The record of the design is the
`experiment-protocol` skill's `protocol.json`; the record of the data is
the export.

## In this repository

- A stage diagnostic (F4/F5/SAT solve time, coverage, cost per useful row)
  is never a speedup; a comparative claim about one needs its own
  controls (the same base, formulation and inputs; a certified UNSAT or
  exhaustive small-field control for false positives; a timeout is
  censored, never UNSAT).
- The A/A arm for a wall-time claim is the same candidate rerun in
  alternating pairs on the same pinned CPU, and a Tier 1 speedup needs a
  95% paired confidence interval whose lower bound exceeds 1
  (`AGENTS.md`, "CPU performance evidence tiers").
- A planted decomposition is the positive control; natural yield is
  estimated only on ordinary uniform queries.
