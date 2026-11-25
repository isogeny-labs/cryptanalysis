#include "dot-kernel.hpp"
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <random>
#include <string>
#include <vector>

constexpr size_t rows = 4096;

template<class Input>
void traverse(const Input* a, const Input* b, Word* out, size_t terms, size_t uses) {
    for (size_t k=0; k<uses; ++k) {
        for (size_t r=0; r<rows; ++r) {
            size_t other = (r+37*k)%rows;
            out[k*rows+r] = dot<true>(a+r*terms,b+other*terms,terms);
        }
    }
}

int main(int argc, char** argv) {
    if (argc!=2 && !(argc==3 && std::string(argv[2])=="refine")) return 1;
    std::mt19937 rng(std::stoul(argv[1]));
    std::puts("terms,uses,round,arm,ns_per_dot");
    for (size_t n : {17,64,128}) {
        std::vector<uint64_t> a(rows*n), b(rows*n);
        std::vector<Word> ap(rows*n), bp(rows*n);
        for (size_t i=0; i<a.size(); ++i) {
            a[i]=i<n?p-1:rng()%p;
            b[i]=i<n?p-1:rng()%p;
        }
        std::vector<size_t> counts{1,2,4,8,16};
        if (argc==3) counts = n==17 ? std::vector<size_t>{8,10,12,14,16}
                                    : std::vector<size_t>{2,3,4};
        for (size_t uses : counts) {
            std::vector<Word> expected(rows*uses), out(expected.size());
            for (size_t k=0;k<uses;++k) for (size_t r=0;r<rows;++r) {
                __uint128_t sum=0;
                for (size_t i=0;i<n;++i) sum+=a[r*n+i]*b[((r+37*k)%rows)*n+i];
                expected[k*rows+r]=sum%p;
            }
            for (int round=0;round<12;++round) for (int j=0;j<2;++j) {
                bool pack=(round+j)%2;
                auto start=std::chrono::steady_clock::now();
                if (pack) {
                    std::copy(a.begin(),a.end(),ap.begin());
                    std::copy(b.begin(),b.end(),bp.begin());
                    traverse(ap.data(),bp.data(),out.data(),n,uses);
                } else traverse(a.data(),b.data(),out.data(),n,uses);
                double ns=std::chrono::duration<double,std::nano>(std::chrono::steady_clock::now()-start).count();
                if (out!=expected) return 2;
                if (round>=4) std::printf("%zu,%zu,%d,%s,%.4f\n",n,uses,round-4,
                    pack?"pack":"wide",ns/out.size());
            }
        }
    }
}
