#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <string>
#include <type_traits>
#include <cstddef>
#include <stdexcept>
#include <vector>
#include <map>
#include <random>
#include <unordered_map>
#include <unordered_set>

using Word = std::uint32_t;
constexpr Word p=2147483647;
struct Point { Word x,y; };
constexpr Point infinity{p,p};
Word add(Word a,Word b) { Word s=a+b; return s>=p?s-p:s; }
Word sub(Word a,Word b) { return a>=b?a-b:p-(b-a); }
// Canonical operands permit a product plus up to 2p in one 64-bit accumulator.
Word fold(std::uint64_t accumulator) {
    return add(Word(accumulator >> 31), Word(accumulator) & p);
}
Word mul(Word a,Word b) { return fold(std::uint64_t(a)*b); }
Word power(Word a,Word e) {
    Word r=1;
    for (;e;e>>=1,a=mul(a,a)) if(e&1) r=mul(r,a);
    return r;
}
// If u = x^(2^k - 1), squaring k times then multiplying by u
// yields x^(2^(2k) - 1). Build blocks of 2, 3, 6, 7, 14, 28, 29 bits.
static Word inverse_nonzero(Word x) {
    auto extend=[](Word u,unsigned k) {
        Word v=u;
        for(unsigned i=0;i<k;++i) v=mul(v,v);
        return mul(v,u);
    };
    Word u=extend(x,1);
    u=mul(mul(u,u),x);
    u=extend(u,3);
    u=mul(mul(u,u),x);
    u=extend(u,7);
    u=extend(u,14);
    u=mul(mul(u,u),x);
    u=mul(u,u);
    return mul(mul(u,u),x);
}
std::vector<Point> basis;
using Bits=std::vector<std::uint64_t>;

// Visit sorted signed multisets, including repeats and inverse cancellations.
// Batch all additions at a node, replacing exceptional denominators with one.
template<bool reduced, bool weighted=false, class Record, class Filter=std::nullptr_t>
void visit(Point a,unsigned start,unsigned left,Record& record,
           unsigned used=1,unsigned run=1,unsigned ways=1,Filter filter=nullptr) {
    // Opposite signs share an abscissa. Invert one denominator per pair.
    constexpr unsigned lanes=4;
    static_assert(lanes && !(lanes & (lanes-1)));
    std::array<Word,195> prefix,den,inverse;
    std::array<Word,lanes> products,lane_prefix;
    products.fill(1);
    const unsigned first=start/2, end=basis.size()/2;
    for(unsigned j=first;j<end;++j) {
        Word x=basis[2*j].x;
        // On the diagonal one sign doubles and the other cancels.
        Word d=a.x==p ? 1 : (a.x==x ? add(a.y,a.y) : sub(x,a.x));
        den[j]=d ? d : 1;
        Word& product=products[j % lanes];
        prefix[j]=product;
        product=mul(product,den[j]);
    }
    Word product=1;
    for(unsigned k=0;k<lanes;++k) {
        lane_prefix[k]=product;
        product=mul(product,products[k]);
    }
    Word reciprocal=inverse_nonzero(product);
    for(unsigned k=lanes;k-->0;) {
        Word lane_product=products[k];
        products[k]=mul(reciprocal,lane_prefix[k]);
        reciprocal=mul(reciprocal,lane_product);
    }
    for(unsigned j=end;j-->first;) {
        Word& lane=products[j % lanes];
        inverse[j]=mul(prefix[j],lane);
        lane=mul(lane,den[j]);
    }
    for(unsigned i=basis.size();i-->start;) {
        const Point b=basis[i];
        Point next;
        Word slope=0;
        if(a.x==p) next=b;
        else if(a.x==b.x && (!a.y || a.y!=b.y)) next=infinity;
        else {
            Word numer;
            if(a.x!=b.x) numer=sub(b.y,a.y);
            else {Word xx=mul(a.x,a.x); numer=add(add(xx,add(xx,xx)),2);}
            slope=mul(numer,inverse[i/2]);
            next.x=fold(std::uint64_t(slope)*slope + (2*p - a.x - b.x));
        }
        // Sorted occurrences put opposite signs of one generator next to each other.
        if constexpr (reduced) if (i==(start^1U)) continue;
        // The last expansion depends on x alone. Complete y only for survivors.
        if constexpr (!std::is_same_v<Filter,std::nullptr_t>) {
            if(left==2 && !(*filter)(next.x)) continue;
        }
        if(left>1 && a.x!=p && next.x!=p)
            next.y=sub(mul(slope,sub(a.x,next.x)),a.y);
        if constexpr (weighted) {
            unsigned next_run=i==start ? run+1 : 1;
            unsigned permutations=ways*(used+1)/next_run;
            if(left>1) visit<reduced,true>(next,i,left-1,record,used+1,next_run,permutations,filter);
            else if constexpr (std::is_invocable_v<Record,Word,unsigned,unsigned>)
                record(next.x,permutations,i/2);
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
template<bool simple=false>
static void five_prefixes(std::vector<Word> xs) {
    load_basis(xs);
    std::sort(xs.begin(),xs.end());
    if(std::adjacent_find(xs.begin(),xs.end())!=xs.end())
        throw std::invalid_argument("duplicate generator abscissa");
    std::array<bool,65536> suffix{};
    for(Word x:xs) suffix[x & 65535]=true;
    std::array<std::uint64_t,25> hits{};
    std::unordered_map<Word,unsigned> index;
    if constexpr (simple)
        for(unsigned j=0;j<basis.size()/2;++j) index.emplace(basis[2*j].x,j);
    auto count=[&](Word x,unsigned ways,unsigned largest) {
        if(!suffix[x & 65535]) return;
        if constexpr (simple) {
            if(ways!=24) return;
            auto it=index.find(x);
            if(it!=index.end() && it->second>largest) ++hits[24];
        } else if(std::binary_search(xs.begin(),xs.end(),x)) ++hits[ways];
    };
    // If T+b is a signed generator, T is the sum of two signed
    // generators. Hash abscissae only; collisions just keep extra nodes.
    constexpr Word mask=(1u<<22)-1;
    Bits pairs((mask+1)/64);
    // One word lookup tests two marks, taken from separate abscissa bits.
    auto marks=[](Word x) {
        return (UINT64_C(1)<<(x & 63)) | (UINT64_C(1)<<((x>>22) & 63));
    };
    auto insert=[&](Word x) {pairs[(x & mask)>>6] |= marks(x);};
    for(unsigned i=0;i<basis.size();i+=2) visit<false>(basis[i],i,1,insert);
    auto possible=[&](Word x) {
        auto bits=marks(x);
        return (pairs[(x & mask)>>6] & bits)==bits;
    };
    for(unsigned i=0;i<basis.size();i+=2)
        visit<true,true>(basis[i],i,3,count,1,1,1,&possible);
    if constexpr (simple) { std::cout<<hits[24]<<'\n'; return; }
    std::cout<<"prefix_permutations,completable_prefixes_up_to_sign\n";
    for(unsigned ways:{1,4,6,12,24}) std::cout<<ways<<','<<hits[ways]<<'\n';
}

template<class Record>
static void visit_shell(unsigned arity, Record& record) {
    for(unsigned i=0; i<basis.size(); i+=2)
        visit<false>(basis[i],i,arity-1,record);
}

// Each triple abscissa can contribute at most once to the intersection.
static std::uint64_t sparse_overlap() {
    constexpr Word mask=(1u<<22)-1;
    Bits filter((mask+1)/64);
    std::unordered_set<Word> remaining;
    auto insert=[&](Word x) {
        if(x==p) return;
        remaining.insert(x);
        filter[(x&mask)/64] |= UINT64_C(1)<<(x%64);
    };
    visit_shell(3,insert);
    auto before=remaining.size();
    auto remove=[&](Word x) {
        if(filter[(x&mask)/64] & (UINT64_C(1)<<(x%64))) remaining.erase(x);
    };
    visit_shell(4,remove);
    return 2*(before-remaining.size());
}

int main(int argc,char** argv) {
    std::vector<Word> xs;
    Word x;
    while(std::cin>>x) xs.push_back(x);
    if(argc==2 && std::string(argv[1])=="overlap-3-4") {
        if(xs.empty() || xs.size()>195) throw std::invalid_argument("invalid basis size");
        load_basis(xs);
        std::cout<<sparse_overlap()<<'\n';
        return 0;
    }
    if(argc==2 && (std::string(argv[1])=="five-prefixes" || std::string(argv[1])=="simple-five")) {
        if(xs.empty() || xs.size()>195) throw std::invalid_argument("invalid basis size");
        if(std::string(argv[1])=="simple-five") five_prefixes<true>(xs);
        else five_prefixes(xs);
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
