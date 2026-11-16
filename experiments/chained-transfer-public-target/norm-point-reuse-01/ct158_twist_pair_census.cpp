// CT158: independent exhaustive cubic-field point census for an original
// translated q223 elliptic model and its explicitly constructed nu=12 twist.
// No Rust implementation, point-order oracle, elliptic scalar, or native fixture.
// Scientific standing [pcc:unverified].
#include <cstdint>
#include <cstdio>
#include <vector>
#include <algorithm>
#include <cstring>
#include <stdexcept>
struct F { int c[3]; };
constexpr int P=223, NONRESIDUE=3;
constexpr int64_t KSIZE=int64_t(P)*P*P;
static F mul(F a, F b) {
  int t[5]{};
  for (int i=0;i<3;i++) for (int j=0;j<3;j++) t[i+j]+=a.c[i]*b.c[j];
  t[1]+=NONRESIDUE*t[4]; t[0]+=NONRESIDUE*t[3];
  return {{t[0]%P,t[1]%P,t[2]%P}};
}
static F add(F a,F b) {return {{(a.c[0]+b.c[0])%P,(a.c[1]+b.c[1])%P,(a.c[2]+b.c[2])%P}};}
static F elem(int64_t i) { return {{int(i%P),int((i/P)%P),int(i/(P*P))}}; }
static int64_t encode(F a){return a.c[0]+int64_t(P)*a.c[1]+int64_t(P)*P*a.c[2];}
static bool zero(F a){return a.c[0]==0&&a.c[1]==0&&a.c[2]==0;}
struct Count {int64_t zeros=0,squares=0,nonsquares=0,order=1;};
static Count count_points(F A,F B,const std::vector<uint8_t>& sq) {
  Count r;
  for(int64_t i=0;i<KSIZE;i++) {
    F x=elem(i);
    F xx=mul(x,x);
    F rhs=add(add(mul(x,xx),mul(A,x)),B);
    if(zero(rhs)){r.zeros++;r.order++;}
    else if(sq[encode(rhs)]){r.squares++;r.order+=2;}
    else r.nonsquares++;
  }
  if(r.zeros+r.squares+r.nonsquares!=KSIZE || r.order!=1+r.zeros+2*r.squares)
    throw std::runtime_error("census partition failed");
  return r;
}
static void row(const char* name,Count a){
  std::printf("\"%s\":{\"zero_rhs\":%lld,\"nonzero_square_rhs\":%lld,\"nonsquare_rhs\":%lld,\"group_order\":%lld}",name,(long long)a.zeros,(long long)a.squares,(long long)a.nonsquares,(long long)a.order);
}
int main(int argc,char**argv){
  if(argc>2 || (argc==2 && strcmp(argv[1],"--mutate-twist-b")!=0)) return 2;
  const bool mutation=argc==2;
  // Formula: x= X - a2/3, A=a4-a2^2/3, B=a6-a2*a4/3+2*a2^3/27.
  // Derived from original a2=[127,56,199],a4=[152,35,36],a6=[212,109,150].
  const F A={{214,144,205}}, B={{137,218,9}};
  // Twist by nonsquare v=12: E_v: y^2=x^3+v^2*A*x+v^3*B.
  const F TA={{42,220,84}}, TB={{133+(mutation?1:0),57,165}};
  std::vector<uint8_t> squares(KSIZE,0);
  for(int64_t i=0;i<KSIZE;i++) squares[encode(mul(elem(i),elem(i)))]=1;
  const auto roster=std::count(squares.begin(),squares.end(),uint8_t(1));
  Count original=count_points(A,B,squares),twist=count_points(TA,TB,squares);
  bool paired=(original.order+twist.order==2*(KSIZE+1));
  bool exact=(original.order==11092292 && twist.order==11086844 && paired);
  std::printf("{\"schema\":\"ct158-twist-pair-census/v1\",\"field_cardinality\":%lld,\"square_roster\":%lld,",(long long)KSIZE,(long long)roster);
  row("original_short",original);std::printf(",");row("twist12",twist);
  std::printf(",\"twist_sum_identity\":%s,\"mutation\":%s,\"nominal_exact\":%s}\n",paired?"true":"false",mutation?"true":"false",exact?"true":"false");
  if(roster!=(KSIZE+1)/2) return 1;
  if(mutation) return (!paired && original.order==11092292 && twist.order!=11086844)?0:1;
  return exact?0:1;
}
