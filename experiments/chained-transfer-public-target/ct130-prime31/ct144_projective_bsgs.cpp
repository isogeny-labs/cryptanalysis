// CT144 producer: projective/batch-normalized BSGS, C++17; [pcc:unverified].
// Prior math/protocol: CT144_PROJECTIVE_BSGS_PROTOCOL.md (commit ebcc7b50).
// CT135 native source and CT136 batched rho source are byte-pinned in build_ct144.py.
#include <limits>
#include <array>
#include <vector>
#include <sstream>
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wreturn-type"
#define main ct135_unused_main
#include "ct135_native.cpp"
#undef main
#pragma GCC diagnostic pop
#include "ct144_batch4.inc"
#include "ct144_batch16.inc"
struct JP {U X=0,Y=1,Z=0;};
JP jp(Point p){return p.inf?JP{}:JP{p.x,p.y,1};}
JP jdbl(JP p,const Curve &c){
 if(!p.Z||!p.Y)return {};
 U zz=mul(p.Z,p.Z),yy=mul(p.Y,p.Y),yyyy=mul(yy,yy);
 U m=add(add(mul(3,mul(p.X,p.X)),mul(2,mul(c.a,mul(p.X,zz)))),mul(c.b,mul(zz,zz)));
 U s=mul(4,mul(p.X,yy)),z=mul(2,mul(p.Y,p.Z));
 U x=sub(sub(mul(m,m),mul(2,s)),mul(c.a,mul(z,z)));
 U y=sub(mul(m,sub(s,x)),mul(8,yyyy));
 return JP{x,y,z};
}
JP jadd(JP p, Point q,const Curve &c){
 if(!p.Z)return jp(q);
 if(q.inf)return p;
 U zz=mul(p.Z,p.Z), zzz=mul(zz,p.Z);
 U h=sub(mul(q.x,zz),p.X),r=sub(mul(q.y,zzz),p.Y);
 if(!h)return r?JP{}:jdbl(p,c);
 U hh=mul(h,h),hhh=mul(h,hh),v=mul(p.X,hh);
 U x=sub(sub(sub(mul(r,r),mul(c.a,mul(hh,zz))),hhh),mul(2,v));
 U y=sub(mul(r,sub(v,x)),mul(p.Y,hhh));
 return JP{x,y,mul(p.Z,h)};
}
std::vector<Point> normall(const std::vector<JP>&p){
 std::vector<Point> out(p.size());
 std::vector<U> prefix(p.size());U acc=1;
 for(size_t i=0;i<p.size();++i){
   if(!p[i].Z)continue;
   prefix[i]=acc;acc=mul(acc,p[i].Z);
 }
 U back=inv(acc);
 for(size_t j=p.size();j>0;){--j;
   if(!p[j].Z)continue;
   U zinv=mul(back,prefix[j]);back=mul(back,p[j].Z);
   U zz=mul(zinv,zinv);
   out[j]=pt(mul(p[j].X,zz),mul(mul(p[j].Y,zz),zinv));
 }
 if(back!=1)throw std::runtime_error("batch normalize integrity");
 return out;
}
void projective_selftest(){
 Curve c{SA,SB};std::mt19937_64 rng(144044);
 auto eq=[&](JP v,Point w,const char*msg){
   if(normall(std::vector<JP>{v})[0]!=w)throw std::runtime_error(std::string("JP mismatch ")+msg);
 };
 eq(jadd(JP{},G,c),G,"inf plus");
 eq(jadd(jp(G),Point{},c),G,"plus inf");
 eq(jadd(jp(G),neg(G),c),Point{},"inverse");
 eq(jdbl(jp(G),c),c.plus(G,G),"double");
 eq(jadd(jp(G),G,c),c.plus(G,G),"mixed double");
 for(int i=0;i<300;i++){
    U a=rng()%Q,b=rng()%Q;
    Point x=c.times(G,a), y=c.times(G,b);
    JP px=jp(x);
    eq(jadd(px,y,c),c.plus(x,y),"mixed");
    eq(jdbl(px,c),c.plus(x,x),"double generated");
    JP cur{}; std::vector<JP> pts;std::vector<Point> expected;
    for(int j=0;j<5;j++){pts.push_back(cur);expected.push_back(c.times(G,j));cur=jadd(cur,G,c);}
    if(normall(pts)!=expected)throw std::runtime_error("batch sequence mismatch");
 }
 // Second curve has nonzero discriminant and a=0, independently exercised.
 Curve t{0,9};for(int i=0;i<100;i++){
  Point x=t.times(H,rng()%Q), y=t.times(H,rng()%Q);
  eq(jadd(jp(x),y,t),t.plus(x,y),"target mixed");
  eq(jdbl(jp(x),t),t.plus(x,x),"target double");
 }
}
Solve bsgs_proj(Curve &c, Point g, Point h){
 U m=1+U(std::sqrt(double(Q-1)));
 std::vector<JP> bb;bb.reserve(m);JP cur{};
 for(U j=0;j<m;j++){bb.push_back(cur);cur=jadd(cur,g,c);++c.additions;}
 auto baby=normall(bb);
 std::unordered_map<Point,U,Hash> table;table.reserve(m*2);
 for(U j=0;j<m;j++)table.emplace(baby[j],j);
 Point stride=neg(c.times(g,m));
 cur=jp(h);
 // Fixed chunk length; normalizes one chunk at a time without per-step inversion.
 constexpr U CHUNK=256;
 for(U offset=0;offset<=m;offset+=CHUNK){
  std::vector<JP> chunk;chunk.reserve(CHUNK);
  for(U j=offset;j<=m&&j<offset+CHUNK;j++){
    chunk.push_back(cur);cur=jadd(cur,stride,c);++c.additions;
  }
  auto pts=normall(chunk);
  for(U i=0;i<pts.size();i++){
    auto it=table.find(pts[i]);
    if(it==table.end())continue;
    U k=((offset+i)*m+it->second)%Q;
    if(c.times(g,k)!=h)throw std::runtime_error("projective BSGS false hit");
    return {k,offset+i,m,table.size()};
  }
 }
 throw std::runtime_error("projective BSGS exhausted");
}
int main(int argc,char **argv){
 try{
  if(argc!=3)throw std::runtime_error("usage: CT144 COUNT SEED");
  int count=std::stoi(argv[1]);U seed=std::stoull(argv[2]);
  if(count!=32)throw std::runtime_error("frozen target cohort count must be 32");
  projective_selftest();
  Curve verify{SA,SB}, tverify{0,9};
  if(!verify.on(G)||!tverify.on(H)||map2(G)!=H||!verify.times(G,Q).inf||!tverify.times(H,Q).inf)
    throw std::runtime_error("curve/map/order");
  if(mul(II,II)!=P-1||((W)LAM*LAM)%Q!=Q-1||tverify.times(H,LAM)!=pt(P-H.x,mul(II,H.y)))
    throw std::runtime_error("target eigenbasis");
  const char*names[]={"source_affine_bsgs","source_projective_bsgs","source_batch4_rho","target_batch16_rho"};
  U totals[4]{}; std::mt19937_64 rng(seed);std::unordered_set<U> seen;
  std::cout<<"schema,ct144-projective-bsgs-cold-v1\nseed,"<<seed<<"\ncount,"<<count<<"\n";
  for(int i=0;i<count;i++){
    U k=Q/8+rng()%(Q-Q/8-1);
    if(!seen.insert(k).second)throw std::runtime_error("duplicate source scalar");
    Point pub=verify.times(G,k);
    if(map2(pub)!=tverify.times(H,k))throw std::runtime_error("map mismatch");
    const int forward[8]={0,1,2,3,3,2,1,0};
    const int backward[8]={3,2,1,0,0,1,2,3};
    const int*order=i%2?backward:forward;
    for(int j=0;j<8;j++){
      int arm=order[j];bool mapped=(arm==3);Curve c=mapped?Curve{0,9}:Curve{SA,SB};
      U iv0=inversions;
      auto start=std::chrono::steady_clock::now();
      Point gg=mapped?map2(G):G,hh=mapped?map2(pub):pub;
      Solve ans{};
      if(arm==0)ans=bsgs(c,gg,hh);
      else if(arm==1)ans=bsgs_proj(c,gg,hh);
      else if(arm==2)ans=rho_batch4(c,gg,hh,false,seed+19*i);
      else ans=rho_batch16(c,gg,hh,true,seed+19*i);
      Curve post{SA,SB};
      if(ans.log!=k||post.times(G,ans.log)!=pub)throw std::runtime_error("postverify");
      U ns=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-start).count();
      totals[arm]+=ns;
      std::cout<<"row,"<<i<<','<<names[arm]<<','<<k<<','<<ans.log<<','<<pub.x<<','<<pub.y<<','<<ns<<','
       <<c.additions+post.additions<<','<<inversions-iv0<<','<<ans.iterations<<','<<ans.cycles<<','<<ans.states<<'\n';
    }
  }
  for(int arm=0;arm<4;arm++)std::cout<<"total,"<<names[arm]<<','<<totals[arm]<<'\n';
  U best=std::min({totals[0],totals[1],totals[2]});
  std::cout<<"ratio_best_source_over_mapped,"<<double(best)/totals[3]<<'\n';
 }catch(const std::exception&e){std::cerr<<"CT144 ERROR: "<<e.what()<<'\n';return 1;}
}
