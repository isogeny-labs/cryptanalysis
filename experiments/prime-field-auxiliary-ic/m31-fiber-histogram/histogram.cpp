#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <numeric>

using U = uint64_t;
constexpr U p = 2147483647;
struct Point { U x, y; };
constexpr Point generator{3,615668188}, twoG{143165577,942483391}, step{1965083199,1854403464};

U add(U a,U b) { U x=a+b; return x>=p ? x-p : x; }
U sub(U a,U b) { return a>=b ? a-b : p-(b-a); }
U mul(U a,U b) {
    U v=a*b;
    return add(v&p,v>>31);
}
U inverse(U x) {
    assert(x);
    U r=1;
    for(U e=p-2;e;e>>=1) {
        if(e&1) r=mul(r,x);
        x=mul(x,x);
    }
    return r;
}
Point advance(Point a,Point b,U denominatorInverse) {
    U s=mul(sub(b.y,a.y),denominatorInverse);
    U x=sub(sub(mul(s,s),a.x),b.x);
    return {x,sub(mul(s,sub(a.x,x)),a.y)};
}
bool lifts(U x) {
    U rhs=add(add(mul(mul(x,x),x),add(x,x)),14);
    U y=rhs;
    for(int i=0;i<29;++i) y=mul(y,y);
    return mul(y,y)==rhs;
}

int main() {
    std::array<Point,32> points;
    Point a=generator;
    for(auto& v:points) {
        v=a;
        a=advance(a,step,inverse(sub(step.x,a.x)));
    }
    assert(a.x==generator.x && a.y==generator.y);
    std::array<U,33> hist{};
    U total=0;
    for(U idx=0;idx<(1u<<24);++idx) {
        std::array<U,32> prefix;
        U product=1, hits=0;
        for(size_t i=0;i<points.size();++i) {
            hits+=lifts(points[i].x);
            prefix[i]=product;
            product=mul(product,sub(twoG.x,points[i].x));
        }
        ++hist[hits];
        total+=hits;
        U inv=inverse(product);
        for(size_t i=points.size();i-->0;) {
            U den=sub(twoG.x,points[i].x);
            points[i]=advance(points[i],twoG,mul(inv,prefix[i]));
            inv=mul(inv,den);
        }
        if(idx%262147==0) std::cout<<"check "<<idx<<' '<<hits<<'\n';
    }
    assert(total==268414441);
    assert(std::accumulate(hist.begin(),hist.end(),U(0))==(1u<<24));
    for(size_t k=0;k<hist.size();++k) std::cout<<"bin "<<k<<' '<<hist[k]<<'\n';
}
