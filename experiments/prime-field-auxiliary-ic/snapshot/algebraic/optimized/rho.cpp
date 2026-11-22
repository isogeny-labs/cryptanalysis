// Pollard rho, 32-adding walk with Brent cycle detection and constant memory.
// Exactly the same field, inverse, and point arithmetic as native_v2.cpp.
#define BUILD_LIBRARY
#include "native_v2.cpp"

U pointHash(Point R){
 U x=R.inf?UINT64_MAX:(R.x<<1)|(R.y&1);
 x+=0x9e3779b97f4a7c15ULL;x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;
 x=(x^(x>>27))*0x94d049bb133111ebULL;return x^(x>>31);
}
struct State{Point R;U a,b;};

int main(int argc,char**argv){
 static_assert(FIELD_BITS<=31,"This benchmark is for the full 31-bit target");
 if(argc<4)throw std::runtime_error("usage: rho PUBLIC OUTPUT SEED");
 auto started=std::chrono::steady_clock::now();
 std::ifstream in(argv[1]);U inputp;Point P,Q;
 if(!(in>>inputp>>n>>curveA>>curveB>>P.x>>P.y>>Q.x>>Q.y))throw std::runtime_error("Bad public input");
 assert(inputp==p);P.inf=Q.inf=false;
 assert(oncurve(P)&&oncurve(Q)&&times(n,P).inf&&times(n,Q).inf);
 std::mt19937_64 rng(20261115+std::stoull(argv[3]));U evaluations=0;
 for(size_t restart=0;restart<20;restart++){
  std::array<State,32> table;
  for(auto &s:table){s.a=rng()%n;s.b=rng()%n;s.R=plus(times(s.a,P),times(s.b,Q));}
  U a=rng()%n,b=rng()%n;State tortoise{plus(times(a,P),times(b,Q)),a,b},hare=tortoise;
  auto advance=[&](State &s){
   const auto &step=table[pointHash(s.R)&31];
   s.R=plus(s.R,step.R);s.a=addn(s.a,step.a);s.b=addn(s.b,step.b);evaluations++;
  };
  U power=1,lambda=1;advance(hare);
  while(!eq(tortoise.R,hare.R)){
   if(evaluations>50000000)throw std::runtime_error("Rho step limit");
   if(power==lambda){tortoise=hare;power*=2;lambda=0;}
   advance(hare);lambda++;
  }
  U denominator=(hare.b+n-tortoise.b)%n;
  if(!denominator)continue;
  U k=muln((tortoise.a+n-hare.a)%n,pown(denominator,n-2));
  assert(eq(times(k,P),Q));
  double elapsed=since(started);std::ofstream out(argv[2]);
  out.precision(12);
  out<<"{\"recovered\":"<<k<<",\"total_seconds\":"<<elapsed<<",\"walk_steps\":"<<evaluations
     <<",\"restarts\":"<<restart<<",\"collision_a1\":"<<tortoise.a<<",\"collision_b1\":"<<tortoise.b
     <<",\"collision_a2\":"<<hare.a<<",\"collision_b2\":"<<hare.b
     <<",\"collision_x\":"<<hare.R.x<<",\"collision_y\":"<<hare.R.y<<",\"collision_infinity\":"<<(hare.R.inf?"true":"false")<<"}\n";
  std::cout<<"RHO RECOVERED "<<k<<", steps "<<evaluations<<", seconds "<<elapsed<<"\n";return 0;
 }
 throw std::runtime_error("Rho degenerate collision restart limit");
}
