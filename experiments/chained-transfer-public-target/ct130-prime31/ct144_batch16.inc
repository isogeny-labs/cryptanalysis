constexpr int LANES16=16;
using StateArray16=std::array<Point,LANES16>;
// Exactly one field inversion for an active group of <=32 affine additions.
StateArray16 batch_plus16(Curve &c,const StateArray16 &points,const StateArray16 &jumps){
 StateArray16 out{};std::array<U,LANES16> numerator{},denominator{},prefix{};
 std::array<bool,LANES16> active{};
 U product=1;int cnt=0;
 for(int i=0;i<LANES16;i++){
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
 for(int i=LANES16-1;i>=0;i--){
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
Solve rho_batch16(Curve&c,Point g,Point h,bool target,U seed){
 std::mt19937_64 rng(seed);U total_iterations=0,total_cycles=0;
 for(int trial=0;trial<6;trial++){
   struct Jump{Point value;U a,b;};Jump jumps[32];
   for(auto &v:jumps){
     v.a=rng()%(Q-1)+1;v.b=rng()%(Q-1)+1;
     v.value=c.plus(c.times(g,v.a),c.times(h,v.b));
   }
   StateArray16 t{};std::array<U,LANES16> aa{},bb{};
   for(int lane=0;lane<LANES16;lane++){
     aa[lane]=rng()%(Q-1)+1;bb[lane]=rng()%(Q-1)+1;
     auto v=c.plus(c.times(g,aa[lane]),c.times(h,bb[lane]));
     auto f=fold(v,target);t[lane]=f.v;
     aa[lane]=(W)aa[lane]*f.e%Q;bb[lane]=(W)bb[lane]*f.e%Q;
   }
   std::unordered_map<Point,std::pair<U,U>,Hash> seen;
   seen.reserve(131072);U salt=rng();
   // 6250*32=200000 exact transitions per trial.
   for(int round=0;round<12500;round++){
     std::array<int,LANES16> jj{};StateArray16 to_add{};
     for(int lane=0;lane<LANES16;lane++){
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
     StateArray16 next=batch_plus16(c,t,to_add);
     for(int lane=0;lane<LANES16;lane++){
       aa[lane]=(aa[lane]+jumps[jj[lane]].a)%Q;
       bb[lane]=(bb[lane]+jumps[jj[lane]].b)%Q;
       auto f=fold(next[lane],target);
       t[lane]=f.v;aa[lane]=(W)aa[lane]*f.e%Q;bb[lane]=(W)bb[lane]*f.e%Q;
     }
   }
 }
 throw std::runtime_error("batched rho 6 trials exhausted");
}
