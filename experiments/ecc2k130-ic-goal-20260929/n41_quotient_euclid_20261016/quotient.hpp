#include "oracle_helpers.hpp"

using RPoly = std::vector<Poly>;

static Poly pxor(Poly a,const Poly&b){
    if(a.size()<b.size())a.resize(b.size(),0);
    for(size_t i=0;i<b.size();++i)a[i]^=b[i];
    trim(a);return a;
}
static Poly pscale(Poly a,Word c){
    for(Word&x:a)x=fm(x,c);
    trim(a);return a;
}
static std::pair<Poly,Poly> pdivrem(Poly a,const Poly&b){
    if(b.empty())throw std::runtime_error("polynomial division by zero");
    if(a.size()<b.size())return {Poly{},a};
    Poly q(a.size()-b.size()+1,0);
    Word inv=fi(b.back());
    for(int k=int(q.size())-1;k>=0;--k){
        Word c=fm(a[k+b.size()-1],inv);q[k]=c;
        if(!c)continue;
        for(size_t j=0;j<b.size();++j)a[k+j]^=fm(c,b[j]);
    }
    trim(q);trim(a);
    if(a.size()>=b.size())throw std::runtime_error("division degree");
    return {q,a};
}
struct Inverse {bool unit;Poly inverse,gcd;};
static Inverse pinverse(const Poly&a,const Poly&mod){
    if(mod.empty()||mod.back()!=1)throw std::runtime_error("ring modulus");
    Poly old_r=mod,r=pmod(a,mod),old_t{},t{1};
    while(!r.empty()){
        auto [q,next]=pdivrem(old_r,r);
        Poly next_t=pxor(old_t,pmul(q,t));
        old_r=std::move(r);r=std::move(next);
        old_t=std::move(t);t=std::move(next_t);
    }
    if(old_r.empty())throw std::runtime_error("extended gcd zero");
    Word scale=fi(old_r.back());
    old_r=pscale(old_r,scale);
    if(old_r.size()>1)return {false,{},old_r};
    Poly inverse=pmod(pscale(old_t,scale),mod);
    if(pmod(pmul(a,inverse),mod)!=Poly{1})throw std::runtime_error("inverse replay");
    return {true,inverse,Poly{1}};
}
static Poly rmul(const Poly&a,const Poly&b,const Poly&mod){
    return pmod(pmul(a,b),mod);
}
static Poly rsq(const Poly&a,const Poly&mod){
    return pmod(psquare(a),mod);
}
static void trimr(RPoly&a){while(!a.empty()&&a.back().empty())a.pop_back();}
static RPoly reduce_coeffs(RPoly a,const Poly&mod){
    for(Poly&v:a)v=pmod(std::move(v),mod);
    trimr(a);return a;
}
static RPoly rscale(RPoly a,const Poly&c,const Poly&mod){
    for(Poly&v:a)v=rmul(v,c,mod);
    trimr(a);return a;
}
static RPoly rmod_monic(RPoly a,const RPoly&h,const Poly&mod){
    if(h.empty()||h.back()!=Poly{1})throw std::runtime_error("nonmonic tower");
    if(a.size()<h.size())return a;
    for(int k=int(a.size()-h.size());k>=0;--k){
        Poly c=a[k+h.size()-1];
        if(c.empty())continue;
        for(size_t j=0;j+1<h.size();++j)
            a[k+j]=pxor(std::move(a[k+j]),rmul(c,h[j],mod));
        a[k+h.size()-1].clear();
    }
    trimr(a);
    if(a.size()>=h.size())throw std::runtime_error("tower reduction degree");
    return a;
}
static RPoly rlinearized_rem(const RPoly&h,const Poly&mod,
                            const std::vector<Word>&basis,int rank){
    if(rank<0||rank>int(basis.size()))throw std::runtime_error("basis rank");
    RPoly x(2);x[1]=Poly{1};
    std::vector<Word>alphas;
    for(int i=0;i<rank;++i){
        Word alpha=basis[i];
        for(Word prior:alphas)alpha=fs(alpha)^fm(prior,alpha);
        if(!alpha)throw std::runtime_error("dependent basis");
        alphas.push_back(alpha);
        RPoly square(2*x.size()-1);
        for(size_t j=0;j<x.size();++j)square[2*j]=rsq(x[j],mod);
        square=rmod_monic(std::move(square),h,mod);
        if(square.size()<x.size())square.resize(x.size());
        for(size_t j=0;j<x.size();++j)
            square[j]=pxor(std::move(square[j]),pscale(x[j],alpha));
        trimr(square);x=std::move(square);
    }
    return x;
}

struct Euclid {
    Poly suspects;
    int unit_pivots=0,splits=0,all_suspect_branches=0;
    uint64_t inverse_ns=0,division_ns=0;
};
static Euclid euclid_gate(const RPoly&h_full,const RPoly&l_full,
                         Poly active){
    Euclid out;
    while(active.size()>1){
        RPoly a=reduce_coeffs(h_full,active),b=reduce_coeffs(l_full,active);
        bool restart=false;
        for(int step=0;step<50;++step){
            if(b.empty()){
                if(a.size()>1){
                    out.suspects=pmul(out.suspects.empty()?Poly{1}:out.suspects,active);
                    ++out.all_suspect_branches;
                }
                active=Poly{1};break;
            }
            auto began=tick();auto inverse=pinverse(b.back(),active);
            out.inverse_ns+=ns(began);
            if(!inverse.unit){
                Poly factor=inverse.gcd;
                if(factor.size()==1)throw std::runtime_error("nonunit constant gcd");
                out.suspects=pmul(out.suspects.empty()?Poly{1}:out.suspects,factor);
                ++out.splits;
                if(factor==active){active=Poly{1};break;}
                auto [quotient,remainder]=pdivrem(active,factor);
                if(!remainder.empty())throw std::runtime_error("CRT factor division");
                active=std::move(quotient);restart=true;break;
            }
            ++out.unit_pivots;
            if(b.size()==1){active=Poly{1};break;}
            began=tick();
            RPoly monic_b=rscale(b,inverse.inverse,active);
            if(monic_b.back()!=Poly{1})throw std::runtime_error("monic Euclid divisor");
            RPoly remainder=rmod_monic(std::move(a),monic_b,active);
            out.division_ns+=ns(began);
            a=std::move(b);b=std::move(remainder);
        }
        if(!restart&&active.size()>1)throw std::runtime_error("Euclid step bound");
    }
    if(out.suspects.empty())out.suspects=Poly{1};
    return out;
}
