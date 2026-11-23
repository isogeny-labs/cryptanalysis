#include "orbit.hpp"
#include <cassert>
#include <random>

using namespace orbit_simd;

static bool reference(uint64_t x) {
    uint64_t power=1;
    for (uint32_t e=(modulus-1)/2; e; e>>=1) {
        if (e&1) power=power*x%modulus;
        x=x*x%modulus;
    }
    return power!=modulus-1;
}

int main() {
    std::mt19937 rng(20261122);
    for (unsigned trial=0; trial<1024; ++trial) {
        uint32_t seed=trial==0 ? 1 : trial==1 ? modulus-1 : 1+rng()%(modulus-1);
        uint64_t x=seed, expected_e=0, expected_l=0;
        for (unsigned j=0; j<31; ++j) {
            uint64_t xx=x*x%modulus;
            bool accepted=!reference((xx+1)%modulus);
            expected_e+=accepted;
            expected_l+=accepted && reference((xx*x+2*x+14)%modulus);
            x=2*x%modulus;
        }
        for (bool carry : {false,true}) {
            uint64_t e=0,l=0;
            if (carry) classify<true>(seed,e,l);
            else classify<false>(seed,e,l);
            assert(e==expected_e && l==expected_l);
        }
        uint32_t data[32];
        for (auto& v : data) v=rng()%modulus;
        data[0]=0; data[1]=1; data[2]=modulus-1;
        V inputs[8], masks[8];
        for (unsigned i=0;i<8;++i) inputs[i]=vld1q_u32(data+4*i);
        square_masks(inputs,masks);
        for (unsigned i=0;i<8;++i) {
            uint32_t flags[4]; vst1q_u32(flags,masks[i]);
            for (unsigned j=0;j<4;++j)
                assert((flags[j]!=0)==reference(data[4*i+j]));
        }
    }
}
