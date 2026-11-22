import Mathlib
theorem earlyReject32 (prefixHits prefixMiss restHits restMiss threshold : ℕ)
    (size : prefixHits + prefixMiss + restHits + restMiss = 32)
    (miss : prefixMiss + threshold > 32) : prefixHits + restHits < threshold := by omega
