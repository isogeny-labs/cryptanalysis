# Target-bearing relation selection for the nine-point Xedni lift

Date: 2026-11-18

Status: implementation and fresh-seed protocol are frozen at commit
`10a28313a6`; no natural outcome has been generated because the mandatory
resume-checkpoint gate has no upload transport in this environment.  The
access obstruction is tracked in
[`problems/xedni-affine-cvp-checkpoint-access.md`](../../problems/xedni-affine-cvp-checkpoint-access.md).
[pcc:unverified]

The November 17 panel demonstrated exact bounded relations on optimized
plane-cubic lifts, but 44 of 67 selected relations had zero target coefficient.
This follow-up changes only the ordering of exact relation candidates: it tests
invertible target coefficients before minimum weight, while retaining the old
ordering as a paired baseline on the same fresh lift. [pcc:unverified]

See [`PROTOCOL.md`](PROTOCOL.md) for the frozen question, controls, budgets,
acceptance boundary, and exact command. [pcc:unverified]
