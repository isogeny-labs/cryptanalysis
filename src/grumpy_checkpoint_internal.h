/* Existing CAGRMP01 wire layout, shared with format controls. */
#ifndef CA_GRUMPY_CHECKPOINT_INTERNAL_H
#define CA_GRUMPY_CHECKPOINT_INTERNAL_H
#include <stdint.h>

typedef struct grumpy_checkpoint_header {
    char magic[8];
    uint64_t p, a, b, order, cofactor;
    uint64_t base[4], target[4], lo, hi, m;
    uint32_t kind, endo_kind, aut_order, entry_size;
    uint64_t endo_lambda, endo_c_mont;
    uint64_t next_i, ops, entries, result;
    double elapsed_seconds;
    uint32_t solved;
    uint64_t checksum;
} grumpy_checkpoint_header;

#endif
