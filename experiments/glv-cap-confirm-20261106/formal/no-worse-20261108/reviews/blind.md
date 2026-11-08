# Blind algebra attestation — PR #1445

**Verdict: breaks** the proposed implication from pooled passage to the separate family upper bound. The pooled check itself **holds** under the supplied rule, and all supplied intervals are well formed.

- Reviewed immutable head identifier: `8e8c49b6e50463988710f21c5253172176610fbf` (identifier supplied with the task; repository state was not inspected).
- Sole mathematical source read: `experiments/glv-cap-confirm-20261106/formal/no-worse-20261108/BLIND_INPUT.json`, SHA256 `11c13dfb48e6de04ea7102122c5331a7710087b2dcaa9ea886fdcdf1c19c50ec`.
- I did not read the Lean proof, source code, `results.json`, `README`, `REVIEW_PLAN`, git history, sibling reviews, or prior chat. The Conductor claim response supplied task administration only.

## Independent derivation

Let `S = 10,000,000,000,000,000`. For pooled sizes 40–43, the lower endpoints are respectively `9,633,305,383,496,846`, `9,607,939,208,626,060`, `9,539,100,281,038,944`, and `9,495,902,517,552,110`. Each is at most `S`, so the stipulated conjunction defining pooled passage is true. Each pooled lower endpoint is also at most its corresponding upper endpoint. Each pooled upper endpoint exceeds `S`; pooled passage therefore says nothing about those upper endpoints.

The separate family interval is `[9,860,137,324,692,078, 10,186,699,532,206,690]`. Its lower endpoint is at most its upper endpoint, and it straddles `S`: the lower is `139,862,675,307,922` below `S`, while the upper is `186,699,532,206,690` above `S`. Thus the interval does **not** lie wholly at or below `S`. The supplied point estimate `10,019,840,110,118,106` lies inside this interval and is `19,840,110,118,106` above `S`.

The supplied input is itself a counterexample to `pooled passage => separate family upper <= S`: the antecedent is true and the consequent is false. No relation between a pooled lower endpoint and the separate family upper endpoint is given that could repair this implication.

## Known-false controls

- Requiring **every pooled upper endpoint** to be at most `S` gives false for all four supplied intervals; this is a distinct rule from the stipulated pooled check.
- Requiring the **separate family upper endpoint** to be at most `S` gives false, while checking only its lower endpoint gives true. These checks distinguish an interval wholly below the cap from one that crosses it.
- Requiring the **separate point estimate** to be at most `S` gives false. The point estimate does not replace the family upper endpoint.
- As a logical perturbation, replacing one pooled lower endpoint with `S + 1` makes the stipulated pooled conjunction false; reversing any interval's endpoints makes its well-formedness check false. This confirms the direction of the inequalities used above.

This is arithmetic and implication review of the supplied numbers only. The input does not establish that any endpoint or point estimate was empirically measured, how observations were sampled, how intervals were constructed, their nominal or actual statistical coverage, independence, or whether the intervals describe the claimed population. Those claims need evidence outside the permitted blind input.
