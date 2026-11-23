#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <string>
#include <stdexcept>
#include <vector>
#include <map>
#include <random>
#include <unordered_map>

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
template<bool reduced, bool weighted=false, class Record>
void visit(Point a,unsigned start,unsigned left,Record& record,
           unsigned used=1,unsigned run=1,unsigned ways=1) {
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
        if constexpr (weighted) {
            unsigned next_run=i==start ? run+1 : 1;
            unsigned permutations=ways*(used+1)/next_run;
            if(left>1) visit<reduced,true>(next,i,left-1,record,used+1,next_run,permutations);
            else record(next.x,permutations);
        } else {
            if(left>1) visit<reduced>(next,i,left-1,record);
            else record(next.x);
        }
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
static std::uint64_t extend_ball(Bits& total, Word anchor) {
    auto it=std::find_if(basis.begin(),basis.end(),[&](Point a){return a.x==anchor;});
    assert(it!=basis.end());
    auto record=[&](Word x) {
        if(x!=p) total[x>>6]|=UINT64_C(1)<<(x&63);
    };
    record(anchor);
    for(unsigned n=1;n<=4;++n) visit<false>(*it,0,n,record);
    std::uint64_t finite=0;
    for(auto word:total) finite+=2ULL*__builtin_popcountll(word);
    return finite;
}

static void translated(const std::vector<Word>& xs, Word anchor) {
    Bits total=census(xs,-1,{});
    std::cout<<"translated_union_finite,"<<extend_ball(total,anchor)<<std::endl;
}

// Independently classify all canonical abscissae by quadratic residuosity.
// Build squares by first differences, then evaluate the cubic by third
// differences; this check uses no elliptic-curve addition or inversion.
static void check_full_curve(const Bits& total) {
    Bits squares(total.size());
    Word square=0, delta=1;
    for(Word y=0;y<=p/2;++y) {
        squares[square>>6]|=UINT64_C(1)<<(square&63);
        square=add(square,delta);
        delta=add(delta,2);
    }
    Word rhs=14, diff=3, second=6;
    for(Word x=0;x<p;++x) {
        bool covered=(total[x>>6]>>(x&63))&1;
        bool lifts=(squares[rhs>>6]>>(rhs&63))&1;
        if(covered!=lifts) throw std::runtime_error("curve support mismatch");
        rhs=add(rhs,diff);
        diff=add(diff,second);
        second=add(second,6);
    }
}

static void five_cover(std::vector<Word> xs, bool reverse) {
    const auto anchors=xs;
    if(reverse) std::reverse(xs.begin(),xs.end());
    Bits total=census(xs,-1,{});
    std::cout<<"anchor_ordinal,anchor_x,finite_points"<<std::endl;
    for (std::size_t i=0;i<anchors.size();++i) {
        auto finite=extend_ball(total,anchors[i]);
        std::cout<<i+1<<','<<anchors[i]<<','<<finite<<std::endl;
        if (finite==UINT64_C(2147505292)) {
            check_full_curve(total);
            std::cerr<<"Verified all "<<p<<" abscissae against the curve cubic."<<std::endl;
            break;
        }
    }
}

// Histogram of the number of ordered length-four walks ending at each
// group point. Store one count per pair of opposite finite points.
// Rejection from 32-bit encodings gives each affine point and the identity
// one accepted encoding. The published curve has no affine point with y=0.
static Point sample_group(std::mt19937& rng) {
    for (;;) {
        Word code=rng(), x=code>>1;
        if(x==p) {
            if(!(code&1)) return infinity;
            continue;
        }
        Word rhs=add(add(mul(mul(x,x),x),add(x,x)),14);
        Word y=power(rhs,(p+1u)/4);
        if(mul(y,y)!=rhs || (!y && (code&1))) continue;
        return {x,(code&1) ? sub(0,y) : y};
    }
}

static void sample_walks(const std::vector<std::uint8_t>& counts,
                         const std::unordered_map<Word,std::uint64_t>& overflow,
                         std::uint64_t identity) {
    constexpr std::uint64_t order=2147505293;
    constexpr unsigned samples=65536;
    const std::uint64_t degree=basis.size();
    const auto paths4=degree*degree*degree*degree, paths5=degree*paths4;
    auto paths_at=[&](Word x) -> std::uint64_t {
        if(x==p) return identity;
        if(counts[x]!=255) return counts[x];
        auto it=overflow.find(x);
        return 255+(it==overflow.end()?0:it->second);
    };
    auto five_at=[&](Point g) {
        std::uint64_t sum=0;
        auto accumulate=[&](Word x){sum+=paths_at(x);};
        visit<false>(g,0,1,accumulate);
        return sum;
    };
    const auto five_return=five_at(infinity);
    std::uint64_t six_return=0;
    for(Point step:basis) six_return+=five_at(step);
    auto deficit=[](std::uint64_t paths,std::uint64_t k) {
        // Test before multiplying so the product fits in 64 bits.
        return k<=paths/order ? paths-k*order : UINT64_C(0);
    };
    std::cout<<"seed,samples,four_deficit_numerator,five_deficit_numerator,five_zero,five_return_paths,six_return_paths"<<std::endl;
    for(Word seed : {31u,211u,390u,195u}) {
        std::mt19937 rng(seed);
        std::uint64_t four=0,five=0,zero=0;
        for(unsigned j=0;j<samples;++j) {
            Point g=sample_group(rng);
            auto k4=paths_at(g.x);
            auto k5=five_at(g);
            four+=deficit(paths4,k4);
            five+=deficit(paths5,k5);
            zero+=k5==0;
        }
        std::cout<<seed<<','<<samples<<','<<four<<','<<five<<','<<zero<<','<<five_return<<','<<six_return<<std::endl;
    }
}

static void walk_histogram(const std::vector<Word>& xs, bool sample) {
    load_basis(xs);
    unsigned m=xs.size();
    std::uint64_t identity=12ULL*m*(m-1)+6ULL*m;
    std::vector<std::uint8_t> counts(p);
    std::unordered_map<Word,std::uint64_t> overflow;
    auto record=[&](Word x,unsigned ways) {
        if(x==p) { identity+=2ULL*ways; return; }
        unsigned sum=counts[x]+ways;
        counts[x]=std::min(sum,255U);
        if(sum>255) overflow[x]+=sum-255;
    };
    // A reduced pair becomes a four-word multiset by inserting one neutral
    // pair. A repeated signed letter and two distinct letters have different
    // numbers of arrangements.
    auto cancelled=[&](Word x,unsigned ways) {
        record(x,ways==1 ? 12*m-8 : 24*(m-1));
    };
    for(unsigned i=0;i<basis.size();i+=2) {
        visit<true,true>(basis[i],i,1,cancelled);
        visit<true,true>(basis[i],i,3,record);
    }
    std::array<std::uint64_t,256> bins{};
    for(auto k:counts) ++bins[k];
    std::map<std::uint64_t,std::uint64_t> hist;
    for(unsigned k=1;k<bins.size();++k)
        if(bins[k]) hist[k]=2*bins[k];
    for(auto entry:overflow) {
        hist[255]-=2;
        hist[255+entry.second]+=2;
    }
    ++hist[identity];
    std::uint64_t covered=0, mass=0;
    for(auto entry:hist) {
        covered+=entry.second;
        mass+=entry.first*entry.second;
    }
    std::uint64_t degree=2*m;
    if(mass!=degree*degree*degree*degree) throw std::runtime_error("four-walk mass mismatch");
    if(sample) {
        sample_walks(counts,overflow,identity);
        return;
    }
    hist[0]=2147505293ULL-covered;
    std::cout<<"ordered_walks,group_points"<<std::endl;
    for(auto entry:hist)
        if(entry.second) std::cout<<entry.first<<','<<entry.second<<'\n';
}

// Count four-letter prefixes up to sign whose endpoint admits a fifth letter.
static void five_prefixes(std::vector<Word> xs) {
    load_basis(xs);
    std::sort(xs.begin(),xs.end());
    if(std::adjacent_find(xs.begin(),xs.end())!=xs.end())
        throw std::invalid_argument("duplicate generator abscissa");
    std::array<bool,65536> suffix{};
    for(Word x:xs) suffix[x & 65535]=true;
    std::array<std::uint64_t,25> hits{};
    auto count=[&](Word x,unsigned ways) {
        if(suffix[x & 65535] && std::binary_search(xs.begin(),xs.end(),x))
            ++hits[ways];
    };
    for(unsigned i=0;i<basis.size();i+=2) visit<true,true>(basis[i],i,3,count);
    std::cout<<"prefix_permutations,completable_prefixes_up_to_sign\n";
    for(unsigned ways:{1,4,6,12,24}) std::cout<<ways<<','<<hits[ways]<<'\n';
}

int main(int argc,char** argv) {
    std::vector<Word> xs;
    Word x;
    while(std::cin>>x) xs.push_back(x);
    if(argc==2 && std::string(argv[1])=="five-prefixes") {
        if(xs.empty() || xs.size()>195) throw std::invalid_argument("invalid basis size");
        five_prefixes(xs);
        return 0;
    }
    if(argc==2 && (std::string(argv[1])=="walk-four" || std::string(argv[1])=="walk-five-sample")) {
        assert(!xs.empty() && xs.size()<=195);
        walk_histogram(xs,std::string(argv[1])=="walk-five-sample");
        return 0;
    }
    if(argc==2 && (std::string(argv[1])=="five" || std::string(argv[1])=="five-reverse")) {
        assert(!xs.empty() && xs.size()<=195);
        five_cover(xs, std::string(argv[1])=="five-reverse");
        return 0;
    }
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
