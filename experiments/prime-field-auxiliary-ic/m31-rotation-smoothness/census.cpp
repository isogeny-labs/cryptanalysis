#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <unordered_set>
#include <vector>
using U = uint64_t;
constexpr U p = 2147483647;

U rotate(U x) { return ((x << 1) & p) | (x >> 30); }
bool square(U x) {
    U result=1;
    for (U e=(p-1)/2; e; e>>=1) {
        if (e&1) result=result*x%p;
        x=x*x%p;
    }
    return result != p-1;
}

int main() {
    std::vector<U> values{1};
    std::unordered_set<U> seen;
    U eligible=0, lifts=0;
    for (U prime : {3,5,7,11,13,17,19,23,29,31,37,41,43,47}) {
        const auto previous=values.size();
        for (size_t i=0; i<previous; ++i)
            for (U x=values[i]*prime; x<p; x*=prime) values.push_back(x);
        if (prime!=7 && prime!=13 && prime!=23 && prime!=47) continue;
        for (U v : values) {
            U key=v, x=rotate(v);
            while (x!=v) {key=std::min(key,x); x=rotate(x);}
            if (!seen.insert(key).second || square(key)) continue;
            // Two is a square modulo p, so the whole orbit has the same character.
            do {
                U xx=x*x%p;
                if (!square((xx+1)%p)) {
                    ++eligible;
                    lifts+=square((xx*x+2*x+14)%p);
                }
                x=rotate(x);
            } while (x!=v);
        }
        std::printf("%llu %zu %llu %llu\n",(unsigned long long)prime,
            seen.size(),(unsigned long long)eligible,(unsigned long long)lifts);
    }
}
