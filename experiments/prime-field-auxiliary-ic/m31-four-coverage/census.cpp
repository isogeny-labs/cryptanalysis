#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <string>
#include <stdexcept>
#include <vector>

using Word = std::uint32_t;
constexpr Word p=2147483647;
struct Point { Word x,y; };
constexpr Point infinity{p,p};
Word add(Word a,Word b) { Word s=a+b; return s>=p?s-p:s; }
Word sub(Word a,Word b) { return a>=b?a-b:p-(b-a); }
Word mul(Word a,Word b) {
    std::uint64_t prod=std::uint64_t(a)*b;
    return add(prod>>31, Word(prod)&p);
}
Word power(Word a,Word e) {
    Word r=1;
    for (;e;e>>=1,a=mul(a,a)) if(e&1) r=mul(r,a);
    return r;
}
std::vector<Point> basis;
using Bits=std::vector<std::uint64_t>;

// Visit sorted signed multisets, including repeats and inverse cancellations.
// Batch all additions at a node, replacing exceptional denominators with one.
template<bool reduced, class Record>
void visit(Point a,unsigned start,unsigned left,Record& record) {
    std::array<Word,390> prefix,den;
    Word prod=1;
    for(unsigned i=start;i<basis.size();++i) {
        const Point b=basis[i];
        Word d=a.x==p?0:(a.x!=b.x?sub(b.x,a.x):(a.y==b.y?add(a.y,a.y):0));
        den[i]=d;
        prefix[i]=prod;
        if(d) prod=mul(prod,d);
    }
    Word inv=power(prod,p-2);
    for(unsigned i=basis.size();i-->start;) {
        const Point b=basis[i];
        Point next;
        if(!den[i]) next=a.x==p?b:infinity;
        else {
            Word numer;
            if(a.x!=b.x) numer=sub(b.y,a.y);
            else {Word xx=mul(a.x,a.x); numer=add(add(xx,add(xx,xx)),2);}
            Word slope=mul(numer,mul(prefix[i],inv));
            inv=mul(inv,den[i]);
            next.x=sub(sub(mul(slope,slope),a.x),b.x);
            if(left>1) next.y=sub(mul(slope,sub(a.x,next.x)),a.y);
        }
        // Sorted occurrences put opposite signs of one generator next to each other.
        if constexpr (reduced) if (i==(start^1U)) continue;
        if(left>1) visit<reduced>(next,i,left-1,record);
        else record(next.x);
    }
}

static void load_basis(const std::vector<Word>& xs) {
    basis.clear();
    for(Word u:xs) {
        assert(u<p);
        Word rhs=add(add(mul(mul(u,u),u),add(u,u)),14);
        Word y=power(rhs,(p+1u)/4);
        assert(y && mul(y,y)==rhs);
        y=std::min(y,p-y);
        basis.push_back({u,y});
        basis.push_back({u,p-y});
    }
}

static Bits census(const std::vector<Word>& xs, int arm, const Bits& reference) {
    load_basis(xs);
    Bits total((std::size_t(p)+63)/64), shell(total.size());
    for(unsigned n=1;n<=4;++n) {
        std::fill(shell.begin(),shell.end(),0);
        bool has_infinity=false;
        auto record = [&](Word x) {
            if(x==p) has_infinity=true;
            else shell[x>>6]|=UINT64_C(1)<<(x&63);
        };
        // Global negation preserves x. An orientation with a positive
        // occurrence of the smallest generator always exists.
        for(unsigned i=0;i<basis.size();i+=2) {
            if(n==1) shell[basis[i].x>>6]|=UINT64_C(1)<<(basis[i].x&63);
            else visit<false>(basis[i],i,n-1,record);
        }
        std::uint64_t exact=0, upto=0;
        for(std::size_t j=0;j<total.size();++j) {
            exact+=__builtin_popcountll(shell[j]);
            total[j]|=shell[j];
            upto+=__builtin_popcountll(total[j]);
        }
        if (arm>=0) std::cout<<arm<<',';
        std::cout<<n<<','<<2*exact<<','<<2*upto<<','<<has_infinity;
        if (arm>=0) {
            if (n==4 && !reference.empty()) {
                std::uint64_t common=0;
                for (std::size_t j=0;j<total.size();++j)
                    common+=__builtin_popcountll(total[j]&reference[j]);
                std::cout<<','<<2*common;
            } else std::cout<<',';
        }
        std::cout<<std::endl;
    }
    return total;
}

// Count one coefficient vector per orientation, merging global signs only.
// Retain aggregate multiplicities, including any nonempty vectors evaluating to zero.
static void multiplicities(const std::vector<Word>& xs) {
    load_basis(xs);
    std::vector<std::uint8_t> packed((std::size_t(p)+1)/2);
    std::uint64_t zero_vectors=1;
    auto record = [&](Word x) {
        if(x==p) { zero_vectors+=2; return; }
        auto& byte=packed[x/2];
        unsigned shift=4*(x%2);
        if(((byte>>shift)&15)==15) throw std::overflow_error("multiplicity exceeds nibble");
        byte+=1U<<shift;
    };
    for(unsigned n=1;n<=4;++n) {
        for(unsigned i=0;i<basis.size();i+=2) {
            if(n==1) record(basis[i].x);
            else visit<true>(basis[i],i,n-1,record);
        }
    }
    std::array<std::uint64_t,16> bins{};
    for(auto byte:packed) {
        ++bins[byte&15];
        ++bins[byte>>4];
    }
    std::cout<<"multiplicity,finite_points,identity_vectors\n";
    for(unsigned k=1;k<bins.size();++k)
        if(bins[k]) std::cout<<k<<','<<2*bins[k]<<','<<zero_vectors<<'\n';
}

// The starting point is a fixed generator. The additional sorted multiset
// may use every sign. Taking both ordinates of a visited x also covers
// the negative starting point because the unshifted ball is symmetric.
static void translated(const std::vector<Word>& xs, Word anchor) {
    Bits total=census(xs,-1,{});
    auto it=std::find_if(basis.begin(),basis.end(),[&](Point a){return a.x==anchor;});
    assert(it!=basis.end());
    auto record=[&](Word x) {
        if(x!=p) total[x>>6]|=UINT64_C(1)<<(x&63);
    };
    record(anchor);
    for(unsigned n=1;n<=4;++n) visit<false>(*it,0,n,record);
    std::uint64_t finite=0;
    for(auto word:total) finite+=2ULL*__builtin_popcountll(word);
    std::cout<<"translated_union_finite,"<<finite<<std::endl;
}

int main(int argc,char** argv) {
    std::vector<Word> xs;
    Word x;
    while(std::cin>>x) xs.push_back(x);
    if(argc==3 && std::string(argv[1])=="translate") {
        assert(!xs.empty() && xs.size()<=195);
        translated(xs,static_cast<Word>(std::stoul(argv[2])));
        return 0;
    }
    if(argc==2 && std::string(argv[1])=="multiplicity") {
        assert(!xs.empty() && xs.size()<=195);
        multiplicities(xs);
        return 0;
    }
    if(argc==2 && std::string(argv[1])=="matched") {
        assert(xs.size()==4*195);
        std::cout<<"arm,arity,exact_finite,upto_finite,exact_has_infinity,common_with_smooth\n";
        Bits reference;
        for (int arm=0;arm<4;++arm) {
            auto begin=xs.begin()+arm*195;
            auto covered=census(std::vector<Word>(begin,begin+195),arm,reference);
            if (!arm) reference.swap(covered);
        }
    } else {
        assert(!xs.empty() && xs.size()<=195);
        if(argc==2 && std::string(argv[1])=="reverse") std::reverse(xs.begin(),xs.end());
        std::cout<<"arity,exact_finite,upto_finite,exact_has_infinity\n";
        census(xs,-1,{});
    }
}
