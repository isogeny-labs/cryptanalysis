#include "representation_join.hpp"
#include <iostream>
#include <set>
#include <string>
using namespace representation_join;
static std::uint64_t checks=0;
void check_at(bool ok,int line) {++checks;if(!ok)throw std::runtime_error("test assertion failed at line "+std::to_string(line));}
#define check(...) check_at((__VA_ARGS__),__LINE__)
template<class Fnc> void rejects(Fnc fn) {bool caught=false;try{fn();}catch(const std::invalid_argument&){caught=true;}check(caught);}
std::vector<Point> points(const Curve& e) {
    std::vector<Point> all{{}};
    std::map<std::pair<Int,Int>,std::vector<F>> roots;
    for(Int u=0;u<e.field.p;++u)for(Int v=0;v<e.field.p;++v) {
        F y{u,v},s=e.field.mul(y,y);roots[{s.u,s.v}].push_back(y);
    }
    for(Int u=0;u<e.field.p;++u)for(Int v=0;v<e.field.p;++v) {
        F x{u,v},r=e.rhs(x);for(auto y:roots[{r.u,r.v}])all.push_back({x,y,false});
    }
    return all;
}
Int order(const Curve& e,Point p,std::size_t bound) {
    Point q;for(std::size_t k=1;k<=bound;++k){q=e.add(q,p);if(q.infinity)return static_cast<Int>(k);}
    throw std::runtime_error("order bound violated");
}
int main() {try {
    rejects([]{Field f(9,2);});rejects([]{Field f(3,2);});rejects([]{Field f(7,1);});
    rejects([]{Curve e(7,3,{0,0},{0,0});});
    std::uint64_t pair_checks=0, false_positives=0, solved=0, pdp_checks=0;
    for(Int p:{5,7,11}) {
        Int d=2;for(;;++d){bool square=false;for(Int x=0;x<p;++x)square|=x*x%p==d;if(!square)break;}
        Curve e(p,d,{1,1},{p==5?2:1,0});const auto& f=e.field;
        for(Int u=0;u<p;++u)for(Int v=0;v<p;++v) {
            F x{u,v};if(x==F{})rejects([&]{f.inv(x);});else check(f.mul(x,f.inv(x))==F{1,0});
        }
        auto all=points(e);
        for(auto a:all)for(auto b:all) {
            auto sum=e.add(a,b);check(e.contains(sum));check(sum==e.add(b,a));
            bool possible=resultant_filter(e,a,b)==0;
            check(!e.accepts(sum)||possible);++pair_checks;
            if(possible&&!e.accepts(sum))++false_positives;
        }
        auto plain=join(e,all,all,Backend::exhaustive);
        auto filtered=join(e,all,all,Backend::resultant);
        check(plain.witnesses==filtered.witnesses);
        for(std::size_t i=0;i<std::min<std::size_t>(all.size(),12);++i)
            for(std::size_t j=0;j<12&&j<all.size();++j)
                for(std::size_t k=0;k<12&&k<all.size();++k)
                    check(e.add(e.add(all[i],all[j]),all[k])==e.add(all[i],e.add(all[j],all[k])));
        check(join(e,{},all).witnesses.empty());
        rejects([&]{join(e,all,all,Backend::resultant,{1,1});});
        rejects([&]{join(e,all,all,Backend::resultant,{1000000,0});});
        Point invalid{{p,0},{0,0},false};rejects([&]{join(e,{invalid},all);});
        // Repeated indices are witnesses, not points to deduplicate away.
        std::vector<Point> repeated{all[1],all[1],e.neg(all[1]),Point{}};
        check(join(e,repeated,all).witnesses==join(e,repeated,all,Backend::exhaustive).witnesses);
        // Public known-answer subgroup selected deterministically from the finite fixture.
        Point g;Int r=0;
        for(auto a:all)if(!a.infinity) {
            Int candidate=order(e,a,all.size());
            if(!prime(candidate)||candidate<=r)continue;
            bool admissible=false;for(Int k=1;k<candidate;++k)admissible|=e.accepts(e.mul(a,k));
            if(admissible){g=a;r=candidate;}
        }
        if(r<=2) {
            // Keep a zero-yield fixture as a negative control, not a success.
            for(auto a:all)if(!a.infinity) {
                Int candidate=order(e,a,all.size());
                if(prime(candidate)&&candidate>r){g=a;r=candidate;}
            }
            check(r>=2);
            std::vector<Int> scalars;for(Int k=0;k<r;++k)scalars.push_back(k);
            Prepared no_yield(e,g,r,scalars,{0},scalars,{0});
            check(no_yield.setup_stats.accepted==0);
            for(Int k=1;k<r;++k)check(!no_yield.solve(e.mul(g,k)));
            std::cout<<"negative fixture p="<<p<<" delta="<<d<<" a=(1,1) b=("<<e.b.u
                     <<",0) points="<<all.size()<<" r="<<r<<" no admissible subgroup point\n";
            continue;
        }
        Int radix=1;while(radix*radix<r)++radix;
        std::vector<Int> lo,hi;
        for(Int i=0;i<radix;++i)lo.push_back(i);
        for(Int i=0;i<r;i+=radix)hi.push_back(i);
        Prepared prepared(e,g,r,lo,hi,lo,hi);
        for(Int k=0;k<r;++k) {Stats online;auto answer=prepared.solve(e.mul(g,k),&online);check(answer&&*answer==k);++solved;}
        Prepared empty(e,g,r,{},{},{},{});check(!empty.solve(g));
        rejects([&]{Prepared wrong(e,g,r+1,lo,hi,lo,hi);});
        rejects([&]{Prepared wrong(e,g,r,{r},hi,lo,hi);});
        rejects([&]{prepared.solve(invalid);});
        for(auto a:all)if(!e.mul(a,r).infinity){rejects([&]{prepared.solve(a);});break;}
        std::cout<<"fixture p="<<p<<" delta="<<d<<" a=(1,1) b=("<<e.b.u<<",0) points="<<all.size()
                 <<" r="<<r<<" G=("<<g.x.u<<","<<g.x.v<<","<<g.y.u<<","<<g.y.v<<")\n";
        // Independent exhaustive four-index oracle: same admissibility condition,
        // no use of join or resultant. Compare complete witness sets for every target.
        std::vector<Point> base;
        for(Int k=1;k<std::min<Int>(r,6);++k)base.push_back(e.mul(g,k));
        for(Int t=0;t<r;++t) {
            Point target=e.mul(g,t);
            std::set<std::array<std::size_t,4>> expected,actual;
            for(std::size_t i=0;i<base.size();++i)for(std::size_t j=0;j<base.size();++j)
                for(std::size_t k=0;k<base.size();++k)for(std::size_t l=0;l<base.size();++l)
                    if(e.accepts(e.add(base[i],base[j]))&&e.add(e.add(base[i],base[j]),e.add(base[k],base[l]))==target)
                        expected.insert({i,j,k,l});
            for(auto w:decompose4(e,base,target))actual.insert(w.indices);
            check(expected==actual);++pdp_checks;
        }
        Point public_q=e.mul(g,3);
        for(auto row:collect_relations(e,g,public_q,2,3,base)) {
            Int scalar_sum=0;
            for(std::size_t i=0;i<row.coefficients.size();++i)
                scalar_sum+=static_cast<Int>(row.coefficients[i])*static_cast<Int>(i+1);
            check(scalar_sum%r==(row.a+3*row.b)%r);
        }
    }
    check(false_positives>0);
    std::cout<<"PASS assertions="<<checks<<" pair_checks="<<pair_checks<<" filter_false_positives="<<false_positives
             <<" public_targets_solved="<<solved<<" pdp_target_oracles="<<pdp_checks<<"\n";
    std::cout<<"Scope: bounded correctness tests; no timing, asymptotic, or end-to-end IC gain claim.\n";
    return 0;
} catch(const std::exception& e) {std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
