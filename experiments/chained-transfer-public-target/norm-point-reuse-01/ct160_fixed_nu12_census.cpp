// CT160: independent exhaustive fixed nu12 F_(223^3) source/target census.
// No Rust, no Sage, no CT158 point counter imports. [pcc:unverified]
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <vector>

namespace {
constexpr int prime=223;
constexpr std::int64_t field_size=std::int64_t(prime)*prime*prime;
struct K { std::array<int,3> a; };
K from_index(std::int64_t x) { return {{{int(x%prime),int((x/prime)%prime),int(x/(prime*prime))}}}; }
std::int64_t index(K x) {return x.a[0] + std::int64_t(prime)*x.a[1] + std::int64_t(prime)*prime*x.a[2];}
K plus(K x,K y) {for(int i=0;i<3;i++) x.a[i]=(x.a[i]+y.a[i])%prime; return x;}
K multiply(K x,K y) {
  int c0=x.a[0]*y.a[0]+3*(x.a[1]*y.a[2]+x.a[2]*y.a[1]);
  int c1=x.a[0]*y.a[1]+x.a[1]*y.a[0]+3*x.a[2]*y.a[2];
  int c2=x.a[0]*y.a[2]+x.a[1]*y.a[1]+x.a[2]*y.a[0];
  return {{{c0%prime,c1%prime,c2%prime}}};
}
bool is_zero(K a) {return a.a[0]==0 && a.a[1]==0 && a.a[2]==0;}
struct Census {std::int64_t zeros=0,nonzero_squares=0,nonsquares=0;
   std::int64_t order() const {return 1+zeros+2*nonzero_squares;}
};
Census census(K A,K B,const std::vector<std::uint8_t>& square) {
  Census c;
  for(std::int64_t i=0;i<field_size;i++) {
    const K x=from_index(i);
    const K fx=plus(multiply(x,plus(multiply(x,x),A)),B);
    if(is_zero(fx)) c.zeros++;
    else if(square[index(fx)]) c.nonzero_squares++;
    else c.nonsquares++;
  }
  if(c.zeros+c.nonzero_squares+c.nonsquares!=field_size) throw std::runtime_error("classification incomplete");
  return c;
}
void print_census(const char *key,Census x) {
  std::printf("\"%s\":{\"zeros\":%lld,\"nonzero_squares\":%lld,\"nonsquares\":%lld,\"order\":%lld}",
    key,(long long)x.zeros,(long long)x.nonzero_squares,(long long)x.nonsquares,(long long)x.order());
}
}
int main(int argc,char**argv) {
  if(argc>2 || (argc==2 && std::strcmp(argv[1],"--mutate-source-B0")!=0)) return 2;
  const bool mutant=argc==2;
  // Fixed actual nu12 models from the public twisted-pair native render-data.json,
  // NOT the twist of the original CT152 curve (different model).
  const K sourceA{{167,76,41}},sourceB{{27+(mutant?1:0),91,187}};
  const K targetA{{207,175,148}},targetB{{175,89,34}};
  // Explicit twist of CT152 short curve included as independent cross-control.
  const K controlA{{42,220,84}},controlB{{133,57,165}};
  std::vector<std::uint8_t> square(field_size,0);
  for(std::int64_t i=0;i<field_size;i++) square[index(multiply(from_index(i),from_index(i)))]=1;
  std::int64_t sqcount=0;for(auto bit:square) sqcount+=bit;
  if(sqcount!=(field_size+1)/2) throw std::runtime_error("wrong square roster");
  const Census src=census(sourceA,sourceB,square);
  const Census dst=census(targetA,targetB,square);
  const Census ctl=census(controlA,controlB,square);
  std::printf("{\"schema\":\"ct160-fixed-nu12-whole-field-census/v1\",\"field_cardinality\":%lld,\"square_roster_cardinality\":%lld,",(long long)field_size,(long long)sqcount);
  print_census("actual_fixed_nu12_source",src);std::printf(",");
  print_census("actual_fixed_nu12_target",dst);std::printf(",");
  print_census("independent_explicit_original_twist_control",ctl);
  const bool accepted = !mutant && src.order()==11086844 && dst.order()==11086844 && ctl.order()==11086844;
  const bool rejected = mutant && src.order()!=11086844 && dst.order()==11086844 && ctl.order()==11086844;
  std::printf(",\"mutant\":%s,\"accepted\":%s,\"mutation_rejected\":%s}\n",mutant?"true":"false",accepted?"true":"false",rejected?"true":"false");
  return (accepted||rejected)?0:1;
}
