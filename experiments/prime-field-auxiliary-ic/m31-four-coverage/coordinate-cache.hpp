#pragma once
#include "side-kernel.hpp"
#include <cstdlib>
#include <vector>

// Cache a declared working set of 1024 batches. An absent key recomputes the batch.
struct CoordinateCache {
    static constexpr unsigned capacity=1u<<17;
    std::vector<uint32_t> slots=std::vector<uint32_t>(capacity,p);
    unsigned probe(uint32_t key) const {
        unsigned i=(key*2654435761u)>>(32-17);
        while ((slots[i]&p)!=key && slots[i]!=p) i=(i+1)&(capacity-1);
        return i;
    }
    explicit CoordinateCache(const std::vector<Batch>& inputs) {
        if(inputs.size()>capacity/64) std::abort();
        for(const auto& batch:inputs) {
            auto labels=classify<3>(batch);
            for(unsigned j=0;j<32;++j)
                slots[probe(batch[j])]=batch[j]|(uint32_t(labels[j])<<31);
        }
    }
    Labels lookup(const Batch& batch) const {
        Labels labels{};
        for(unsigned j=0;j<32;++j) {
            uint32_t word=slots[probe(batch[j])];
            if(word==p) return classify<3>(batch);
            labels[j]=word>>31;
        }
        return labels;
    }
};
