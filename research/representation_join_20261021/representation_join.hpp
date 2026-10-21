#pragma once
// DFKM 2020, HAL hal-02427655, sections 3--4: bounded reference implementation.
// Pairwise resultant evaluation, NOT Kedlaya--Umans multipoint evaluation.
#include <algorithm>
#include <array>
#include <cstdint>
#include <map>
#include <optional>
#include <stdexcept>
#include <tuple>
#include <vector>

namespace representation_join {
using Int = std::int64_t;
inline void require(bool ok, const char* why) {
    if (!ok) throw std::invalid_argument(why);
}
inline bool prime(Int n) {
    if (n < 2) return false;
    for (Int d=2; d*d<=n; ++d) if (n%d==0) return false;
    return true;
}
struct F { Int u=0, v=0; bool operator==(const F& z) const {return u==z.u && v==z.v;} };
class Field {
public:
    const Int p, delta;
    Field(Int modulus, Int nonresidue): p(modulus), delta(nonresidue) {
        require(p>3 && p<=101 && prime(p), "require prime 3 < p <= 101");
        require(delta>0 && delta<p, "noncanonical nonresidue");
        for (Int x=0; x<p; ++x) require(x*x%p!=delta, "reducible quadratic modulus");
    }
    Int mod(Int x) const { x%=p; return x<0 ? x+p : x; }
    F make(Int u, Int v=0) const { return {mod(u),mod(v)}; }
    bool canonical(F z) const {return z.u>=0 && z.u<p && z.v>=0 && z.v<p;}
    F add(F x,F y) const {return make(x.u+y.u,x.v+y.v);}
    F neg(F x) const {return make(-x.u,-x.v);}
    F sub(F x,F y) const {return add(x,neg(y));}
    F mul(F x,F y) const {return make(x.u*y.u+delta*x.v*y.v,x.u*y.v+x.v*y.u);}
    F pow(F x,Int n) const {F y{1,0}; for (;n;n>>=1,x=mul(x,x)) if(n&1)y=mul(y,x); return y;}
    F inv(F x) const {require(!(x==F{}),"division by zero");return pow(x,p*p-2);}
    F div(F x,F y) const {return mul(x,inv(y));}
};
struct Point {
    F x{}, y{}; bool infinity=true;
    bool operator==(const Point& q) const {
        return infinity==q.infinity && (infinity || (x==q.x && y==q.y));
    }
    bool operator<(const Point& q) const {
        return std::tie(infinity,x.u,x.v,y.u,y.v)<std::tie(q.infinity,q.x.u,q.x.v,q.y.u,q.y.v);
    }
};
class Curve {
public:
    const Field field; const F a,b;
    Curve(Int p,Int d,F aa,F bb):field(p,d),a(aa),b(bb) {
        require(field.canonical(a)&&field.canonical(b),"noncanonical coefficients");
        require(!(field.add(field.mul({4,0},field.pow(a,3)),field.mul(field.make(27),field.mul(b,b)))==F{}),"singular curve");
    }
    F rhs(F x) const {return field.add(field.add(field.pow(x,3),field.mul(a,x)),b);}
    bool contains(Point p) const {
        if(p.infinity) return p.x==F{} && p.y==F{};
        return field.canonical(p.x)&&field.canonical(p.y)&&field.mul(p.y,p.y)==rhs(p.x);
    }
    Point neg(Point p) const {return p.infinity ? Point{} : Point{p.x,field.neg(p.y),false};}
    Point add(Point p,Point q) const {
        require(contains(p)&&contains(q),"point not on curve");
        if(p.infinity)return q;
        if(q.infinity)return p;
        const auto& f=field;
        F m;
        if(p.x==q.x) {
            if(f.add(p.y,q.y)==F{})return {};
            m=f.div(f.add(f.mul({3,0},f.mul(p.x,p.x)),a),f.mul({2,0},p.y));
        } else m=f.div(f.sub(q.y,p.y),f.sub(q.x,p.x));
        F x=f.sub(f.sub(f.mul(m,m),p.x),q.x);
        return {x,f.sub(f.mul(m,f.sub(p.x,x)),p.y),false};
    }
    Point mul(Point p,Int n) const {
        require(contains(p)&&n>=0,"invalid scalar multiplication");
        Point q; for(;n;n>>=1,p=add(p,p))if(n&1)q=add(q,p); return q;
    }
    bool accepts(Point p) const {return !p.infinity && p.x.v==0;}
};

// Evaluate the padded 4x4 Sylvester determinant of real/imaginary
// coefficients of G(x1,x2,T). Common finite roots always make it zero.
// Degenerate degree drops and sign ambiguity can create false positives;
// the actual group sum must always be checked after this necessary test.
inline Int resultant_filter(const Curve& e,Point p,Point q) {
    require(e.contains(p)&&e.contains(q),"invalid filter input");
    if(p.infinity||q.infinity||p.x==q.x)return 0; // exact exceptional fallback
    const auto& f=e.field;
    F d=f.mul(f.sub(p.x,q.x),f.sub(p.x,q.x));
    F h=f.sub(f.mul(d,f.add(p.x,q.x)),f.add(e.rhs(p.x),e.rhs(q.x)));
    std::array<F,3> g{f.sub(f.mul(h,h),f.mul({4,0},f.mul(e.rhs(p.x),e.rhs(q.x)))),
                      f.mul({2,0},f.mul(h,d)),f.mul(d,d)};
    std::array<std::array<Int,4>,4> m{{
        {g[2].u,g[1].u,g[0].u,0},{0,g[2].u,g[1].u,g[0].u},
        {g[2].v,g[1].v,g[0].v,0},{0,g[2].v,g[1].v,g[0].v}}};
    std::array<int,4> perm{0,1,2,3}; Int det=0;
    do {
        Int term=1; int inversions=0;
        for(int i=0;i<4;++i) {
            term=f.mod(term*m[i][perm[i]]);
            for(int j=0;j<i;++j)inversions+=perm[j]>perm[i];
        }
        det=f.mod(det+(inversions%2 ? -term : term));
    } while(std::next_permutation(perm.begin(),perm.end()));
    return det;
}
enum class Backend { exhaustive, resultant };
struct Budget { std::uint64_t max_pairs=1000000, max_outputs=1000000; };
struct Stats { std::uint64_t pairs=0, candidates=0, accepted=0; };
struct Witness {
    std::size_t left,right; Point sum;
    bool operator==(const Witness& w) const {return left==w.left&&right==w.right&&sum==w.sum;}
};
struct JoinResult { std::vector<Witness> witnesses; Stats stats; };
inline JoinResult join(const Curve& e,const std::vector<Point>& a,const std::vector<Point>& b,
                       Backend backend=Backend::resultant,Budget budget={}) {
    require(b.empty()||a.size()<=budget.max_pairs/b.size(),"pair budget exceeded");
    for(auto p:a)require(e.contains(p),"invalid left point");
    for(auto p:b)require(e.contains(p),"invalid right point");
    JoinResult out;
    for(std::size_t i=0;i<a.size();++i)for(std::size_t j=0;j<b.size();++j) {
        ++out.stats.pairs;
        if(backend==Backend::resultant && resultant_filter(e,a[i],b[j])!=0)continue;
        ++out.stats.candidates;
        Point sum=e.add(a[i],b[j]);
        if(!e.accepts(sum))continue;
        require(out.witnesses.size()<budget.max_outputs,"output budget exceeded");
        out.witnesses.push_back({i,j,sum}); ++out.stats.accepted;
    }
    return out;
}

// Four scalar sets are supplied explicitly; no heuristic coverage is assumed.
// All points in a subgroup are enumerated only for bounded membership validation.
class Prepared {
    Curve e; Point generator; Int order;
    std::vector<Int> s11,s12,s21,s22;
    std::vector<Point> minus21,minus22;
    std::map<Point,Int> left;
    Backend backend; Budget budget;
    std::vector<Point> multiples(const std::vector<Int>& s,bool negative) const {
        std::vector<Point> out;
        for(Int k:s) {
            require(k>=0&&k<order,"scalar set entry outside subgroup range");
            Point p=e.mul(generator,k);out.push_back(negative?e.neg(p):p);
        }
        return out;
    }
public:
    Stats setup_stats;
    Prepared(Curve curve,Point p,Int r,std::vector<Int> a,std::vector<Int> b,
             std::vector<Int> c,std::vector<Int> d,Backend mode=Backend::resultant,Budget limits={}):
        e(curve),generator(p),order(r),s11(std::move(a)),s12(std::move(b)),
        s21(std::move(c)),s22(std::move(d)),backend(mode),budget(limits) {
        require(order<=20000&&prime(order)&&!p.infinity&&e.contains(p)&&e.mul(p,order).infinity,
                "require bounded prime-order generator");
        for(auto size:{s11.size(),s12.size(),s21.size(),s22.size()})
            require(size<=budget.max_pairs,"input budget exceeded");
        auto apts=multiples(s11,false), bpts=multiples(s12,false);
        minus21=multiples(s21,true);minus22=multiples(s22,true);
        auto joined=join(e,apts,bpts,backend,budget);setup_stats=joined.stats;
        for(const auto& w:joined.witnesses)left.emplace(w.sum,(s11[w.left]+s12[w.right])%order);
    }
    std::optional<Int> solve(Point q,Stats* online=nullptr) const {
        require(e.contains(q),"target not on curve");
        Point member; bool found=false;
        for(Int i=0;i<order;++i,member=e.add(member,generator))if(member==q){found=true;break;}
        require(found,"target outside generated subgroup");
        if(q.infinity){if(online)*online={};return 0;}
        std::vector<Point> shifted;for(auto p:minus21)shifted.push_back(e.add(q,p));
        auto joined=join(e,shifted,minus22,backend,budget);if(online)*online=joined.stats;
        for(const auto& w:joined.witnesses) {
            auto match=left.find(w.sum);if(match==left.end())continue;
            Int k=(match->second+s21[w.left]+s22[w.right])%order;
            if(e.mul(generator,k)==q)return k;
        }
        return std::nullopt; // constrained search exhausted, not a nonexistence proof
    }
};

struct Decomposition { std::array<std::size_t,4> indices; };
// IC adapter: only emits verified R=B_i+B_j+B_k+B_l with a filtered
// intermediate B_i+B_j. Keeps all ordered/repeated witnesses; no orbit folding.
inline std::vector<Decomposition> decompose4(const Curve& e,const std::vector<Point>& base,
                                            Point target,Backend mode=Backend::resultant,Budget budget={}) {
    require(e.contains(target),"invalid target");
    auto lhs=join(e,base,base,mode,budget);
    std::map<Point,std::vector<std::pair<std::size_t,std::size_t>>> table;
    for(const auto& w:lhs.witnesses)table[w.sum].push_back({w.left,w.right});
    std::vector<Point> right1,right2;
    for(auto p:base){right1.push_back(e.add(target,e.neg(p)));right2.push_back(e.neg(p));}
    auto rhs=join(e,right1,right2,mode,budget);
    std::vector<Decomposition> out;
    for(const auto& w:rhs.witnesses) {
        auto it=table.find(w.sum);if(it==table.end())continue;
        for(auto ij:it->second) {
            require(out.size()<budget.max_outputs,"decomposition budget exceeded");
            Point sum=e.add(e.add(base[ij.first],base[ij.second]),e.add(base[w.left],base[w.right]));
            require(sum==target,"invalid decomposition");
            out.push_back({{ij.first,ij.second,w.left,w.right}});
        }
    }
    return out;
}

struct Relation {
    Int a,b; // a*P+b*Q = sum_j coefficients[j]*base[j], before reduction mod r
    std::vector<unsigned> coefficients;
    std::array<std::size_t,4> witness;
};
// Collector boundary: this routine verifies the group equation. The caller
// must establish common prime-order subgroup membership and use that r for LA.
// No factor-base logarithms, hidden scalar, or orbit folding enter this API.
inline std::vector<Relation> collect_relations(const Curve& e,Point p,Point q,Int a,Int b,
                                              const std::vector<Point>& base,Budget budget={}) {
    require(a>=0&&b>=0,"negative relation coefficient");
    Point target=e.add(e.mul(p,a),e.mul(q,b));
    std::vector<Relation> out;
    for(auto decomposition:decompose4(e,base,target,Backend::resultant,budget)) {
        Relation row{a,b,std::vector<unsigned>(base.size(),0),decomposition.indices};
        for(auto i:row.witness)++row.coefficients[i];
        out.push_back(std::move(row));
    }
    return out;
}
} // namespace representation_join
