#define main inherited_bilinear_screen_main
#include "../n41_bilinear_rank_screen_20261013/native.cpp"
#undef main
#include <map>

bool insert(u64 value,std::array<u64,N>& pivots) {
  u64 work=value;
  for(int bit=N-1;bit>=0;bit--)if(work&(1ULL<<bit)) {
    if(pivots[bit])work^=pivots[bit];
    else {pivots[bit]=work;return true;}
  }
  return false;
}
bool contains(u64 value,const std::array<u64,N>& pivots) {
  u64 work=value;
  for(int bit=N-1;bit>=0;bit--)if(work&(1ULL<<bit)) {
    if(!pivots[bit])return false;
    work^=pivots[bit];
  }
  return true;
}
std::vector<u64> region_basis(const std::vector<std::vector<u64>>& families,int free_bits,int region) {
  std::array<u64,N> pivots{};std::vector<u64> result;
  int begin=region<<free_bits,end=(region+1)<<free_bits;
  for(int family=begin;family<end;family++)for(u64 value:families[family])
    if(insert(value,pivots))result.push_back(value);
  return result;
}
struct Screen {int cross_rank;bool consistent;int total_rank;};
Screen screen(const std::vector<u64>& left,const std::vector<u64>& right,u64 target) {
  std::array<u64,N> cross{},all{};
  for(u64 c:left)insert(sq(c),all);
  for(u64 d:right)insert(sq(d),all);
  for(u64 c:left)for(u64 d:right) {
    u64 z=mul(mul(target,c),d);
    u64 term=sq(z)^z;
    insert(term,cross);insert(term,all);
  }
  int rc=0,ra=0;
  for(auto value:cross)rc+=value!=0;
  for(auto value:all)ra+=value!=0;
  return {rc,contains(sq(target),all),ra};
}

