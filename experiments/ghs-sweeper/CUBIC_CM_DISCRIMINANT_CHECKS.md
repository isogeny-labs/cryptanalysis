# CM discriminant refinement, frozen 2026-10-25

The completed first CM screen retained the triangle-feasible degree triples
(8,8,37) and (8,13,32). Preserve its v1 output and source commit 214ebc91.
Add the necessary discriminant condition from the written proof: for three
homomorphisms with sum zero in the same ordinary CM Hom-space, the Heron
quantity is 823 times a rational square, hence is divisible by 823 as an
integer. Its values at these triples are 71,680 and 103,360, respectively.
Expect neither to survive divisibility. The earlier (1,26,26) fails positivity.

Controls: the different sum-37 triple (8,13,16) has H=823*64 and must pass
this arithmetic condition; therefore the rule does not reject everything.
Do not use it to claim 53 is the first prime admitting a kernel: the prior
prime list covered only ell=2 mod 3. Other congruence classes are out of that
list's scope, and the degree-37 control does not decide indecomposability.

Freeze the refined Rust source, written proof and Lean arithmetic source
before running. Check all sorted positive degree triples of sum 53 against
the norm degree rectangle and the nonnegative/divisible discriminant test.
Attempt an ordinary Lean kernel proof of this finite exclusion and a theorem
lifting the bounded exclusion to all sorted natural-number triples. Print
every theorem's axioms; no native-decision or assumed geometric conclusion.
The published elliptic/CM/polarization facts, integer witness bounds and
geometric interpretation remain explicit written bridges, not Lean claims.

A verified arithmetic exclusion plus the written geometric bridges gives
a derived indecomposability implication. It does not reconstruct an isogeny,
identify a particular computed quartic as the quotient, establish publication
priority, or transfer a planted log. Preserve all earlier evidence versions.
