// Exact distinct two-pair sum support for the archived N41 W11 source.
#define main archived_join_main
#include "../n41_w11_fivepair_native_join_20261018/join.cpp"
#undef main
#include <unordered_set>

int main(int argc,char** argv){
    if(argc!=2)throw std::runtime_error("usage: right_support join_input.tsv");
    auto start=std::chrono::steady_clock::now();
    std::ifstream input(argv[1]);
    if(!input)throw std::runtime_error("input open failed");
    std::string tag;int slots,states,targets;
    input>>tag>>slots>>states>>targets;
    if(tag!="W11FIVE"||slots!=5||states!=STATES||targets!=1)
        throw std::runtime_error("input header mismatch");
    std::array<std::array<State,STATES>,5> lists{};
    std::array<std::array<bool,STATES>,5> seen{};
    int state_rows=0,check_rows=0,target_rows=0;
    while(input>>tag){
        if(tag=="T"){
            int index;uint64_t x,y;input>>index>>x>>y;
            if(index!=0||++target_rows!=1||!on_curve({x,y,false}))
                throw std::runtime_error("target row mismatch");
        }else if(tag=="S"){
            int slot,sid,code,branch;uint64_t ma,mb,ca,cb,x,y;
            input>>slot>>sid>>code>>branch>>ma>>mb>>ca>>cb>>x>>y;
            if(slot<0||slot>=5||sid<0||sid>=STATES||branch!=sid%4||
               code<0||code>=1024||mb!=(ma^112)||seen[slot][sid]||
               !on_curve({x,y,false}))throw std::runtime_error("bad source state");
            lists[slot][sid]={{x,y,false},static_cast<uint16_t>(code),ca,cb};
            seen[slot][sid]=true;++state_rows;
        }else if(tag=="C"){
            int64_t x1,y1,x2,y2,x3,y3;
            input>>x1>>y1>>x2>>y2>>x3>>y3;
            Point result=add({uint64_t(x1),uint64_t(y1),false},
                             {uint64_t(x2),uint64_t(y2),false});
            if((x3<0)!=result.infinity||
               (x3>=0&&(result.x!=uint64_t(x3)||result.y!=uint64_t(y3))))
                throw std::runtime_error("archived Sage addition check mismatch");
            ++check_rows;
        }else throw std::runtime_error("unknown input row");
    }
    if(state_rows!=5*STATES||check_rows!=128||target_rows!=1)
        throw std::runtime_error("incomplete input");
    for(const auto& row:seen)for(bool value:row)if(!value)
        throw std::runtime_error("missing source state");
    std::unordered_set<Point,Hash> distinct;
    distinct.max_load_factor(0.8f);
    distinct.reserve(1300000);
    uint64_t compatible_pairs=0,rejected_pairs=0;
    for(int i=0;i<STATES;++i)for(int j=0;j<STATES;++j){
        State a=lists[3][i],b=lists[4][j];
        if(!compatible(a,b)){++rejected_pairs;continue;}
        ++compatible_pairs;
        distinct.insert(add(a.p,b.p));
    }
    if(compatible_pairs!=1258720||rejected_pairs!=4656)
        throw std::runtime_error("archived right-pair count mismatch");
    std::cout<<"{\"status\":\"COMPLETE_N41_RIGHT_SUPPORT\","
             <<"\"states_per_slot\":"<<STATES
             <<",\"addition_checks\":"<<check_rows
             <<",\"compatible_pairs\":"<<compatible_pairs
             <<",\"rejected_pairs\":"<<rejected_pairs
             <<",\"distinct_sums\":"<<distinct.size()
             <<",\"duplicate_pairs\":"<<(compatible_pairs-distinct.size())
             <<",\"wall_seconds\":"<<elapsed(start)<<"}"<<std::endl;
}
