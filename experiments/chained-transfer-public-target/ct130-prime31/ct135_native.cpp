// CT135 independent EC affine-ref comparator: fast extended-Euclid inversions.
// Explicit 3-arm cold solve on the CM-isogenous F_p pair from CT133.
// Diagnostic, not signed PCC; cannot substitute for strongest IC/rho/695 benchmark.
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <random>
#include <stdexcept>
#include <unordered_map>
#include <unordered_set>
using U=uint64_t; using W=__uint128_t;
constexpr U P=2147483033ULL,Q=536857417ULL;
constexpr U SA=622683939ULL,SB=2147483024ULL, II=392507391ULL, LAM=390258842ULL;
constexpr U SHIFT=969960860ULL;
struct Point {U x=0,y=0;bool inf=true;
 bool operator==(const Point&v)const{return inf==v.inf&&(inf||(x==v.x&&y==v.y));}
 bool operator!=(const Point&v)const{return !(*this==v);}
 bool operator<(const Point&v)const{return inf!=v.inf?inf:(inf?false:(x!=v.x?x<v.x:y<v.y));}
};
Point pt(U x,U y){return {x,y,false};}
Point neg(Point a){if(!a.inf&&a.y)a.y=P-a.y;return a;}
struct Hash {size_t operator()(const Point &v)const{return (size_t)((v.x*0x9e3779b97f4a7c15ULL)^(v.y<<1)^U(v.inf));}};
U add(U a,U b){U r=a+b;return r>=P?r-P:r;}
U sub(U a,U b){return a>=b?a-b:P+a-b;}
U mul(U a,U b){return (W)a*b%P;}
U inversions=0;
U inv(U x){
 if(!x)throw std::runtime_error("zero field inversion");
 // Extended Euclid with signed 64-bit coefficients, valid p<2^31.
 int64_t t=0,nt=1;int64_t r=P,nr=x;
 while(nr){int64_t d=r/nr;int64_t tmp=t-d*nt;t=nt;nt=tmp;tmp=r-d*nr;r=nr;nr=tmp;}
 if(r!=1)throw std::runtime_error("not invertible");
 ++inversions;return (t<0?t+int64_t(P):t);
}
U invmodq(U a){if(!a)throw std::runtime_error("zero subgroup inverse");
 int64_t t=0,nt=1,r=Q,nr=a;
 while(nr){int64_t d=r/nr,tmp=t-d*nt;t=nt;nt=tmp;tmp=r-d*nr;r=nr;nr=tmp;}
 if(r!=1)throw std::runtime_error("q inverse");
 return U(t<0?t+int64_t(Q):t);
}
struct Curve {U a,b; U additions=0,invs=0;
 Point plus(Point v,Point w){++additions;if(v.inf)return w;if(w.inf)return v;
   if(v.x==w.x&&v.y!=w.y)return {};
   U den,num;
   if(v==w){if(!v.y)return {};den=add(v.y,v.y);
     num=add(add(mul(3,mul(v.x,v.x)),mul(2,mul(a,v.x))),b);
   }else{den=sub(w.x,v.x);num=sub(w.y,v.y);}
   U slope=mul(num,inv(den));++invs;
   U x=sub(sub(sub(mul(slope,slope),a),v.x),w.x);
   U y=sub(mul(slope,sub(v.x,x)),v.y);
   return pt(x,y);
 }
 Point times(Point v,U k){Point r{};while(k){if(k&1)r=plus(r,v);v=plus(v,v);k>>=1;}return r;}
 bool on(Point t)const{return t.inf || mul(t.y,t.y)==add(add(mul(t.x,mul(t.x,t.x)),mul(a,mul(t.x,t.x))),mul(b,t.x));}
};
constexpr U GX=911976709ULL,GY=415929193ULL,HX=180482573ULL,HY=1535800095ULL;
Point G=pt(GX,GY),H=pt(HX,HY);
Point map2(Point v){if(v.inf)return v;if(!v.x)throw std::runtime_error("2-torsion image");
 static const U IV4=inv(4),IV8=inv(8);
 U z=inv(v.x);U z2=mul(z,z);
 return pt(add(mul(add(add(v.x,SA),mul(SB,z)),IV4),SHIFT),mul(mul(v.y,sub(1,mul(SB,z2))),IV8));
}
struct Fold{Point v;U e;};
Fold fold(Point v,bool target){Fold f{v,1};auto upd=[&](Point z,U c){if(z<f.v)f={z,c};};
 upd(neg(v),Q-1);
 if(target&&!v.inf){Point z=pt(v.x?P-v.x:0,mul(II,v.y));upd(z,LAM);upd(neg(z),Q-LAM);}
 return f;
}
struct Solve{U log,iterations,cycles,states;};
Solve rho(Curve&c,Point g,Point h,bool target,U seed){
 std::mt19937_64 rng(seed);U total_iterations=0,total_cycles=0;
 for(int trial=0;trial<6;trial++){
   struct Jump{Point value;U a,b;};Jump jumps[32];
   for(auto&v:jumps){v.a=rng()%(Q-1)+1;v.b=rng()%(Q-1)+1;
     v.value=c.plus(c.times(g,v.a),c.times(h,v.b));}
   U a=rng()%(Q-1)+1,b=rng()%(Q-1)+1;
   Point t=c.plus(c.times(g,a),c.times(h,b));auto f=fold(t,target);
   t=f.v;a=(W)a*f.e%Q;b=(W)b*f.e%Q;
   std::unordered_map<Point,std::pair<U,U>,Hash> seen;
   seen.reserve(131072);U salt=rng();
   for(int step=0;step<200000;step++){
     ++total_iterations;
     auto it=seen.find(t);U j;
     if(it!=seen.end()){
       auto [aa,bb]=it->second;
       if(bb!=b){U diff=bb>=b?bb-b:Q+bb-b;
         U k=(W)(a>=aa?a-aa:Q+a-aa)*invmodq(diff)%Q;
         if(c.times(g,k)!=h)throw std::runtime_error("false rho collision");
         return {k,total_iterations,total_cycles,(U)seen.size()};
       }
       ++total_cycles;j=(Hash{}(t)^salt^rng())&31;
     }else{seen.emplace(t,std::pair{a,b});j=(Hash{}(t)^salt)&31;}
     t=c.plus(t,jumps[j].value);a=(a+jumps[j].a)%Q;b=(b+jumps[j].b)%Q;
     f=fold(t,target);t=f.v;a=(W)a*f.e%Q;b=(W)b*f.e%Q;
   }
 }
 throw std::runtime_error("6 bounded rho trials exhausted");
}
Solve bsgs(Curve&c,Point g,Point h){
 U m=1+U(std::sqrt(double(Q-1)));
 std::unordered_map<Point,U,Hash> baby;baby.reserve(m*2);
 Point t{};for(U j=0;j<m;j++){baby.emplace(t,j);t=c.plus(t,g);}
 Point jump=neg(c.times(g,m));t=h;
 for(U k=0;k<=m;k++){
   auto it=baby.find(t);
   if(it!=baby.end()){
     U x=(k*m+it->second)%Q;
     if(c.times(g,x)!=h)throw std::runtime_error("BSGS answer mismatch");
     return {x,k,m,m};
   }
   t=c.plus(t,jump);
 }
 throw std::runtime_error("BSGS exhausted");
}
int main(int argc,char**argv){
 try{
   int count=argc>1?std::stoi(argv[1]):24;
   U seed=argc>2?std::stoull(argv[2]):20261210;
   if(count<1||count>128)throw std::runtime_error("count bound");
   Curve source{SA,SB},target{0,9};
   if(!source.on(G)||!target.on(H)||map2(G)!=H||!source.times(G,Q).inf||!target.times(H,Q).inf)
     throw std::runtime_error("preflight bad curve or order");
   if(mul(II,II)!=P-1||((W)LAM*LAM)%Q!=Q-1||
      target.times(H,LAM)!=pt(P-H.x,mul(II,H.y)))throw std::runtime_error("CM mismatch");
   const char*names[3]={"source_bsgs","source_neg_rho","target_glv_rho"};
   std::mt19937_64 rng(seed);std::unordered_set<U> scalars;U sums[3]={};
   std::cout<<"schema,ct135-fast-inversion-v1\nseed,"<<seed<<"\ncount,"<<count<<"\n";
   for(int i=0;i<count;i++){
     U k=Q/8+rng()%(Q-Q/8-1);
     if(!scalars.insert(k).second)throw std::runtime_error("duplicate target");
     Point pub=source.times(G,k);
     if(target.times(H,k)!=map2(pub))throw std::runtime_error("map homomorphism mismatch");
     int forward[6]={0,1,2,2,1,0};int backward[6]={2,1,0,0,1,2};
     int *order=i%2?backward:forward;
     for(int j=0;j<6;j++){
       int arm=order[j];Curve c=arm==2?Curve{0,9}:Curve{SA,SB};
       auto start=std::chrono::steady_clock::now();
       Point g=arm==2?map2(G):G;
       Point h=arm==2?map2(pub):pub;
       Solve sol=arm==0?bsgs(c,g,h):rho(c,g,h,arm==2,seed+19*i);
       Curve verify{SA,SB};
       if(sol.log!=k||verify.times(G,sol.log)!=pub)throw std::runtime_error("postverify");
       U ns=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-start).count();
       sums[arm]+=ns;
       std::cout<<"row,"<<i<<','<<names[arm]<<','<<k<<','<<sol.log<<','<<pub.x<<','<<pub.y<<','
         <<ns<<','<<c.additions+verify.additions<<','<<c.invs+verify.invs<<','<<sol.iterations<<','
         <<sol.cycles<<','<<sol.states<<'\n';
     }
   }
   for(int arm=0;arm<3;arm++)std::cout<<"total,"<<names[arm]<<','<<sums[arm]<<"\n";
   std::cout<<"ratio_best_source_over_target,"<<double(std::min(sums[0],sums[1]))/sums[2]<<"\n";
 }catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<'\n';return 1;}
}
