# Follow-up: trace-derived known-label base versus matched generic growth

Exploratory, fixed after the four primary field cells and their independent
replay. The largest f=6 target failed the frozen 256-shift two-sum cap. Keep
that failure. On that same p=1,032,607, r=206,477 field and the same public Q,
test whether an explicitly labeled larger base repairs the target connection.
This is not a fresh-target holdout or a performance claim.

Recompute degree-2,3,5,7 fibers on the frozen 64 points. Compute actual
Frobenius orbit traces and quotient-ring curve checks. Independently measure
the constraints on the original 32 folded columns by eliminating all new
trace columns: rank([A_old A_new])-rank(A_new). Do not mistake full rank
growth for constraints on original logs.

For each squarefree fiber with exactly one nonlinear irreducible factor and
all rational neighbor labels already in the original base, derive the missing
orbit-trace point and its label from a_l P minus the rational neighbors. Verify
against the actual computed extension trace. Keep every duplicate and failed
eligibility count; never introduce a new generic base-log query for this growth.
Skip fibers with more than one unknown orbit. Count actual group-addition calls
for the derivation separately from extension construction and verification.

Compare with generic base growth using exactly that many point additions:
for counter i, choose a pair of points from the same fixed signed original
base using SHA-256('generic-growth-v1/'+str(i)) modulo the base size for each
index. Add each pair once, including duplicates, and propagate its known label.
Neither arm changes the original generic log bootstrap or target Q.

For original, trace-grown and generic-grown bases, use the same signed two-sum
index and offsets0..255, stopping at first success. Record base size, index
size, group counters, failure/success and independent scalar replay; index
construction is charged setup. No timing ratio is qualified; the geometric
fiber-construction cost is additional, not free. Independently verify every
new label and returned target scalar using the separate short-model verifier.
Cap600 seconds, one process, same memory and checkpoint rules as the primary
protocol. Publish all outcomes, including a generic arm outperforming traces.

If the larger base recovers Q, this establishes a finite target connection
after the charged generic bootstrap; it does not establish scalable descent.
If generic growth explains it, pursue fewer required generic bootstrap logs
or cheaper geometric row construction, rather than advertise a Hecke online win.
