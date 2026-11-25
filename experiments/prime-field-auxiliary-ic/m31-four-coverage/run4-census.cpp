// Count failures independently using four overlapping rotations and their complements.
#include <cstdint>
#include <cstdio>

constexpr uint32_t prime = 2147483647;
static uint32_t rotate(uint32_t x) { return ((x << 1) & prime) | (x >> 30); }
static bool has_run(uint32_t x) {
    uint32_t y = rotate(x), z = rotate(y), w = rotate(z);
    return ((x & y & z & w) | (prime & ~(x | y | z | w))) != 0;
}

int main() {
    unsigned misses = 0, double_misses = 0;
    // Complement exchanges the two halves and preserves run lengths.
    for (uint32_t x = 1; x <= prime / 2; ++x) {
        if (has_run(x)) continue;
        ++misses;
        if (!has_run(uint64_t(3) * x % prime)) ++double_misses;
    }
    std::printf("nonzero,first_misses,double_misses\n%u,%u,%u\n",
                prime - 1, 2 * misses, 2 * double_misses);
}
