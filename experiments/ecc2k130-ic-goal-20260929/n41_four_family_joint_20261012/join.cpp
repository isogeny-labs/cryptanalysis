// Exhaustive exact group join for one prescribed four-seed family tuple.
#define main archived_join_main
#include "../n41_w8_ninepair_join_control_20261012/join9.cpp"
#undef main
#include <bitset>
#include <cstdlib>

struct FamilyState { Point point; std::bitset<128> columns; unsigned id; };

int main(int argc, char** argv) {
 try {
    if (argc != 8) throw std::runtime_error("usage: join pairs.tsv seed0 seed1 seed2 seed3 target_x target_y");
    auto start = std::chrono::steady_clock::now();
    std::array<unsigned,4> seeds{};
    for (int i=0;i<4;++i) seeds[i]=std::stoul(argv[2+i]);
    Point target{std::stoull(argv[6]),std::stoull(argv[7]),false};
    std::ifstream in(argv[1]);
    if (!in) throw std::runtime_error("source missing");
    std::string tag; int slots,targets;
    in>>tag>>slots>>targets;
    if(tag!="ECC2K41_ALLSEED4"||slots!=4||targets!=4) throw std::runtime_error("header mismatch");
    std::array<std::vector<FamilyState>,4> lists;
    uint64_t source_rows=0;
    while(in>>tag) {
      if(tag=="T") { unsigned id;uint64_t x,y;in>>id>>x>>y;continue; }
      if(tag!="S") throw std::runtime_error("row tag");
      unsigned slot,id,a,b,ca,cb,sa,sb;uint64_t x,y;
      in>>slot>>id>>a>>b>>ca>>cb>>sa>>sb>>x>>y;
      if(!in||slot>=4||a>=b||ca>=128||cb>=128||ca==cb||sa>1||sb>1)
        throw std::runtime_error("source row invalid");
      ++source_rows;
      if((a^b)!=seeds[slot]) continue;
      FamilyState s{{x,y,false},{},id};
      s.columns.set(ca);s.columns.set(cb);
      lists[slot].push_back(s);
    }
    if(source_rows!=123808) throw std::runtime_error("source incomplete");
    for(auto& list:lists) if(list.empty()) throw std::runtime_error("empty selected family");
    std::unordered_multimap<Point,uint32_t,Hash> left;
    left.reserve(lists[0].size()*lists[1].size());
    uint64_t left_attempts=0,left_kept=0,right_attempts=0,right_kept=0,hits=0;
    for(unsigned a=0;a<lists[0].size();++a) for(unsigned b=0;b<lists[1].size();++b) {
      ++left_attempts;
      if((lists[0][a].columns&lists[1][b].columns).any()) continue;
      left.emplace(add(lists[0][a].point,lists[1][b].point),(a<<16)|b);
      ++left_kept;
    }
    for(unsigned c=0;c<lists[2].size();++c) for(unsigned d=0;d<lists[3].size();++d) {
      ++right_attempts;
      if((lists[2][c].columns&lists[3][d].columns).any()) continue;
      ++right_kept;
      Point sum=add(lists[2][c].point,lists[3][d].point);
      Point need=add(target,negate(sum));
      auto range=left.equal_range(need);
      for(auto it=range.first;it!=range.second;++it) {
        unsigned a=it->second>>16,b=it->second&65535;
        auto lcols=lists[0][a].columns|lists[1][b].columns;
        auto rcols=lists[2][c].columns|lists[3][d].columns;
        if((lcols&rcols).any()) continue;
        Point check=add(add(add(lists[0][a].point,lists[1][b].point),lists[2][c].point),lists[3][d].point);
        if(!(check==target)) throw std::runtime_error("group replay mismatch");
        ++hits;
        std::cout<<"HIT "<<lists[0][a].id<<" "<<lists[1][b].id<<" "
                 <<lists[2][c].id<<" "<<lists[3][d].id<<"\n";
      }
    }
    std::cout<<"RESULT "<<source_rows<<" "<<lists[0].size()<<" "<<lists[1].size()<<" "
             <<lists[2].size()<<" "<<lists[3].size()<<" "<<left_attempts<<" "
             <<left_kept<<" "<<right_attempts<<" "<<right_kept<<" "<<hits<<" "
             <<elapsed(start)<<"\n";
    return 0;
 } catch(const std::exception& e) {std::cerr<<"ERROR "<<e.what()<<"\n";return 2;}
}
