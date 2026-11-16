// CT136 source/target batch32 cold ECDLP control, [pcc:unverified].
// Includes exact unchanged CT135 baseline source blob 4d94fc9163e86689a09c6d6685dd017c5c4c9698.
// CT136_PROTOCOL.md committed before the 20261230–33 holdout sample run.
#include <array>
#include <vector>
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wreturn-type"
#define main ct135_reference_entrypoint
#include "ct135_native.cpp"
#undef main
#pragma GCC diagnostic pop
// The scalar inversion count in CSV is a code-path count, not a timed primitive:
// CT135 rho() / CT136 rho_batch() return on exactly one invmodq call; BSGS uses none.
constexpr int LANES=32;
using StateArray=std::array<Point,LANES>;
// Exactly one field inversion for an active group of <=32 affine additions.
StateArray batch_plus(Curve &c,const StateArray &points,const StateArray &jumps){
 StateArray out{};std::array<U,LANES> numerator{},denominator{},prefix{};
 std::array<bool,LANES> active{};
 U product=1;int cnt=0;
 for(int i=0;i<LANES;i++){
   ++c.additions;
   Point v=points[i],w=jumps[i];
   if(v.inf){out[i]=w;continue;}
   if(w.inf){out[i]=v;continue;}
   if(v.x==w.x&&v.y!=w.y){out[i]={};continue;}
   U n,d;
   if(v==w){
     if(!v.y){out[i]={};continue;}
     d=add(v.y,v.y);
     n=add(add(mul(3,mul(v.x,v.x)),mul(2,mul(c.a,v.x))),c.b);
   }else{d=sub(w.x,v.x);n=sub(w.y,v.y);}
   if(!d)throw std::runtime_error("batch denominator zero");
   numerator[i]=n;denominator[i]=d;prefix[i]=product;
   product=mul(product,d);active[i]=true;cnt++;
 }
 if(!cnt)return out;
 U inverse=inv(product);++c.invs;
 for(int i=LANES-1;i>=0;i--){
   if(!active[i])continue;
   U invdi=mul(inverse,prefix[i]);inverse=mul(inverse,denominator[i]);
   U slope=mul(numerator[i],invdi);
   Point v=points[i],w=jumps[i];
   U nx=sub(sub(sub(mul(slope,slope),c.a),v.x),w.x);
   U ny=sub(mul(slope,sub(v.x,nx)),v.y);
   out[i]=pt(nx,ny);
 }
 if(inverse!=1)throw std::runtime_error("batch inverse product integrity");
 return out;
}
// A complete rho solve, not a throughput-only microbenchmark.
// Collision book is shared across 32 independently seeded lanes.
Solve rho_batch(Curve&c,Point g,Point h,bool target,U seed){
 std::mt19937_64 rng(seed);U total_iterations=0,total_cycles=0;
 for(int trial=0;trial<6;trial++){
   struct Jump{Point value;U a,b;};Jump jumps[32];
   for(auto &v:jumps){
     v.a=rng()%(Q-1)+1;v.b=rng()%(Q-1)+1;
     v.value=c.plus(c.times(g,v.a),c.times(h,v.b));
   }
   StateArray t{};std::array<U,LANES> aa{},bb{};
   for(int lane=0;lane<LANES;lane++){
     aa[lane]=rng()%(Q-1)+1;bb[lane]=rng()%(Q-1)+1;
     auto v=c.plus(c.times(g,aa[lane]),c.times(h,bb[lane]));
     auto f=fold(v,target);t[lane]=f.v;
     aa[lane]=(W)aa[lane]*f.e%Q;bb[lane]=(W)bb[lane]*f.e%Q;
   }
   std::unordered_map<Point,std::pair<U,U>,Hash> seen;
   seen.reserve(131072);U salt=rng();
   // 6250*32=200000 exact transitions per trial.
   for(int round=0;round<6250;round++){
     std::array<int,LANES> jj{};StateArray to_add{};
     for(int lane=0;lane<LANES;lane++){
       ++total_iterations;
       auto it=seen.find(t[lane]);
       if(it!=seen.end()){
         auto [a0,b0]=it->second;
         if(b0!=bb[lane]){
           U diff=b0>=bb[lane]?b0-bb[lane]:Q+b0-bb[lane];
           U k=(W)(aa[lane]>=a0?aa[lane]-a0:Q+aa[lane]-a0)*invmodq(diff)%Q;
           if(c.times(g,k)!=h)throw std::runtime_error("batch rho invalid collision");
           return {k,total_iterations,total_cycles,(U)seen.size()};
         }
         ++total_cycles;jj[lane]=int((Hash{}(t[lane])^salt^rng())&31);
       }else{seen.emplace(t[lane],std::pair{aa[lane],bb[lane]});
         jj[lane]=int((Hash{}(t[lane])^salt)&31);}
       to_add[lane]=jumps[jj[lane]].value;
     }
     StateArray next=batch_plus(c,t,to_add);
     for(int lane=0;lane<LANES;lane++){
       aa[lane]=(aa[lane]+jumps[jj[lane]].a)%Q;
       bb[lane]=(bb[lane]+jumps[jj[lane]].b)%Q;
       auto f=fold(next[lane],target);
       t[lane]=f.v;aa[lane]=(W)aa[lane]*f.e%Q;bb[lane]=(W)bb[lane]*f.e%Q;
     }
   }
 }
 throw std::runtime_error("batched rho 6 trials exhausted");
}
int main(int argc,char**argv){
 try{
   int count=argc>1?std::stoi(argv[1]):8;
   U seed=argc>2?std::stoull(argv[2]):20261210;
   if(count<1||count>64)throw std::runtime_error("count bound 1..64");
   Curve source{SA,SB},target{0,9};
   if(!source.on(G)||!target.on(H)||map2(G)!=H||!source.times(G,Q).inf||!target.times(H,Q).inf)
     throw std::runtime_error("preflight bad curve or order");
   if(mul(II,II)!=P-1||((W)LAM*LAM)%Q!=Q-1||
      target.times(H,LAM)!=pt(P-H.x,mul(II,H.y)))throw std::runtime_error("CM mismatch");
   const char*names[5]={"source_bsgs","source_neg_rho","target_glv_rho", "source_batch32_rho","target_batch32_rho"};
   std::mt19937_64 rng(seed);std::unordered_set<U> scalars;U sums[5]={};
   std::cout<<"schema,ct136-batched-cold-v1\nseed,"<<seed<<"\ncount,"<<count<<"\n";
   for(int i=0;i<count;i++){
     U k=Q/8+rng()%(Q-Q/8-1);
     if(!scalars.insert(k).second)throw std::runtime_error("duplicate target");
     Point pub=source.times(G,k);
     if(target.times(H,k)!=map2(pub))throw std::runtime_error("map homomorphism mismatch");
     const int even[10]={0,1,2,3,4,4,3,2,1,0};
     const int odd[10]={4,3,2,1,0,0,1,2,3,4};
     const int *order=i%2?odd:even;
     for(int j=0;j<10;j++){
       int arm=order[j];bool trg=arm==2||arm==4;
       Curve c=trg?Curve{0,9}:Curve{SA,SB};
       U iv0=inversions;
       auto start=std::chrono::steady_clock::now();
       Point g=trg?map2(G):G;
       Point h=trg?map2(pub):pub;
       Solve sol{};
       if(arm==0)sol=bsgs(c,g,h);
       else if(arm==1||arm==2)sol=rho(c,g,h,trg,seed+19*i);
       else sol=rho_batch(c,g,h,trg,seed+19*i);
       Curve verify{SA,SB};
       if(sol.log!=k||verify.times(G,sol.log)!=pub)throw std::runtime_error("postverify");
       U ns=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-start).count();
       sums[arm]+=ns;
       std::cout<<"row,"<<i<<','<<names[arm]<<','<<k<<','<<sol.log<<','<<pub.x<<','<<pub.y<<','
         <<ns<<','<<c.additions+verify.additions<<','<<inversions-iv0<<','<<(arm?1:0)<<','
         <<sol.iterations<<','<<sol.cycles<<','<<sol.states<<'\n';
     }
   }
   for(int arm=0;arm<5;arm++)std::cout<<"total,"<<names[arm]<<','<<sums[arm]<<"\n";
   U bs=std::min({sums[0],sums[1],sums[3]});U bt=std::min(sums[2],sums[4]);
   std::cout<<"ratio_best_source_over_best_target,"<<double(bs)/bt<<"\n";
   std::cout<<"ratio_source_batch_over_target_batch,"<<double(sums[3])/sums[4]<<"\n";
 }catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<'\n';return 1;}
}
