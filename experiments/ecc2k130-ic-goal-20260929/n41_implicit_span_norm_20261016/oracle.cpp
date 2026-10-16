// Exact explicit-span residue oracle for one frozen first-code region.
#include "oracle_helpers.hpp"

int main(int argc,char**argv)try{
    if(argc!=5)throw std::runtime_error("usage: oracle tensor codes source output");
    auto start=tick();auto symbolic=read_symbolic(argv[1]);
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
    if(allowed_q!=39||!allowed[FIRST][37])throw std::runtime_error("allowed region");
    auto setup_ns=ns(start);
    std::ofstream out(argv[4]);if(!out)throw std::runtime_error("output");
    out<<"{\"status\":\"PASS_N41_EXPLICIT_SPAN_RESIDUE_ORACLE\",\"first_code_index\":24"
       <<",\"allowed_second_codes\":"<<allowed_q<<",\"setup_ns\":"<<setup_ns
       <<",\"panels\":[";
    for(int panel=0;panel<2;++panel){
        if(panel)out<<",";
        auto panel_start=tick();auto tensor=specialize(symbolic,targets[panel]);
        auto contracted=contract_p(tensor,pvals[FIRST]);
        out<<"{\"panel\":"<<panel<<",\"chart\":"<<targets[panel]<<",\"ranks\":[";
        for(int rank: {3,7}){
            if(rank==7)out<<",";
            std::vector<Word>span{0};
            for(int k=0;k<rank;++k){
                size_t size=span.size();
                for(size_t j=0;j<size;++j)span.push_back(span[j]^basis[k]);
            }
            auto query_start=tick();Poly product{1};
            for(Word r:span)product=pmod(pmul(product,in_q(contracted,r)),modulus_q);
            uint64_t query_ns=ns(query_start);
            std::vector<int>zeros;
            for(int j=0;j<40;++j)if(allowed[FIRST][j]&&peval(product,qvals[j])==0)
                zeros.push_back(j);
            if(rank==7){
                if((panel==0&&zeros!=std::vector<int>{37})||(panel==1&&!zeros.empty()))
                    throw std::runtime_error("archived full-rank hit set");
            }
            out<<"{\"rank\":"<<rank<<",\"span_size\":"<<span.size()
               <<",\"query_ns\":"<<query_ns<<",\"coefficients\":[";
            for(size_t j=0;j<product.size();++j){if(j)out<<",";out<<product[j];}
            out<<"],\"zero_second_codes\":[";
            for(size_t j=0;j<zeros.size();++j){if(j)out<<",";out<<zeros[j];}
            out<<"]}";
        }
        out<<"],\"panel_ns\":"<<ns(panel_start)<<"}";
    }
    out<<"],\"worker_ns\":"<<ns(start)<<"}\n";
    std::cout<<"PASS_N41_EXPLICIT_SPAN_RESIDUE_ORACLE\n";
}catch(const std::exception&e){std::cerr<<"ERROR "<<e.what()<<"\n";return 1;}
