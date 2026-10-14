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

int main(int argc,char**argv) {
  if(argc!=2)return 2;
  const u64 constructed=1515824644274ULL,public_t=1000731834126ULL;
  std::vector<std::vector<u64>> families(2048);
  for(int p=0;p<2048;p++)families[p]=family_basis(p);
  auto started=Clock::now();
  std::ofstream output(argv[1]);assert(output.good());
  output<<"{\"status\":\"COMPLETE_N41_REGION_SPAN_PANEL\",\"levels\":[";
  for(int free_bits=0;free_bits<=11;free_bits++) {
    int regions=2048>>free_bits;
    std::vector<std::vector<u64>> bases; bases.reserve(regions);
    std::map<int,int> histogram;
    for(int region=0;region<regions;region++) {
      bases.push_back(region_basis(families,free_bits,region));
      histogram[int(bases.back().size())]++;
    }
    int sampled=0,public_rejected=0,full_cross=0,constructed_checked=0;
    std::map<int,int> cross_hist;
    if(free_bits<=3) {
      std::mt19937_64 rng(202610131800ULL+free_bits);
      for(int k=0;k<512;k++) {
        int a=int(rng()%regions),b=int(rng()%regions);
        auto result=screen(bases[a],bases[b],public_t);
        sampled++;public_rejected+=!result.consistent;
        full_cross+=result.cross_rank==40;cross_hist[result.cross_rank]++;
      }
      auto control=screen(bases[819>>free_bits],bases[176>>free_bits],constructed);
      assert(control.consistent);constructed_checked=1;
    }
    output<<(free_bits?",":"")<<"{\"free_product_bits\":"<<free_bits
      <<",\"region_count\":"<<regions<<",\"families_per_region\":"<<(1<<free_bits)
      <<",\"min_union_rank\":"<<histogram.begin()->first
      <<",\"max_union_rank\":"<<histogram.rbegin()->first
      <<",\"union_rank_histogram\":{ ";
    bool first=true;
    for(auto [rank,count]:histogram){output<<(first?"":",")<<"\""<<rank<<"\":"<<count;first=false;}
    output<<"},\"sampled_public_region_pairs\":"<<sampled
      <<",\"public_rank_rejects\":"<<public_rejected
      <<",\"full_cross_rank_sampled\":"<<full_cross
      <<",\"constructed_positive_checked\":"<<constructed_checked
      <<",\"sampled_cross_rank_histogram\":{ ";
    first=true;
    for(auto [rank,count]:cross_hist){output<<(first?"":",")<<"\""<<rank<<"\":"<<count;first=false;}
    output<<"}}";
  }
  output<<"],\"public_target_reciprocal\":"<<public_t
    <<",\"constructed_target_reciprocal\":"<<constructed<<"}\n";
  auto seconds=std::chrono::duration<double>(Clock::now()-started).count();
  std::cout<<"COMPLETE_N41_REGION_SPAN_PANEL seconds="<<seconds<<"\n";
}
