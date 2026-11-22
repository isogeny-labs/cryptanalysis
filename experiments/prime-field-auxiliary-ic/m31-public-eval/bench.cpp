#include <algorithm>
#include <array>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <random>

using U = uint64_t;
extern "C" void* chain_create(const U*, size_t, const U*, size_t, U, U, U);
extern "C" size_t chain_candidates(void*, U, U*);
extern "C" void chain_values(void*, U*);
extern "C" void chain_free(void*);

int main() {
    const U frozen[] = {3,98625645,308768278,536276641,753804470,975624154,985108144,1171458932,1213058799,1393679185,1685732321,1760557235,1896314920,1900239952,1900319349,1908835095,2084456163};
    const U dense[] = {1878924967,758188976,1846538141,407139822,878910144,780848845,2139669403,1253556569,793577623,58074013,1555830891,547091187,2011009199,716239208,1270523019,972044777,509907442,1165892079,1682260252,220539160};
    const U maps[] = {0,0,1,2,6,8,262150,786438,3145792,135006214,403445766,562160130,199756251,1939860868,1327400300};
    void* models[] = {chain_create(frozen,17,maps,5,1569594640,2,14),
                      chain_create(dense,17,maps,5,308674601,2,14),
                      chain_create(dense,20,maps,5,308674601,2,14)};
    for (auto model : models) assert(model);
    std::array<U,8192> inputs{};
    std::mt19937_64 rng(291147);
    U indices[20], values[3][20]{}, hash=0;
    for (int block=-1; block<36; ++block) {
        for (U& x : inputs) x=rng()%2147483647;
        if (block<0) {
            for (U x : inputs) {
                for (int arm=0; arm<3; ++arm) {
                    chain_candidates(models[arm],x,indices);
                    chain_values(models[arm],values[arm]);
                    for (int j=0; j<(arm==2?20:17); ++j)
                        hash=hash*1099511628211ULL+values[arm][j];
                }
                assert(std::equal(values[1],values[1]+17,values[2]));
            }
            std::cerr<<"verification checksum "<<hash<<"\n";
            continue;
        }
        constexpr int orders[][3]={{0,1,2},{0,2,1},{1,2,0},{1,0,2},{2,0,1},{2,1,0}};
        for (int arm : orders[block%6]) {
            U hits=0;
            auto start=std::chrono::steady_clock::now();
            for (U x : inputs) hits+=chain_candidates(models[arm],x,indices);
            auto ns=std::chrono::duration_cast<std::chrono::nanoseconds>(
                std::chrono::steady_clock::now()-start).count();
            std::cout<<block<<','<<arm<<','<<ns<<','<<hits<<'\n';
        }
    }
    for (auto model : models) chain_free(model);
}
