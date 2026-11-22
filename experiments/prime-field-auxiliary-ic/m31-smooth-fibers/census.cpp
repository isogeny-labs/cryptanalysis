#include <algorithm>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <unordered_set>
#include <vector>

using U = uint64_t;
constexpr U p = 2147483647;
struct Point { U x,y; };
constexpr Point step {1965083199,1854403464};
U power(U x,U e) {
    U r=1;
    for (;e;e>>=1) {
        if (e&1) r=r*x%p;
        x=x*x%p;
    }
    return r;
}
U rotate(U x) { return ((2*x)&p)|(x>>30); }
Point advance(Point a,Point b,bool doubling) {
    U numerator=doubling ? (3*(a.x*a.x%p)+1)%p : (p+b.y-a.y)%p;
    U denominator=doubling ? 2*a.y%p : (p+b.x-a.x)%p;
    assert(denominator);
    U slope=numerator*power(denominator,p-2)%p;
    U x=(slope*slope%p+2*p-a.x-b.x)%p;
    return {x,(slope*((p+a.x-x)%p)%p+p-a.y)%p};
}
bool lifts(U x) { return power(((x*x%p)*x+2*x+14)%p,(p-1)/2)!=p-1; }

int main() {
    std::vector<U> oddSmooth{1};
    for (U q:{3,5,7,11,13,17,19,23,29,31,37,41,43,47}) {
        size_t old=oddSmooth.size();
        for (size_t i=0;i<old;++i)
            for(U v=oddSmooth[i]*q;v<p;v*=q) oddSmooth.push_back(v);
    }
    std::unordered_set<U> orbits,fibers;
    U marks=0,markedLifts=0,allLifts=0,rich=0;
    for (U seed:oddSmooth) {
        U key=seed;
        for(U v=rotate(seed);v!=seed;v=rotate(v)) key=std::min(key,v);
        if (!orbits.insert(key).second || power(key,(p-1)/2)!=p-1) continue;
        U x=key;
        do {
            U xx=x*x%p;
            if(power((xx+1)%p,(p-1)/2)==p-1) {
                ++marks;
                markedLifts+=lifts(x);
                U rhs=(xx*x+x)%p;
                Point a{x,power(rhs,(p+1)/4)};
                assert(a.y*a.y%p==rhs);
                Point tag=a;
                for(int k=0;k<5;++k) tag=advance(tag,tag,true);
                if(fibers.insert(tag.x).second) {
                    unsigned total=0;
                    Point initial=a;
                    for(int k=0;k<32;++k) {
                        total+=lifts(a.x);
                        a=advance(a,step,false);
                    }
                    assert(initial.x==a.x && initial.y==a.y);
                    allLifts+=total;
                    rich+=total>=20;
                }
            }
            x=rotate(x);
        } while(x!=key);
    }
    assert(marks==1852867 && markedLifts==925398);
    std::cout<<"marked_coordinates marked_lifts fibers fiber_lifts fibers_at_least_20\n"
             <<marks<<' '<<markedLifts<<' '<<fibers.size()<<' '<<allLifts<<' '<<rich<<'\n';
}
