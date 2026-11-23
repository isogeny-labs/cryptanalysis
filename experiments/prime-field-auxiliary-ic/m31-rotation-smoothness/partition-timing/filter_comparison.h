// Benchmark extension using the preceding census types and enumeration.
Keys filtered_census(U bound, size_t* surviving = nullptr, size_t* emitted = nullptr) {
    constexpr U mask = (1u << 20) - 1;
    std::vector<uint8_t> seen(mask+1);
    Keys keys, pairs;
    auto emit = [&](U, U k, U inv, bool neg) {
        if (!neg) return;
        U low = std::min(k,inv);
        U orientation = k > inv;
        seen[low & mask] |= uint8_t(1u << orientation);
        keys.push_back(2*low + orientation);
    };
    visit<true>(factors(bound),0,1,1,1,false,emit);
    if (emitted) *emitted = keys.size();
    size_t count = 0;
    for (auto key : keys) {
        keys[count] = key;
        count += seen[(key/2) & mask] == 3;
    }
    keys.resize(count);
    if (surviving) *surviving = count;
    unique_sort(keys);
    for (size_t i=1; i<keys.size(); ++i)
        if ((keys[i-1]^keys[i]) == 1) pairs.push_back(keys[i]/2);
    return pairs;
}

int compare_filters() {
    constexpr int orders[][4] = {{0,1,3,2},{1,2,0,3},{2,3,1,0},{3,0,2,1}};
    std::puts("bound,round,position,arm,ms,pairs,emitted,retained");
    for (U bound : {67,83,89}) {
        auto ref = exhaustive(bound);
        size_t emitted, retained;
        if (filtered_census(bound,&retained,&emitted) != ref) return 1;
        for (int r=0; r<12; ++r) {
            for (int pos=0; pos<4; ++pos) {
                int arm=orders[r%4][pos];
                using Clock=std::chrono::steady_clock;
                auto start=Clock::now();
                Keys out=arm<2 ? exhaustive(bound) : filtered_census(bound);
                double ms=std::chrono::duration<double,std::milli>(Clock::now()-start).count();
                if (out != ref) return 2;
                std::printf("%u,%d,%d,%d,%.6f,%zu,%zu,%zu\n",bound,r,pos,arm,ms,
                            out.size(),emitted,arm<2 ? emitted : retained);
            }
        }
    }
    return 0;
}
