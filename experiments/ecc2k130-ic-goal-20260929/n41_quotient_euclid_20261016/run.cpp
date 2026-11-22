// Exact-safe Euclidean gate in F[q]/G_p(q), retaining nonunit-pivot code sets.
#include "quotient.hpp"
#include <sys/resource.h>

static uint64_t peak_rss(){
    struct rusage value{};
    if(getrusage(RUSAGE_SELF,&value)!=0)throw std::runtime_error("getrusage");
    return uint64_t(value.ru_maxrss);
}

int main(int argc,char**argv)try{
    if(argc!=5)throw std::runtime_error("usage: quotient tensor codes source result");
    auto started=tick();auto symbolic=read_symbolic(argv[1]);
    std::ifstream codes(argv[2]);std::string tag;int count;
    codes>>tag>>count;
    if(!codes||tag!="N41CODES1"||count!=40)throw std::runtime_error("codes header");
    std::array<Word,40>pvals{},qvals{};
    for(Word&x:pvals)codes>>x;
    for(Word&x:qvals)codes>>x;
    if(!codes)throw std::runtime_error("codes values");
    std::ifstream source(argv[3]);int rows,nbasis,nvalid,npanels;
    source>>tag>>rows>>nbasis>>nvalid>>npanels;
    if(!source||tag!="N41ROOTP1"||rows!=1554||nbasis!=8||nvalid!=40||npanels!=2)
        throw std::runtime_error("source header");
    std::array<Word,8>basis_raw{};
    for(Word&x:basis_raw)source>>x;
    std::array<Word,40>rvalid{};
    for(Word&x:rvalid)source>>x;
    std::array<Word,2>targets{};
    for(Word&x:targets)source>>x;
    Word seed;source>>seed;
    std::array<std::array<bool,40>,40>allowed{};
    for(int n=0;n<rows;++n){
        int p,q;source>>p>>q;
        if(!source||p<0||p>=40||q<0||q>=40||allowed[p][q])
            throw std::runtime_error("source row");
        allowed[p][q]=true;
        Word ignored;for(int k=0;k<8;++k)source>>ignored;
    }
    if(!source)throw std::runtime_error("source rows");
    auto basis=basis_of(basis_raw);
    if(basis.size()!=7)throw std::runtime_error("basis rank");
    constexpr int FIRST=24;
    Poly modulus_q{1};int allowed_q=0;
    for(int j=0;j<40;++j)if(allowed[FIRST][j]){
        modulus_q=pmul(modulus_q,Poly{qvals[j],1});++allowed_q;
    }
    if(allowed_q!=39||!allowed[FIRST][37]||modulus_q.size()!=40)
        throw std::runtime_error("allowed region");
    uint64_t setup_ns=ns(started);
    std::ofstream out(argv[4]);if(!out)throw std::runtime_error("output");
    out<<"{\"status\":\"COMPLETE_N41_QUOTIENT_EUCLID_GATE\",\"first_code_index\":24"
       <<",\"allowed_second_codes\":"<<allowed_q<<",\"setup_ns\":"<<setup_ns
       <<",\"panels\":[";
    for(int panel=0;panel<2;++panel){
        if(panel)out<<",";
        auto panel_start=tick();auto tensor=specialize(symbolic,targets[panel]);
        auto contracted=contract_p(tensor,pvals[FIRST]);
        RPoly h(25);
        for(int k=0;k<25;++k){
            h[k].resize(17);
            for(int j=0;j<17;++j)h[k][j]=contracted[j][k];
            trim(h[k]);
        }
        if(h.back().empty())throw std::runtime_error("H degree");
        auto normal_start=tick();auto inv=pinverse(h.back(),modulus_q);
        if(!inv.unit)throw std::runtime_error("H leading nonunit");
        h=rscale(std::move(h),inv.inverse,modulus_q);
        if(h.size()!=25||h.back()!=Poly{1})throw std::runtime_error("H normalization");
        uint64_t normalize_ns=ns(normal_start);
        out<<"{\"panel\":"<<panel<<",\"chart\":"<<targets[panel]
           <<",\"normalize_ns\":"<<normalize_ns<<",\"ranks\":[";
        for(int rank: {3,7}){
            if(rank==7)out<<",";
            auto reduce_start=tick();RPoly l=rlinearized_rem(h,modulus_q,basis,rank);
            uint64_t reduce_ns=ns(reduce_start);
            auto gate_start=tick();Euclid gate=euclid_gate(h,l,modulus_q);
            uint64_t gate_ns=ns(gate_start);
            std::vector<int>candidates;
            for(int j=0;j<40;++j)if(allowed[FIRST][j]&&peval(gate.suspects,qvals[j])==0)
                candidates.push_back(j);
            if(rank==7&&panel==0&&
               std::find(candidates.begin(),candidates.end(),37)==candidates.end())
                throw std::runtime_error("witness lost");
            out<<"{\"rank\":"<<rank<<",\"remainder_degree_r\":"<<int(l.size())-1
               <<",\"reduce_ns\":"<<reduce_ns<<",\"gate_ns\":"<<gate_ns
               <<",\"unit_pivots\":"<<gate.unit_pivots
               <<",\"splits\":"<<gate.splits
               <<",\"all_suspect_branches\":"<<gate.all_suspect_branches
               <<",\"inverse_ns\":"<<gate.inverse_ns
               <<",\"division_ns\":"<<gate.division_ns
               <<",\"suspect_degree_q\":"<<int(gate.suspects.size())-1
               <<",\"suspect_second_codes\":[";
            for(size_t j=0;j<candidates.size();++j){if(j)out<<",";out<<candidates[j];}
            out<<"]}";
        }
        out<<"],\"panel_ns\":"<<ns(panel_start)<<"}";
    }
    out<<"],\"peak_rss_bytes\":"<<peak_rss()
       <<",\"worker_ns\":"<<ns(started)<<"}\n";
    std::cout<<"COMPLETE_N41_QUOTIENT_EUCLID_GATE\n";
}catch(const std::exception&e){std::cerr<<"ERROR "<<e.what()<<"\n";return 1;}
