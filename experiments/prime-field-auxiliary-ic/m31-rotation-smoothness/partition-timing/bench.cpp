#include <string_view>
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <iterator>
#include <vector>
using U = uint32_t;
using W = uint64_t;
using Keys = std::vector<U>;
constexpr U p = 2147483647;
constexpr U primes[] = {3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89};

U mul(U a, U b) {
    W z = W(a)*b;
    U r = (z & p) + (z >> 31);
    return r >= p ? r-p : r;
}
U power(U x, U n) {
    U a = 1;
    for (; n; n >>= 1) {
        if (n & 1) a = mul(a,x);
        x = mul(x,x);
    }
    return a;
}
template<class T> void unique_sort(std::vector<T>& xs) {
    std::sort(xs.begin(),xs.end());
    xs.erase(std::unique(xs.begin(),xs.end()),xs.end());
}
struct Prime { U q, key, inv; bool negative; };
using Factors = std::vector<Prime>;
Factors factors(U bound) {
    Factors out;
    for (auto q : primes) {
        if (q > bound) break;
        U k = power(q,31);
        out.push_back({q,k,power(k,p-2),power(q,(p-1)/2) == p-1});
    }
    return out;
}
template<bool both, class Emit>
void visit(const Factors& fs, size_t first, U x, U k, U inv, bool neg, Emit& emit) {
    emit(x,k,inv,neg);
    for (size_t i=first; i<fs.size(); ++i) {
        const auto f = fs[i];
        W y = W(x)*f.q;
        if (y >= p) break;
        visit<both>(fs,i,U(y),mul(k,f.key),both ? mul(inv,f.inv) : 0,
                    both && neg != f.negative,emit);
    }
}
Keys exhaustive(U bound) {
    Keys keys, pairs;
    auto emit = [&](U,U k,U inv,bool neg) {
        if (neg) keys.push_back(2*std::min(k,inv) + (k>inv));
    };
    visit<true>(factors(bound),0,1,1,1,false,emit);
    unique_sort(keys);
    for (size_t i=1; i<keys.size(); ++i)
        if ((keys[i-1]^keys[i]) == 1) pairs.push_back(keys[i]/2);
    return pairs;
}
using Row = std::pair<U,U>;
std::vector<Row> list(const Factors& fs) {
    std::vector<Row> rows;
    auto emit = [&](U x,U k,U,bool) { rows.emplace_back(k,x); };
    visit<false>(fs,0,1,1,1,false,emit);
    std::sort(rows.begin(),rows.end());
    return rows;
}
void products(const Factors& fs, int bit, std::vector<W>& out) {
    Factors left,right;
    for (size_t i=0; i<fs.size(); ++i) {
        auto f = fs[i];
        if ((i>>bit)&1) left.push_back(f);
        else { f.key=f.inv; right.push_back(f); }
    }
    auto xs=list(left), ys=list(right);
    size_t i=0,j=0;
    while (i<xs.size() && j<ys.size()) {
        if (xs[i].first<ys[j].first) { ++i; continue; }
        if (ys[j].first<xs[i].first) { ++j; continue; }
        size_t a=i,b=j;
        U k=xs[i].first;
        while (i<xs.size() && xs[i].first==k) ++i;
        while (j<ys.size() && ys[j].first==k) ++j;
        for (size_t u=a; u<i; ++u)
            for (size_t v=b; v<j; ++v) out.push_back(W(xs[u].second)*ys[v].second);
    }
}
void replay(W n,const Factors& fs,Keys& pairs) {
    W remaining=n;
    std::vector<W> divisors{1};
    for (auto f:fs) {
        size_t count=divisors.size();
        W qpower=1;
        while (remaining%f.q==0) {
            remaining/=f.q;
            qpower*=f.q;
            for (size_t i=0;i<count;++i) divisors.push_back(divisors[i]*qpower);
        }
    }
    for (W x:divisors) {
        W y=n/x;
        if (x>y || y>=p || power(U(x),(p-1)/2)!=p-1) continue;
        U k=power(U(x),31), t=power(U(y),31);
        if (k!=t) pairs.push_back(std::min(k,t));
    }
}
Keys capped(U bound) {
    auto fs=factors(bound);
    std::vector<W> ns;
    for (int bit=0;bit<2;++bit) products(fs,bit,ns);
    unique_sort(ns);
    Keys pairs;
    for (W n:ns) replay(n,fs,pairs);
    unique_sort(pairs);
    return pairs;
}
#include "filter_comparison.h"

int main(int argc, char** argv) {
    if (argc == 2 && std::string_view(argv[1]) == "--hash-filter") return compare_filters();
    if (argc != 1) return EXIT_FAILURE;
    auto old=exhaustive(83), oldcap=capped(83);
    auto full=exhaustive(89), part=capped(89);
    auto subset=[](const Keys& a,const Keys& b) {
        return std::includes(b.begin(),b.end(),a.begin(),a.end());
    };
    if (old.size()!=2308 || oldcap.size()!=1534 || !subset(oldcap,old) ||
        !subset(old,full) || !subset(part,full) || !subset(oldcap,part)) return 1;
    std::puts("round,position,mode,ms,pairs,new_since_83");
    for (int round=0;round<12;++round) for (int pos=0;pos<2;++pos) {
        bool partial=(round+pos)%2;
        using Clock=std::chrono::steady_clock;
        auto start=Clock::now();
        Keys result=partial ? capped(89) : exhaustive(89);
        double ms=std::chrono::duration<double,std::milli>(Clock::now()-start).count();
        if (result!=(partial ? part : full)) return 2;
        Keys fresh;
        std::set_difference(result.begin(),result.end(),old.begin(),old.end(),std::back_inserter(fresh));
        std::printf("%d,%d,%s,%.6f,%zu,%zu\n",round,pos,partial?"capped":"full",ms,result.size(),fresh.size());
    }
}
