// Lokshtanov--Paturi--Tamaki--Williams--Yu, SODA 2017, Lemma 3.3, q=2.
// Bounded reference implementation; exact algorithmic operation counts.
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <random>
#include <vector>

using Poly = std::vector<unsigned>;
struct Counts {
    uint64_t random_bits=0, coefficient_xors=0, monomial_products=0,
             mobius_xors=0, scoreboard_increments=0, suffixes=0;
};

Poly multiply(const Poly& left, const Poly& right, unsigned size, Counts& counts) {
    std::vector<uint8_t> bits(size,0);
    for (unsigned x:left) for (unsigned y:right) {
        bits[x|y] ^= 1;
        ++counts.monomial_products;
    }
    Poly out;
    for (unsigned i=0;i<size;++i) if(bits[i]) out.push_back(i);
    return out;
}

Poly restrict_suffix(const Poly& source,unsigned low,unsigned suffix,Counts& counts) {
    unsigned size=1u<<low;
    std::vector<uint8_t> bits(size,0);
    for(unsigned mon:source) if(((mon>>low)&~suffix)==0) {
        bits[mon&(size-1)]^=1;
        ++counts.coefficient_xors;
    }
    Poly out;
    for(unsigned i=0;i<size;++i) if(bits[i]) out.push_back(i);
    return out;
}

int main() {
    unsigned nv,n0,neq,repeats;
    uint64_t seed;
    if(!(std::cin>>nv>>n0>>neq>>repeats>>seed) || nv<2 || nv>12 || n0<1 || n0>=nv) return 2;
    std::vector<Poly> equations(neq);
    for(auto& polynomial:equations) {
        unsigned size;std::cin>>size;
        for(unsigned j=0;j<size;++j){unsigned mon;std::cin>>mon;if(mon>=(1u<<nv))return 3;polynomial.push_back(mon);}
    }
    std::mt19937_64 rng(seed);
    Counts counts;
    auto bit=[&](){++counts.random_bits;return unsigned(rng()&1);};
    unsigned low=nv-n0,size=1u<<low,ell=n0+2;
    std::vector<std::vector<Poly>> restricted(1u<<n0);
    for(unsigned a=0;a<(1u<<n0);++a)
        for(const auto& equation:equations) restricted[a].push_back(restrict_suffix(equation,low,a,counts));
    std::vector<unsigned> scoreboard(size,0);
    for(unsigned trial=0;trial<repeats;++trial) {
        std::vector<uint8_t> result(size,0);
        for(unsigned suffix=0;suffix<(1u<<n0);++suffix) {
            ++counts.suffixes;
            if(!bit())continue;
            Poly product{0};
            for(unsigned i=0;i<ell;++i) {
                std::vector<uint8_t> mixture(size,0);
                for(const auto& equation:restricted[suffix]) if(bit())
                    for(unsigned mon:equation){mixture[mon]^=1;++counts.coefficient_xors;}
                mixture[0]^=1; // q=2: 1 - sum_j alpha_j P_j.
                ++counts.coefficient_xors;
                Poly complement;
                for(unsigned mon=0;mon<size;++mon)if(mixture[mon])complement.push_back(mon);
                product=multiply(product,complement,size,counts);
                if(product.empty())break;
            }
            for(unsigned mon:product){result[mon]^=1;++counts.coefficient_xors;}
        }
        for(unsigned j=0;j<low;++j)
            for(unsigned mask=0;mask<size;++mask)if(mask&(1u<<j)) {
                result[mask]^=result[mask^(1u<<j)];++counts.mobius_xors;
            }
        for(unsigned y=0;y<size;++y)if(result[y]){++scoreboard[y];++counts.scoreboard_increments;}
        if((trial+1)%100==0)
            std::cerr<<"completed_repetitions="<<trial+1<<" monomial_products="<<counts.monomial_products<<"\n";
    }
    bool feasible=false;unsigned max_score=0;
    for(unsigned score:scoreboard){max_score=std::max(score,max_score);if(5ull*score>=2ull*repeats)feasible=true;}
    std::cout<<"{\"nvars\":"<<nv<<",\"n0\":"<<n0<<",\"ell\":"<<ell
             <<",\"repetitions\":"<<repeats<<",\"seed\":"<<seed
             <<",\"satisfiable\":"<<(feasible?"true":"false")<<",\"maximum_score\":"<<max_score
             <<",\"counts\":{\"random_bits\":"<<counts.random_bits
             <<",\"coefficient_xors\":"<<counts.coefficient_xors
             <<",\"monomial_products\":"<<counts.monomial_products
             <<",\"mobius_xors\":"<<counts.mobius_xors
             <<",\"scoreboard_increments\":"<<counts.scoreboard_increments
             <<",\"suffixes\":"<<counts.suffixes<<"}}\n";
}
