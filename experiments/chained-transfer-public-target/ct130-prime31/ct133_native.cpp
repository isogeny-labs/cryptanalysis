// CT133 independently authored same-host native C++17 CM-neighbor ECDLP cost screen.
// Producer-only measurement, not a signed PCC or fully optimized external reference.
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <random>
#include <stdexcept>
#include <unordered_map>
#include <unordered_set>
#include <vector>
using u64=uint64_t; using u128=__uint128_t;
constexpr u64 p=2147483033ULL, q=536857417ULL;
constexpr u64 sa=622683939ULL,sb=2147483024ULL, ii=392507391ULL, lam=390258842ULL;
constexpr u64 r=969960860ULL;
struct Pt { u64 x=0,y=0; bool o=true;
  bool operator==(const Pt& b)const{return o==b.o&&(o||(x==b.x&&y==b.y));}
  bool operator!=(const Pt& b)const{return !(*this==b);}
  bool operator<(const Pt& b)const {return o!=b.o?o:(o?false:(x!=b.x?x<b.x:y<b.y));}
};
struct Hash { size_t operator()(const Pt& t)const{return (size_t)((t.x*0x9e3779b97f4a7c15ULL)^(t.y<<1)^uint64_t(t.o));}};
Pt pt(u64 x,u64 y){return Pt{x,y,false};}
Pt neg(Pt t){if(!t.o && t.y)t.y=p-t.y;return t;}
u64 addm(u64 a,u64 b){u64 x=a+b;return x>=p?x-p:x;}
u64 subm(u64 a,u64 b){return a>=b?a-b:p+a-b;}
u64 mulm(u64 a,u64 b){return (u64)(((u128)a*b)%p);}
u64 powm(u64 a,u64 b){u64 out=1;while(b){if(b&1)out=mulm(out,a);a=mulm(a,a);b>>=1;}return out;}
u64 invq(u64 a){if(!a)throw std::runtime_error("zero q inverse");u64 r=1,e=q-2;while(e){if(e&1)r=(u128)r*a%q;a=(u128)a*a%q;e>>=1;}return r;}
u64 invm(u64 a){if(!a)throw std::runtime_error("division by zero");return powm(a,p-2);}
struct Curve {
  u64 a,b,adds=0,invs=0;
  Pt plus(Pt v,Pt w){++adds;if(v.o)return w;if(w.o)return v;
    if(v.x==w.x && v.y!=w.y)return Pt{};
    u64 den=0,num=0;
    if(v==w){if(v.y==0)return Pt{};den=addm(v.y,v.y);num=addm(addm(mulm(3,mulm(v.x,v.x)),mulm(2,mulm(a,v.x))),b);}
    else {den=subm(w.x,v.x);num=subm(w.y,v.y);}
    ++invs;u64 s=mulm(num,invm(den));
    u64 xr=subm(subm(subm(mulm(s,s),a),v.x),w.x);
    u64 yr=subm(mulm(s,subm(v.x,xr)),v.y);
    return pt(xr,yr);
  }
  Pt times(Pt v,u64 k){Pt z{};while(k){if(k&1)z=plus(z,v);v=plus(v,v);k>>=1;}return z;}
  bool on(Pt v)const {return v.o || mulm(v.y,v.y)==addm(addm(mulm(v.x,mulm(v.x,v.x)),mulm(a,mulm(v.x,v.x))),mulm(b,v.x));}
};
constexpr u64 i4=536870758ULL; // overridden by runtime modular inverse(4)
Pt map2(Pt v){if(v.o)return v;if(!v.x)throw std::runtime_error("2-torsion kernel mapped");
  u64 z=invm(v.x), z2=mulm(z,z);
  return pt(addm(mulm(addm(addm(v.x,sa),mulm(sb,z)),invm(4)),r),
            mulm(mulm(v.y,subm(1,mulm(sb,z2))),invm(8)));
}
struct Fold {Pt v;u64 e;};
Fold fold(Pt v,int orbit){if(v.o)return {v,1};
  Fold ret{v,1};
  auto upd=[&](Pt n,u64 c){if(n<ret.v)ret={n,c};};
  upd(neg(v),q-1);
  if(orbit==4){Pt z=pt(v.x? p-v.x:0,mulm(ii,v.y));upd(z,lam);upd(neg(z),q-lam);}
  return ret;
}
struct Solve {u64 dlog,adds,invs,iterations,cycles,states;};
Solve rho(Curve& c, Pt g,Pt h,int orbit,u64 seed){
 std::mt19937_64 rng(seed); u64 iterations=0,cycles=0;
 for(int trial=0;trial<6;trial++){
  struct Jump{Pt j;u64 a,b;}; Jump J[32];
  for(auto& v:J){v.a=rng()%(q-1)+1;v.b=rng()%(q-1)+1;v.j=c.plus(c.times(g,v.a),c.times(h,v.b));}
  u64 a=rng()%(q-1)+1,b=rng()%(q-1)+1;
  Pt t=c.plus(c.times(g,a),c.times(h,b));
  Fold f=fold(t,orbit);t=f.v;a=a*f.e%q;b=b*f.e%q;
  std::unordered_map<Pt,std::pair<u64,u64>,Hash> seen;
  seen.reserve(131072);
  u64 salt=rng();
  for(int step=0;step<200000;step++){
    ++iterations;
    auto it=seen.find(t);u64 idx;
    if(it!=seen.end()){
      auto [aa,bb]=it->second;
      if(bb!=b){
        u64 diff=bb>=b?bb-b:q+bb-b;
        u64 ans=(u128)(a>=aa?a-aa:q+a-aa)*invq(diff)%q; // Solve: aG+bQ=aaG+bbQ => (a-aa)/(bb-b)
        if(c.times(g,ans)!=h)throw std::runtime_error("false rho collision");
        return {ans,c.adds,c.invs,iterations,cycles,(u64)seen.size()};
      }
      ++cycles;
      idx=(Hash{}(t)^salt^rng())&31;
    }else{
      seen.emplace(t,std::pair{a,b});
      idx=(Hash{}(t)^salt)&31;
    }
    t=c.plus(t,J[idx].j);a=(a+J[idx].a)%q;b=(b+J[idx].b)%q;
    f=fold(t,orbit);t=f.v;a=(u128)a*f.e%q;b=(u128)b*f.e%q;
  }
 }
 throw std::runtime_error("rho failed six bounded runs");
}
Solve bsgs(Curve& c,Pt g,Pt h){
 u64 m=(u64)std::ceil(std::sqrt((double)q));
 std::unordered_map<Pt,u64,Hash> baby;baby.reserve(m*2);
 Pt t{};for(u64 j=0;j<m;j++){baby.emplace(t,j);t=c.plus(t,g);}
 Pt jump=neg(c.times(g,m));t=h;
 for(u64 k=0;k<=m;k++){
   auto it=baby.find(t);
   if(it!=baby.end()){
     u64 x=(k*m+it->second)%q;
     if(c.times(g,x)!=h)throw std::runtime_error("false BSGS output");
     return {x,c.adds,c.invs,k,m,m};
   }
   t=c.plus(t,jump);
 }
 throw std::runtime_error("BSGS no solution");
}
Pt G=pt(911976709,415929193),H=pt(180482573,1535800095);
int main(int argc,char**argv){
 try{
  int count=argc>1?std::stoi(argv[1]):24;
  u64 seed=argc>2?std::stoull(argv[2]):20261120;
  if(count<1||count>128)throw std::runtime_error("count out of range");
  Curve src{sa,sb},dst{0,9};
  if(!src.on(G)||!dst.on(H)||!(map2(G)==H)||!src.times(G,q).o||!dst.times(H,q).o)throw std::runtime_error("point/order/isogeny preflight failed");
  if(mulm(ii,ii)!=p-1||lam*lam%q!=q-1||!(dst.times(H,lam)==pt(p-H.x,mulm(ii,H.y))))throw std::runtime_error("CM eigenvalue wrong");
  std::mt19937_64 rng(seed);std::unordered_set<u64> fixture_seen; u64 totals[3]={},a[3]={},iv[3]={},n[3]={},cycles[3]={};
  const char*names[3]={"source_bsgs","source_neg_rho","target_glv_rho"};
  std::cout<<"schema,ct133-native-cm-v1\nseed,"<<seed<<"\ncount,"<<count<<"\n";
  for(int idx=0;idx<count;idx++){
    u64 k=q/8+rng()%(q-q/8-1);
    if(!fixture_seen.insert(k).second)throw std::runtime_error("duplicate public scalar");
    Pt publicQ=src.times(G,k);
    if(!(dst.times(H,k)==map2(publicQ)))throw std::runtime_error("public map mismatch");
    const int sequence[6]={0,1,2,2,1,0};const int rev[6]={2,1,0,0,1,2};
    const int *order=idx%2?rev:sequence;
    for(int o=0;o<6;o++){
      int arm=order[o];Curve cc=arm==2?Curve{0,9}:Curve{sa,sb};
      auto begin=std::chrono::steady_clock::now();
      Pt base=arm==2?map2(G):G;
      Pt point=arm==2?map2(publicQ):publicQ;
      Solve z=arm==0?bsgs(cc,base,point):rho(cc,base,point,arm==2?4:2,seed+19*idx);
      Curve verify{sa,sb};
      if(z.dlog!=k || !(verify.times(G,z.dlog)==publicQ))throw std::runtime_error("known answer mismatch");
      auto nanosec=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-begin).count();
      totals[arm]+=nanosec; a[arm]+=cc.adds+verify.adds;iv[arm]+=cc.invs+verify.invs;n[arm]+=z.iterations;cycles[arm]+=z.cycles;
      std::cout<<"row,"<<idx<<','<<names[arm]<<','<<k<<','<<z.dlog<<','<<publicQ.x<<','<<publicQ.y<<','<<nanosec<<','<<cc.adds+verify.adds<<','<<cc.invs+verify.invs<<','<<z.iterations<<','<<z.cycles<<','<<z.states<<'\n';
    }
  }
  for(int j=0;j<3;j++)std::cout<<"total,"<<names[j]<<','<<totals[j]<<','<<a[j]<<','<<iv[j]<<','<<n[j]<<','<<cycles[j]<<"\n";
  std::cout<<"ratio_best_source_over_target,"<<double(std::min(totals[0],totals[1]))/double(totals[2])<<"\n";
  return 0;
 }catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<"\n";return 1;}
}
