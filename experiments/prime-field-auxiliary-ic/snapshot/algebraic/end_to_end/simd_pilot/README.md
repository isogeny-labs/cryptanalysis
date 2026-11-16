These are preliminary SIMD runs that permitted repeated or sign-reversed
relation rows. Their certificates are valid, but a recovery could cancel two
copies of the same row. The final experiment rejects those rows and requires
at least three distinct rows in every recovery certificate. These pilot times
are excluded from the final comparison. A partial seed-one run was stopped
when strengthening that protocol. `native_ic.cpp` preserves the pilot source.
