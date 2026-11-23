#include "../m31-boolean-lifts/lift_table.h"
#include <inttypes.h>
#include <stdio.h>

int main(void) {
    uint64_t *squares = square_table();
    if (!squares) return EXIT_FAILURE;
    uint32_t mixed = 0;
    for (uint32_t x = 1; x <= P / 2; ++x)
        mixed += lifts(x, squares) != lifts(P - x, squares);
    free(squares);
    printf("mixed pairs=%" PRIu32 "\n", mixed);
    return mixed == UINT32_C(536844426) ? EXIT_SUCCESS : EXIT_FAILURE;
}
