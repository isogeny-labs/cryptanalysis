/* Full-field certificate for y^2 = x^3 + 2x + 14 over F_(2^31-1).
 * Build with cc -O3 -std=c11 xor_period.c -o xor_period and run locally.
 * The bit-2-zero count supplies the numerical hypothesis of Degree.lean.
 */
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "lift_table.h"

int main(void) {
    uint64_t *squares = square_table();
    if (!squares) return EXIT_FAILURE;
    uint32_t count = 0, checksum = 0, bit2_zero_count = 0;
    for (uint32_t x = 0; x < P; ++x) {
        if (lifts(x, squares)) {
            ++count;
            checksum ^= x;
            bit2_zero_count += (x & UINT32_C(4)) == 0;
        }
    }
    printf("liftable=%" PRIu32 " xor=%" PRIu32 "\n", count, checksum);
    printf("bit2_zero_liftable=%" PRIu32 "\n", bit2_zero_count);
    /* An XOR period partitions an invariant set into pairs. The unused word
     * P must be rejected since adding it gives odd cardinality. With an odd
     * number of pairs, the XOR of the whole set equals their common period. */
    if (count != 1073752646 || checksum != 1602806244 || bit2_zero_count != 536874593) {
        free(squares);
        return EXIT_FAILURE;
    }
    for (uint32_t x = 0; x < P; ++x) {
        uint32_t other = x ^ checksum;
        if (other < P && lifts(x, squares) != lifts(other, squares)) {
            printf("witness=%" PRIu32 ",%" PRIu32 " labels=%u,%u\n",
                   x, other, lifts(x, squares), lifts(other, squares));
            free(squares);
            return EXIT_SUCCESS;
        }
    }
    free(squares);
    return EXIT_FAILURE;
}
