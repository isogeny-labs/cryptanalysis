// All XOR directions by exact Walsh autocorrelation, then selected two-planes.
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

constexpr unsigned N = 1u << 19;
constexpr unsigned M = 1u << 20;
constexpr unsigned SEED = 898618;

void walsh(std::vector<int64_t>& a) {
    for (unsigned len=1; len<N; len*=2) {
        for (unsigned base=0; base<N; base+=2*len) {
            for (unsigned j=0; j<len; ++j) {
                auto u=a[base+j], v=a[base+j+len];
                a[base+j]=u+v;
                a[base+j+len]=u-v;
            }
        }
    }
}

unsigned code(unsigned x) {
    constexpr unsigned pivot=19; // highest bit of the frozen seed
    return (x & ((1u<<pivot)-1)) | ((x>>(pivot+1))<<pivot);
}

int main(int argc, char** argv) {
    try {
        if (argc!=2) throw std::runtime_error("usage: affine support_w20.tsv");
        auto start=std::chrono::steady_clock::now();
        std::vector<int> col(M,-1);
        std::ifstream in(argv[1]);
        if (!in) throw std::runtime_error("cannot open source");
        unsigned mask,column,shift,rows=0;
        while (in>>mask>>column>>shift) {
            if (mask>=M || col[mask]!=-1) throw std::runtime_error("bad support row");
            col[mask]=int(column); ++rows;
        }
        std::vector<uint8_t> valid(N,0);
        std::vector<unsigned> codes;
        for (unsigned a=0; a<M; ++a) {
            unsigned b=a^SEED;
            if (a<b && col[a]>=0 && col[b]>=0 && col[a]!=col[b]) {
                unsigned c=code(a);
                if (valid[c]) throw std::runtime_error("duplicate code");
                valid[c]=1; codes.push_back(c);
            }
        }
        if (codes.size()!=132045) throw std::runtime_error("source count");
        std::cout << "SOURCE " << rows << " " << codes.size() << "\n";
        std::vector<int64_t> autocorr(N);
        for (unsigned i=0; i<N; ++i) autocorr[i]=valid[i];
        walsh(autocorr);
        for (auto& value:autocorr) value*=value;
        walsh(autocorr);
        for (auto& value:autocorr) {
            if (value%N) throw std::runtime_error("nonintegral correlation");
            value/=N;
        }
        if (autocorr[0]!=int64_t(codes.size())) throw std::runtime_error("zero shift");
        std::vector<unsigned> directions;
        for (unsigned d=1; d<N; ++d) {
            if (autocorr[d]<0 || autocorr[d]>int64_t(codes.size()) || (autocorr[d]&1))
                throw std::runtime_error("bad correlation");
            directions.push_back(d);
        }
        std::sort(directions.begin(),directions.end(),[&](unsigned a,unsigned b){
            if (autocorr[a]!=autocorr[b]) return autocorr[a]>autocorr[b];
            return a<b;
        });
        std::cout << "BEST_LINE " << directions[0] << " " << autocorr[directions[0]]
                  << " " << codes.size()-autocorr[directions[0]]/2 << "\n";
        for (unsigned j=0; j<64; ++j)
            std::cout << "TOP_LINE " << j << " " << directions[j] << " "
                      << autocorr[directions[j]] << "\n";
        std::vector<uint32_t> seen(N,0);
        unsigned generation=0, best_size=N+1, best_a=0,best_b=0;
        unsigned pairs=0;
        for (unsigned i=0; i<64; ++i) for (unsigned j=i+1; j<64; ++j) {
            unsigned a=directions[i],b=directions[j],ab=a^b;
            // Distinct nonzero directions span exactly one affine two-plane.
            if (!ab) throw std::runtime_error("dependent directions");
            ++generation;
            unsigned nonempty=0;
            for (unsigned c:codes) {
                unsigned base=std::min(std::min(c,c^a),std::min(c^b,c^ab));
                if (seen[base]!=generation) {seen[base]=generation; ++nonempty;}
            }
            if (nonempty<best_size || (nonempty==best_size && std::pair(a,b)<std::pair(best_a,best_b))) {
                best_size=nonempty; best_a=a; best_b=b;
            }
        }
        if (pairs!=2016) throw std::runtime_error("pair count");
        std::cout << "BEST_PLANE " << pairs << " " << best_a << " " << best_b
                  << " " << best_size << "\n";
        std::cout << "DONE " << std::chrono::duration<double>(
            std::chrono::steady_clock::now()-start).count() << "\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << e.what() << "\n";
        return 1;
    }
}
