/* Full-field certificate for y^2 = x^3 + 2x + 14 over F_(2^31-1).
 * Build with cc -O3 -std=c11 xor_period.c -o xor_period and run locally.
 * Only the count, checksum and one separating pair leave the process.
 */
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define P UINT32_C(2147483647)

static unsigned lifts(uint32_t x, const uint64_t *squares) {
    uint64_t xx = (uint64_t)x * x % P;
    uint32_t rhs = (xx * x + 2ULL * x + 14) % P;
    return (unsigned)((squares[rhs / 64] >> (rhs % 64)) & 1);
}

int main(void) {
    uint64_t *squares = calloc((size_t)P / 64 + 1, sizeof(*squares));
    if (!squares) return EXIT_FAILURE;
    for (uint32_t y = 0; y <= P / 2; ++y) {
        uint32_t square = (uint64_t)y * y % P;
        squares[square / 64] |= UINT64_C(1) << (square % 64);
    }

    uint32_t count = 0, checksum = 0;
    for (uint32_t x = 0; x < P; ++x) {
        if (lifts(x, squares)) {
            ++count;
            checksum ^= x;
        }
    }
    printf("liftable=%" PRIu32 " xor=%" PRIu32 "\n", count, checksum);
    /* An XOR period partitions an invariant set into pairs. The unused word
     * P must be rejected since adding it gives odd cardinality. With an odd
     * number of pairs, the XOR of the whole set equals their common period. */
    if (count != 1073752646 || checksum == 0) {
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
