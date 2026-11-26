#set page(paper: "us-letter", margin: 0.7in)
#set text(font: "Helvetica", size: 9.5pt)
= Horizontal-isogeny derivative as a point character
2026-11-25 · Retrospective finite exact screen · PCC unverified

Candidate: for a known horizontal isogeny with x-map f, test whether the
field character of f'(x([d]G)) equals the scalar character of d up to one
fixed edge sign. The input is the supplied target point. On every checked
nonzero rational point, exact evaluation gives f'(x(P)) = y(phi(P))/y(P).

#figure(image("isogeny_derivative_character.svg", width: 45%), caption: [Mechanism and exact falsifier. The derivative gives a compact point predicate, but the scalar-character identity fails.])

#figure(image("isogeny_derivative_character_agreement.png", width: 96%), caption: [Best global-sign agreement. Every bar is an exhaustive finite subgroup census, with no sampling interval.])

All five screened edges fail an exact identity under either global sign.
The p=1009 degree-5 edge is the existing same-order horizontal control;
its best agreement is 550/1068. The p=47 D=-19 degree-5 edges each give
32/60, and its degree-7 edges give 34/60 and 36/60. These values are not
predictive accuracy: the sign was chosen after inspection. The result
falsifies this exact predicate on the stated curves, not other isogeny
compositions or P-192.

Sources and reproduction: `ISOGENY_DERIVATIVE_CHARACTER_SCREEN.md`,
`isogeny_derivative_character_screen.py`,
`isogeny_derivative_character_results.json`, `RAY_LABEL_CHARACTER_GATE.md`,
and `SMOOTH_KERNEL_CHARACTER_SCREEN.md` in this study directory.
