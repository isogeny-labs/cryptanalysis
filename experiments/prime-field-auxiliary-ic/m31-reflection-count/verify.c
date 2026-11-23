#include "../m31-boolean-lifts/lift_table.h"
#include <inttypes.h>
#include <stdio.h>

static uint32_t mixed_pairs(uint32_t center, const uint64_t *squares) {
    uint32_t mixed = 0;
    for (uint32_t offset = 1; offset <= P / 2; ++offset) {
        uint32_t left = (center + offset) % P;
        uint32_t right = (center + P - offset) % P;
        mixed += lifts(left, squares) != lifts(right, squares);
    }
    return mixed;
}

int main(void) {
    uint64_t *squares = square_table();
    if (!squares) return EXIT_FAILURE;
    const uint32_t centers[] = {0, 1431655765, 1900239952};
    const uint32_t expected[] = {536844426, 536834928, 536908419};
    int status = EXIT_SUCCESS;
    for (size_t i = 0; i < sizeof(centers) / sizeof(centers[0]); ++i) {
        uint32_t mixed = mixed_pairs(centers[i], squares);
        printf("center=%" PRIu32 " mixed pairs=%" PRIu32 "\n", centers[i], mixed);
        if (mixed != expected[i]) status = EXIT_FAILURE;
    }
    free(squares);
    return status;
}
