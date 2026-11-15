#define BUILD_LIBRARY
#include "native_v2.cpp"

int main(int argc,char**argv){
 if(argc!=2)throw std::runtime_error("selftest PUBLIC");
 std::ifstream in(argv[1]);U inputp;Point P,Q;
 in>>inputp>>n>>curveA>>curveB>>P.x>>P.y>>Q.x>>Q.y;assert(inputp==p);P.inf=Q.inf=false;
 std::mt19937_64 rng(20261115);size_t checked=0;
 for(U a:{U(0),U(1),p-1})assert(invf(a)==powf(a,p-2));
 for(size_t j=0;j<10000;j++){
  U a=rng()%p;assert(invf(a)==powf(a,p-2));if(a)assert(mul(a,invf(a))==1);checked++;
 }
 std::vector<U> a(256),b(256);
 for(size_t trial=0;trial<10;trial++){
  for(size_t j=0;j<256;j++){a[j]=trial? rng()%p:p-1;b[j]=trial?rng()%p:p-1;}
  U expected=0;
  for(size_t length=0;length<=256;length++){
   if(length)expected=add(expected,mul(a[length-1],b[length-1]));
   assert(dot(a.data(),b.data(),length)==expected);checked++;
  }
 }
 for(size_t trial=0;trial<10;trial++){
  std::array<Point,64> points,steps,expected;
  for(size_t j=0;j<64;j++){points[j]=times(rng()%n,P);steps[j]=times(rng()%n,Q);}
  points[0]={};steps[1]={};points[2]=steps[2]=P;points[3]=P;steps[3]=neg(P);points[4]=steps[4]={};
  for(size_t j=0;j<64;j++)expected[j]=plus(points[j],steps[j]);
  batchPlus(points,steps);
  for(size_t j=0;j<64;j++){assert(eq(points[j],expected[j]));assert(oncurve(points[j]));checked++;}
 }
 std::cout<<"{\"field_bits\":"<<FIELD_BITS<<",\"checks\":"<<checked<<",\"passed\":true}\n";
}
