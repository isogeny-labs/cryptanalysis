#include "dlog_internal.h"
#include <stdio.h>
int main(void)
{
    uint64_t n = UINT64_MAX - 58, x = 0, lo = n + 1, hi = UINT64_MAX;
    int ok = ca_fit_interval(n, &x, lo, hi);
    printf("ok=%d x=%llu lo=%llu hi=%llu in_interval=%d\n", ok, (unsigned long long)x,
           (unsigned long long)lo, (unsigned long long)hi, x >= lo && x <= hi);
    return 0;
}
