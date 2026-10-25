/* Export actual inline functions; do not transcribe their implementations. */
#include "cryptanalysis/ca_modarith.h"

uint64_t assay_ca_addmod(uint64_t a, uint64_t b, uint64_t m)
{
    return ca_addmod(a, b, m);
}

uint64_t assay_ca_submod(uint64_t a, uint64_t b, uint64_t m)
{
    return ca_submod(a, b, m);
}
