/* Frozen HEAD trial_factor before inverse arithmetic; see receipt.json. */
static int trial_factor_reference(uint64_t v, const uint32_t *fb, uint32_t nfb, uint32_t col0,
                        relation *rel, uint32_t *cnt)
{
    uint32_t n = *cnt;
    for (uint32_t i = 0; i < nfb && v > 1; i++) {
        uint32_t q = fb[i];
        if ((uint64_t)q * q > v) {
            /* v is prime: in the base iff <= fb[nfb-1] */
            if (v <= fb[nfb - 1]) {
                /* find index by binary search */
                uint32_t lo = i, hi = nfb;
                while (lo < hi) {
                    uint32_t mid = (lo + hi) / 2;
                    if (fb[mid] < v) lo = mid + 1; else hi = mid;
                }
                if (lo < nfb && fb[lo] == v) {
                    if (n >= IC_MAX_REL_COLS) return 0;
                    rel->col[n] = col0 + lo;
                    rel->val[n] = 1;
                    n++;
                    v = 1;
                    break;
                }
            }
            *cnt = n;
            return 0;
        }
        if (v % q == 0) {
            int32_t e = 0;
            do { v /= q; e++; } while (v % q == 0);
            if (n >= IC_MAX_REL_COLS) return 0;
            rel->col[n] = col0 + i;
            rel->val[n] = e;
            n++;
        }
    }
    *cnt = n;
    return v == 1;
}

