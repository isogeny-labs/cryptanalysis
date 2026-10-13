#include <algorithm>
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <unordered_set>
#include <utility>
#include <vector>
using u64=uint64_t;
constexpr int N=41;
constexpr u64 MOD=(1ULL<<N)|(1ULL<<3)|1;
u64 mul(u64 a,u64 b) { u64 r=0;while(b){if(b&1)r^=a;b>>=1;a<<=1;if(a>>N)a^=MOD;}return r; }
u64 sq(u64 a) {return mul(a,a);}
u64 power(u64 a,u64 e) {u64 r=1;while(e){if(e&1)r=mul(r,a);a=sq(a);e>>=1;}return r;}
u64 inv(u64 a) {assert(a);u64 r=power(a,(1ULL<<N)-2);assert(mul(a,r)==1);return r;}
u64 ht(u64 a) {u64 h=a;for(int i=0;i<(N-1)/2;i++){a=sq(sq(a));h^=a;}return h;}
int tr(u64 a) {u64 h=ht(a),v=sq(h)^h^a;assert(v<2);return int(v);}
std::vector<u64> roots(u64 a,u64 b,u64 c) {
  if(!a) {if(!b) {assert(c);return {};}return {mul(c,inv(b))};}
  if(!b) {u64 v=mul(c,inv(a));for(int i=0;i<N-1;i++)v=sq(v);return {v};}
  u64 scale=mul(b,inv(a));u64 rhs=mul(mul(a,c),inv(sq(b)));
  if(tr(rhs))return {};
  u64 h=ht(rhs);std::vector<u64> out={mul(scale,h),mul(scale,h^1)};
  for(u64 v:out)assert((mul(a,sq(v))^mul(b,v)^c)==0);
  return out;
}
std::vector<u64> load(const char* path) {
  std::ifstream in(path,std::ios::binary);assert(in.good());
  std::vector<u64> out;u64 v;
  while(in.read(reinterpret_cast<char*>(&v),sizeof(v)))out.push_back(v);
  assert(in.eof());assert(std::is_sorted(out.begin(),out.end()));
  assert(std::adjacent_find(out.begin(),out.end())==out.end());return out;
}
void run(const char* name,u64 t,const std::vector<u64>& outputs,
         const std::unordered_set<u64>& outset,const std::unordered_set<u64>& exact) {
  u64 probes=0,relaxed=0,exact_hits=0;
  std::pair<u64,u64> first_exact={0,0};
  for(u64 c:outputs) {
    u64 ct=mul(c,t);
    auto ds=roots(1^sq(ct),ct,sq(c)^sq(t));
    probes+=ds.size();
    for(u64 d:ds) {
      if(c>d || !outset.count(d))continue;
      relaxed++;
      if(exact.count(c)&&exact.count(d)) {
        exact_hits++;
        if(first_exact.first==0)first_exact={c,d};
      }
    }
  }
  std::cout<<"\""<<name<<"\":{\"target_reciprocal\":"<<t
           <<",\"s3_proposals\":"<<probes
           <<",\"relaxed_unordered_hits\":"<<relaxed
           <<",\"exact_unordered_hits\":"<<exact_hits
           <<",\"first_exact\":["<<first_exact.first<<","<<first_exact.second<<"]}";
}
int main(int argc,char** argv) {
  if(argc!=3)return 2;
  auto outputs=load(argv[1]),source=load(argv[2]);
  assert(source.size()==991);assert(outputs.size()==130405);
  std::unordered_set<u64> outset(outputs.begin(),outputs.end());
  std::unordered_set<u64> exact(source.begin(),source.end());
  for(u64 c:source)assert(outset.count(c));
  u64 c=source[0],d=source[1],cd=mul(c,d);
  auto ts=roots(1^sq(cd),cd,sq(c)^sq(d));
  assert(ts.size()==2);
  std::cout<<"{\"status\":\"COMPLETE_NATIVE_JOIN\",\"cases\":{";
  run("constructed",ts[0],outputs,outset,exact);
  std::cout<<",";
  run("public_point_inverse_x",inv(920359962848ULL),outputs,outset,exact);
  std::cout<<"}}\n";
}
