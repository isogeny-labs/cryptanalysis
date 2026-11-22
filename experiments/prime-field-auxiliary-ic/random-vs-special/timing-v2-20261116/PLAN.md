# Complete caller and observed-CLI timing boundaries

Baseline: `fcbaca780b038760d6a9f68f692f8ab4e6102080`. This increment corrects
accounting; it does not implement or claim an algorithmic/runtime improvement.
No qualified Rust timing baseline or new benchmark exists. [pcc:unverified]

Keep the requested three-arm random/auxiliary/same-base IC comparison and
optional matched rho reference. Freeze no fresh targets here. Development
checks use only existing public correctness fixtures and scripted durations.

Acceptance for version 2 reports:

- Construct/check the supplied target point after reusable preparation and
  inside the IC online caller interval. Retain the existing core partition
  separately, with input validation and call overhead charged exactly once.
- Include rho's final Rust scalar replay in its online wall interval, while
  keeping its native-only operation count explicitly scoped.
- Partition observed CLI costs into setup, pre-online bookkeeping, online,
  reporting and optional reference; remove reference work from the IC total.
- Leave upstream preparation, process start/exit and independent replay
  unknown; supply no fabricated cold total or qualified ratio.
- Preserve old version 1 reports and their interpretation. Validate both
  formats; refuse mixing formats, wrong units/types, overlaps/gaps and fake
  completeness. Keep replay/decomposition controls outside attack timing.

Controls: deterministic monotonic/nonmonotonic boundary vectors, overflow
refusals, profiled/unprofiled real public fixture outcomes, every bounded stop,
rho success/replay partition, existing scalar/certificate/yield controls,
actual three-arm Rust-to-Python hand-off, legacy and v2 malformed reports,
strict CLI lint/format and stable/1.78 rustdoc. Keep all failed commands with
their exact source and output. This is ordinary development validation, not
a research run or a substitute for the requested 31/61-bit measurements.

Sources checked: the baseline CLI, comparison checker/specification and root
measurement/accounting rules. Existing math, factor bases, core arithmetic,
native consumers and frozen snapshot are unchanged. No new ECDLP mechanism,
prior-art or novelty claim is made. Shared-KB/atlas access limitations remain
as recorded in the preceding field-fiber/engineering reports.

Next discriminating step remains an admitted frozen comparison with complete
upstream/process costs and signed independent replay. The known failed
checkpoint/runner preflight is not retried without changed access.
