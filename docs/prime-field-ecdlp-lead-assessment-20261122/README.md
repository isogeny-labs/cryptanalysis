# Prime-field ECDLP — lead assessment & measured verdict (2026-11-22)

Deposited from a Claude Code cloud session (orchestrator + two Mythos 5.1 deep-reasoning
subagents, reconciled) and the measured follow-up run against
`isogeny-labs/lfd-summation-systems`. Every number is `[pcc:unverified]` (an assertion;
one engine/host, no pcc claim id). Proven vs conjectured kept separate.

## Headline
The sub-√p question reduces to the per-decomposition **solving-degree growth**:
1. **Measured** (`lfd-summation-systems/experiments/ic-solving-degree/rows-merged.jsonl`,
   5,818 systems): prime-field last-fall/solving degree **saturates the proven `mk+1` cap
   (linear in tower height, slope ≈ m) for every arity m≥5** a sub-√p exponent needs;
   bounded only at m=3 (which cannot beat √p). Binary stays bounded through m=4 (the
   Frobenius/Weil-descent structure F_p lacks).
2. **Sealed** (`lfd-summation-systems/experiments/ic-costmodel`, validation PASSES): under
   the measured degree law, index calculus is **+3…+10 bits worse than rho at every size
   40–256 bits**; it wins only in the D=2 bounded-degree counterfactual. **No crossover p\*.**

**⇒ Lead B1 (PKM two-power-subgroup sub-√p tower) is dead as posed** — a clean publishable
negative. A1–A4 optimise a solve whose degree is pinned to `mk+1`: constant-factor
engineering, not exponent-movers. The only live reopener is a *non-Gröbner* bounded-cost
decomposition oracle (e.g. a real Graeffe/iterated-norm engine, absent in-repo) that beats
the budget table `C_dec(m,p)`.

## Files
- `FINDING_B1_solving_degree.md` — the measured LFD(m,k) finding (core result)
- `SEAL_costmodel.md`, `costmodel_headline.md`, `costmodel_fig-cost.svg`, `data/costmodel_sweep.jsonl` — cost-model seal
- `lfd_growth_fit.txt`, `analyze_lfd.py` — growth-law fit on the 5,818-system table
- `budget_table.{txt,csv,py}` — `C_dec(m,p)` acceptance test
- `semireg_dreg.{txt,py}` — validated semi-regular d_reg predictor
- `classify.gp`, `classify_demo.txt` — S5 structural pre-screen
- `lowerbound_membership.md` — generic+membership Ω(√p) bound (closes B3)

## Residual falsifiers (open)
- Short high-m lever (measured k≤4): extend m=5 to k=5,6, confirm it stays on `mk+1`.
- Untested prime-field presentations (split / System-(4)).
- A non-Gröbner bounded-cost oracle beating `C_dec(m,p)` would reopen B1.
