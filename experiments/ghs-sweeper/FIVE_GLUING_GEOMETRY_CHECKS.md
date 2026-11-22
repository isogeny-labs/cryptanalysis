# Five-gluing geometric screen, frozen 2026-10-25

This is a second, prospectively frozen exact check. It follows the completed
module census; it is not a retroactive protocol for that census.

Inputs: all 126 full-absolute-degree b in F512 (modulus 515) whose a=0/1
twists have trace nonzero modulo 3 and congruent to 2 or 3 modulo 5.
The first census found exactly 252 such source models. Evaluate j=1/b and
y=j^8, then Phi3(j,y), Phi5(j,y), Phi3(j^2,y), Phi3(j,y^2). Also exclude
equal j and Frobenius-distance one or two (degrees 1,2,4). Every evaluation
and order must agree using log-table and raw polynomial multiplication.
These arithmetic paths share the screening logic; no external reviewer
certificate is implied. Survivor count is unknown before this run.

The retained Sutherland integer fixtures must reduce to the exact binary
polynomials used by the checker, reflecting off-diagonal terms. Reject
known modular neighbors found on the fixed b=24 / Phi3 and b=48 / Phi5
curves, and equal, square and fourth-power j controls. Preserve failed
assertions and actual commands/statuses. Run all release tests and Clippy.

The accompanying written proof explains why these predicates suffice to
exclude all geometric degrees 1 through 6, why that makes the five-gluing
quotient indecomposable, and what arithmetic Torelli does and does not give.
Any passing row remains a **twist pair with an existence implication**, not
an evaluated attack. No target equation, selected twist, point map or
planted log may be asserted. All historical models and source classes remain
subject to the old prior-art checks; this does not establish novelty.
