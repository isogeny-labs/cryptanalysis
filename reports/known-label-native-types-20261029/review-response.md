# Independent workflow review and repair status

The immutable review of a2aa1586df54ca0250e30e88c544fa549c456fc9 found two blocking evidence defects. Its original report, attestation and six sealed artifacts are preserved under reviewers/TASK-20261029-b339cc, with all attested hashes verified before archival.

## F1: native diagnostics and failure retention

The candidate repair retains original stdout/stderr bytes, argv, cwd, timeout, return code, gate source hash, GitHub source identity and LEAN_PATH before command validation. Timeouts retain available partial output and explicitly have an unknown return code. Generated type wrappers and zero-exit type output are saved outside disposable build directories before parsing. The corpus workflow uploads the diagnostic directory with always(), including failed builds.

The 35 Python controls pass, including an actual child exiting 7 with non-UTF8 stdout and 4000-byte stderr, a simulated timeout, and malformed zero-exit type output surviving temporary-directory cleanup. These are instrumentation controls, not native Lean proof evidence. Hosted artifact retention and independent repaired-snapshot review remain pending.

## F2: auditor and compiled module binding

OPEN. The initial candidate does not yet bind runtime auditor bytes and the produced compiled module across audit and type collection. Do not treat source/pin before-and-after hashes as immutable execution isolation or evidence that transient changes are detected. Lean executable, dependency binaries/cache and runner integrity remain trusted. The next scoped change must bind the auditor and compiled artifact and add mutation/refusal controls before approval.

The original report/PDF/bindings and original unit log describe the earlier candidate and are preserved. No theorem source or toolchain pin changed. No new native build or experiment was run locally.
