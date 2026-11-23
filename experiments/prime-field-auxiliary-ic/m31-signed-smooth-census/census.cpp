#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>

using U = uint64_t;
constexpr U p = (U(1)<<31)-1;
constexpr std::array<int,6> bounds = {7,13,23,47,97,211};
struct Counts { U n=0, target=0, aux=0, both=0; };
using Bins = std::array<std::array<Counts,3>,bounds.size()>;

static bool square(U v) {
    if (!v) std::abort(); // Neither cubic vanishes on these nonzero inputs.
    U r=v;
    for (int i=1;i<30;++i) r=((r*r%p)*v)%p;
    if (r!=1 && r!=p-1) std::abort();
    return r==1;
}

static void add(Counts& c, bool aux, bool target) {
    ++c.n;
    c.target+=target;
    c.aux+=aux;
    c.both+=aux && target;
}

static void visit(U x, size_t first, size_t bin, const std::vector<int>& primes, Bins& out) {
    U cube=((x*x%p)*x)%p;
    bool a=square((cube+x)%p);
    U odd=(cube+2*x)%p;
    bool t=square((odd+14)%p);
    add(out[bin][0],a,t);
    if (x<=p/2) {
        add(out[bin][1],a,t);
        add(out[bin][2],!a,square((p+14-odd)%p));
    }
    for (size_t j=first;j<primes.size();++j) {
        U y=x*primes[j];
        if (y>=p) break;
        while (primes[j]>bounds[bin]) ++bin;
        visit(y,j,bin,primes,out);
    }
}

int main() {
    std::vector<int> primes;
    for (int v=2;v<=bounds.back();++v) {
        bool prime=true;
        for (int d=2;d*d<=v;++d) if (v%d==0) prime=false;
        if (prime) primes.push_back(v);
    }
    Bins out{};
    visit(1,0,0,primes,out);
    std::puts("bound,representative,coordinates,target_lifts,auxiliary_lifts,joint_lifts");
    const char* names[]={"canonical","positive_half","negative_half"};
    for (size_t arm=0;arm<3;++arm) {
        Counts total;
        for (size_t b=0;b<bounds.size();++b) {
            Counts c=out[b][arm];
            total.n+=c.n; total.target+=c.target; total.aux+=c.aux; total.both+=c.both;
            std::printf("%d,%s,%llu,%llu,%llu,%llu\n",bounds[b],names[arm],
                (unsigned long long)total.n,(unsigned long long)total.target,
                (unsigned long long)total.aux,(unsigned long long)total.both);
        }
    }
}
