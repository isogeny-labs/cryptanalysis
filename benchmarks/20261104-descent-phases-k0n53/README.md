# k0n53 walked descent: native time by phase (2026-11-04)

Copies for browsing. The study is
[`experiments/descent-phases-k0n53-20261104/`](../../experiments/descent-phases-k0n53-20261104/REPORT.md).

This is a diagnostic, not a speed claim.

| phase | share of native time |
|---|---|
| batched add (`add_many_lazy`) | 38–39% |
| presence-filter probe loop | 34–36% |
| Frobenius key (`keys_of`) | 10–11% |

- **Presence filter:** it admits 12.3% of probed keys, and each admitted
  key pays a slow bucket lookup. [pcc:unverified]
- **Next lever:** cut the filter's false-positive rate. That needs a
  version bump of the serialized filter format.
