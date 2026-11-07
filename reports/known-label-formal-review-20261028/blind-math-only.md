# Independent algebra brief

You own J1 for TASK-20261028-32bc7d. Work from this file alone and your own
mathematical reasoning. Do not read the producer repository, source, reports,
review plan, receipts, commit history, memory, siblings, or external commentary.
There is no Git tree to inspect in your minimal input directory.

Let K be any commutative ring, with a,b,c in K. Define
s1=a+b-c, s2=a^2+b^2-c^2, s3=a^3+b^3-c^3.
Independently expand and simplify or factor:
1. (a+b)-(b+c)+(c+a)
2. s1^2-s2
3. -s1^3+3*s1*s2-2*s3
4. s1^2-s2+2*c*s1.
Give a derivation, not just numeric agreement. State whether zero rings,
characteristics 2 and 3, and zero divisors require exclusions for the
identities themselves. Separately test the stronger implication
2*a=2*b implies a=b, and division by (a-c)*(b-c), in those settings;
give explicit known-false counterexamples where appropriate.

Do not run a Lean/Mathlib build, benchmark, cloud job, or experiment. A small
exact symbolic or integer arithmetic calculation is allowed as a diagnostic,
not as a proof. Write report.md and attestation.json only in your assigned
output directory; list all actual reads and commands. Attestation top-level
review_attestation: task_id, joints_owned:[J1], sources_read:[],
read_sibling_reports:false, blind_from_respected:true, verdict holds/breaks/
inconclusive. Report actual deviations honestly. Claim only your joint.
