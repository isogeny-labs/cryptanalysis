#include "kernel.hpp"
#include "root.h"

template<bool balanced, unsigned chains>
void fixed(const Word* input, Word* output) {
    m31root::scheduled<balanced, chains>(input, output, count);
}

void abi(const Word* input, Word* output) {
    m31_checked_roots(input, output, count);
}

int main(int argc, char** argv) {
    if (argc != 2) return 2;
    unsigned seed = std::stoul(argv[1]);
    std::mt19937 rng(seed);
    std::vector<Word> input(count), expected(count), output(count);
    constexpr std::array arms = {roots<2>, fixed<false,1>, fixed<false,8>,
                                 fixed<true,1>, abi};
    // All positions balanced in both forward and reverse cyclic orders.
    std::puts("seed,block,position,arm,elapsed_ns");
    for (unsigned block=0; block<30; ++block) {
        for (auto& x : input) x = rng() % prime;
        input[0]=0; input[1]=1; input[2]=prime-1; input[3]=prime-2;
        std::transform(input.begin(),input.end(),expected.begin(),oracle);
        for (const auto arm : arms) {
            arm(input.data(),output.data());
            if (output != expected) return 3;
        }
        for (unsigned pos=0; pos<arms.size(); ++pos) {
            unsigned arm = (block + (block/5%2 ? 5-pos : pos)) % 5;
            const auto start = std::chrono::steady_clock::now();
            for (unsigned rep=0; rep<32; ++rep) {
                arms[arm](input.data(),output.data());
                asm volatile("" : : "r"(output.data()) : "memory");
            }
            const auto ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
                std::chrono::steady_clock::now()-start).count();
            if (output != expected) return 4;
            std::printf("%u,%u,%u,%u,%lld\n",seed,block,pos,arm,static_cast<long long>(ns));
        }
    }
}
