// Independently compare the code-linear solve with every archived right-root match.
#include "../n131_w20_affine_product_recovery_20261017/implicit_core.hpp"

static int lowbit(Fe a){
    if(a.lo)return __builtin_ctzll(a.lo);
    if(a.mid)return 64+__builtin_ctzll(a.mid);
    if(a.hi)return 128+__builtin_ctzll(a.hi);
    return -1;
}
struct LowInverse {
    std::array<Fe,131> row{};
    std::array<uint32_t,131> code{};
    int rank=0;
    void add(Fe p,uint32_t label){
        while(!zero(p)){
            int k=lowbit(p);
            if(zero(row[k])){row[k]=p;code[k]=label;++rank;return;}
            p=xo(p,row[k]);label^=code[k];
        }
        throw std::runtime_error("low basis dependency");
    }
    bool recover(Fe p,uint32_t &label)const{
        label=0;
        while(!zero(p)){
            int k=lowbit(p);
            if(zero(row[k]))return false;
            p=xo(p,row[k]);label^=code[k];
        }
        return true;
    }
};
struct Counts {uint64_t roots=0,reference=0,linear=0,equation_checks=0;
               uint64_t zero=0,exceptional=0,rank_defect=0;};

static Counts check_target(const Field&f,Fe target,const std::vector<Row>&left,
        const std::unordered_map<Fe,Row,FeHash,FeEq>&right,
        const LowInverse&basis,const std::array<Fe,19>&source_basis,
        const std::vector<unsigned char>&valid,
        Fe Crot,Fe Hrot,uint64_t start,uint64_t cap_ns,uint64_t cap_bytes){
    Counts q;Fe one{1,0,0},target2=f.sq(target);
    for(const Row&row:left){
        if((q.roots&1023)==0){
            if(ticks()-start>cap_ns)throw std::runtime_error("AUDIT_WALL_CAP");
            if(rss()>cap_bytes)throw std::runtime_error("AUDIT_RSS_CAP");
        }
        Fe c=row.x,B=f.mul(c,target),A=xo(one,f.sq(B)),D=xo(f.sq(c),target2);
        Fe U=xo(f.mul(Crot,D),f.mul(Hrot,A)),V=f.mul(Hrot,B);
        Fe K=f.mul(A,f.sq(D)),L=f.mul(B,f.mul(U,D));
        Fe R=xo(xo(f.mul(A,f.sq(V)),f.mul(B,f.mul(U,V))),f.mul(D,f.sq(U)));
        if(zero(D)||zero(U))++q.exceptional;
        LowInverse linear;
        for(int j=0;j<19;++j){
            Fe term=xo(f.mul(K,f.sq(source_basis[j])),f.mul(L,source_basis[j]));
            if(zero(term)){++q.rank_defect;break;}
            try{linear.add(term,1U<<j);}
            catch(const std::exception&){++q.rank_defect;break;}
        }
        uint32_t recovered=0;
        bool candidate=linear.rank==19&&linear.recover(R,recovered)&&
                       recovered<(1U<<19)&&valid_code(valid,int(recovered));
        Fe candidate_d{};
        if(candidate){
            if(zero(U)||zero(D))throw std::runtime_error("candidate exceptional");
            Fe p{};for(int j=0;j<19;++j)if(recovered>>j&1)p=xo(p,source_basis[j]);
            candidate_d=f.mul(xo(f.mul(D,p),V),f.inverse(U));
            if(!satisfies(f,A,B,D,candidate_d)||
               !satisfies(f,Crot,p,Hrot,candidate_d))
                throw std::runtime_error("candidate replay");
            auto it=right.find(candidate_d);
            if(it==right.end()||it->second.code!=int(recovered))
                throw std::runtime_error("linear candidate absent from reference");
            ++q.linear;
        }
        int row_reference=0;
        for(Fe d:roots(f,A,B,D)){
            ++q.roots;
            if(!satisfies(f,A,B,D,d))throw std::runtime_error("audit S3 root");
            if(zero(d)){++q.zero;continue;}
            auto ref=right.find(d);
            bool refhit=ref!=right.end();q.reference+=refhit;row_reference+=refhit;
            Fe direct=xo(f.mul(Crot,d),f.mul(Hrot,f.inverse(d)));
            uint32_t code=0;
            bool own=basis.recover(direct,code) && code<(1U<<19) &&
                     valid_code(valid,int(code));
            if(own!=refhit || (own && int(code)!=ref->second.code))
                throw std::runtime_error("candidate membership disagreement");
            Fe equation=xo(xo(f.mul(K,f.sq(direct)),f.mul(L,direct)),R);
            if(!zero(equation))throw std::runtime_error("linearized equation drift");
            ++q.equation_checks;
        }
        if(row_reference!=int(candidate)||
           (candidate&&!eq(candidate_d,right.find(candidate_d)->first)))
            throw std::runtime_error("row-level reference disagreement");
    }
    return q;
}

int main(int argc,char**argv)try{
    if(argc!=7)throw std::runtime_error("usage: audit fixture support valid result cap_seconds rss_cap");
    uint64_t start=ticks(),cap_ns=std::stoull(argv[5])*1000000000ULL;
    uint64_t cap_bytes=std::stoull(argv[6]);
    std::ifstream fixture(argv[1]);
    std::string pzt,ozt,lzt,rzt,extra;int expected_left,expected_right;
    fixture>>pzt>>ozt>>lzt>>rzt>>expected_left>>expected_right;
    if(!fixture||fixture>>extra)throw std::runtime_error("fixture");
    Field f(131);Fe one{1,0,0};
    Fe pos=standard(f,decimal(pzt)),ord=standard(f,decimal(ozt));
    Fe selected_c=standard(f,decimal(lzt));
    Fe selected_d=frob(f,standard(f,decimal(rzt)),18);
    std::vector<int>columns(1<<20,-1);std::ifstream support(argv[2]);
    int mask,column,shift,n=0;
    while(support>>mask>>column>>shift){
        if(mask<0||mask>=int(columns.size())||columns[mask]!=-1||shift<0||shift>=131)
            throw std::runtime_error("support row");
        columns[mask]=column;++n;
    }
    if(!support.eof()||n!=524493)throw std::runtime_error("support count");
    std::ifstream bitmap(argv[3],std::ios::binary);std::vector<unsigned char>valid(1<<16);
    bitmap.read(reinterpret_cast<char*>(valid.data()),valid.size());
    if(!bitmap||bitmap.get()!=EOF)throw std::runtime_error("bitmap");
    Fe s{uint64_t(898618)<<1,0,0},h=halftrace(f,s),H=f.sq(h),C=xo(one,H);
    Fe invC=f.inverse(C),HC=f.mul(H,C),Crot=frob(f,C,18),Hrot=frob(f,H,18);
    std::array<Fe,19>raw_basis{},source_basis{};
    LowInverse basis;
    for(int j=0;j<19;++j){
        Fe w{uint64_t(1)<<(j+1),0,0};
        raw_basis[j]=f.mul(w,xo(w,s));
        source_basis[j]=frob(f,raw_basis[j],18);
        basis.add(source_basis[j],1U<<j);
    }
    if(basis.rank!=19)throw std::runtime_error("basis rank");
    std::vector<Row>left;left.reserve(264090);
    std::unordered_map<Fe,Row,FeHash,FeEq>right;right.reserve(400000);
    int codes=0;
    for(int code=0;code<(1<<19);++code){
        if(!valid_code(valid,code))continue;
        int other=code^898618;
        if(columns[code]<0||columns[other]<0||columns[code]==columns[other])
            throw std::runtime_error("valid source drift");
        Fe p{};for(int j=0;j<19;++j)if(code>>j&1)p=xo(p,raw_basis[j]);
        auto rr=pair_roots(f,p,C,H,invC,HC);
        for(Fe c:rr){
            left.push_back({c,code,columns[code],columns[other]});
            Fe d=frob(f,c,18);
            if(!right.emplace(d,Row{d,code,columns[code],columns[other]}).second)
                throw std::runtime_error("right collision");
        }
        ++codes;
    }
    if(codes!=132045||left.size()!=264090||right.size()!=264090)
        throw std::runtime_error("source table count");
    auto selected=right.find(selected_d);
    bool found_left=false;
    for(const Row&row:left)
        if(row.code==expected_left&&eq(row.x,selected_c))found_left=true;
    if(selected==right.end()||selected->second.code!=expected_right||
       !found_left)
        throw std::runtime_error("selected fixture drift");
    Counts positive=check_target(f,pos,left,right,basis,source_basis,valid,Crot,Hrot,start,cap_ns,cap_bytes);
    Counts ordinary=check_target(f,ord,left,right,basis,source_basis,valid,Crot,Hrot,start,cap_ns,cap_bytes);
    std::ofstream out(argv[4]);if(!out)throw std::runtime_error("result write");
    auto emit=[&](Counts q){out<<"{\"roots\":"<<q.roots<<",\"reference\":"<<q.reference
        <<",\"linear\":"<<q.linear<<",\"equation_checks\":"<<q.equation_checks
        <<",\"zero\":"<<q.zero<<",\"exceptional\":"<<q.exceptional
        <<",\"rank_defect\":"<<q.rank_defect<<"}";};
    out<<"{\"status\":\"PASS_CODE_LINEAR_EQUIVALENCE\",\"codes\":"<<codes
       <<",\"left_roots\":"<<left.size()<<",\"right_roots\":"<<right.size()
       <<",\"elapsed_seconds\":"<<double(ticks()-start)/1e9
       <<",\"peak_rss_bytes\":"<<rss()<<",\"positive\":";
    emit(positive);out<<",\"ordinary\":";emit(ordinary);out<<"}\n";
    if(!out)throw std::runtime_error("result write");
    std::cout<<"PASS_CODE_LINEAR_EQUIVALENCE "<<positive.roots<<" "<<ordinary.roots<<"\n";
    return 0;
}catch(const std::exception&e){std::cerr<<"ERROR "<<e.what()<<"\n";return 1;}
