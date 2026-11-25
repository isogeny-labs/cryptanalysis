// One CryptoMiniSat instance; exact first-code assumptions and learned reuse.
#include <cryptominisat5/cryptominisat_c.h>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using Clock=std::chrono::steady_clock;
double elapsed(Clock::time_point t){
    return std::chrono::duration<double>(Clock::now()-t).count();
}

int main(int argc,char**argv){
 try{
    if(argc!=5)throw std::runtime_error("usage: incremental formula.xcnf codes.tsv max_codes per_call_cpu_s");
    const std::string formula_path=argv[1],codes_path=argv[2];
    const int max_codes=std::stoi(argv[3]);const double cpu_cap=std::stod(argv[4]);
    if(max_codes<1||max_codes>40||cpu_cap<=0)throw std::runtime_error("limits");
    std::ifstream codes_file(codes_path);if(!codes_file)throw std::runtime_error("codes file");
    std::string tag;int width;codes_file>>tag>>width;
    if(tag!="W"||width!=7)throw std::runtime_error("codes header");
    std::vector<unsigned> wires(7);
    for(auto&wire:wires){codes_file>>wire;if(wire==0)throw std::runtime_error("zero wire");}
    std::vector<int> codes;int code;
    while(codes_file>>tag>>code){
        if(tag!="C"||code<0||code>=128)throw std::runtime_error("code row");
        codes.push_back(code);
    }
    if(codes.size()!=40)throw std::runtime_error("code count");
    std::ifstream input(formula_path);if(!input)throw std::runtime_error("formula file");
    SATSolver* solver=cmsat_new();if(!solver)throw std::runtime_error("cmsat_new");
    cmsat_set_num_threads(solver,1);
    cmsat_set_verbosity(solver,0);
    cmsat_set_no_bve(solver);
    auto load_start=Clock::now();
    size_t ordinary=0,xors=0;unsigned variables=0,declared=0;
    std::string line;
    while(std::getline(input,line)){
        if(line.empty()||line[0]=='c')continue;
        if(line[0]=='p'){
            std::istringstream row(line);std::string p,cnf;
            row>>p>>cnf>>variables>>declared;
            if(p!="p"||cnf!="cnf"||variables==0)throw std::runtime_error("DIMACS header");
            cmsat_new_vars(solver,variables);
            continue;
        }
        if(!variables)throw std::runtime_error("record before header");
        const bool is_xor=line[0]=='x';
        std::istringstream row(is_xor?line.substr(1):line);
        std::vector<c_Lit> clause;std::vector<unsigned> xorvars;
        int literal=0;bool rhs=true,terminated=false;
        while(row>>literal){
            if(literal==0){terminated=true;break;}
            unsigned var=unsigned(std::abs(literal));
            if(var==0||var>variables)throw std::runtime_error("literal range");
            if(is_xor){xorvars.push_back(var-1);if(literal<0)rhs=!rhs;}
            else clause.push_back(c_Lit{((var-1)<<1)|unsigned(literal<0)});
        }
        if(!terminated)throw std::runtime_error("unterminated record");
        bool okay=is_xor?cmsat_add_xor_clause(solver,xorvars.data(),xorvars.size(),rhs)
                        :cmsat_add_clause(solver,clause.data(),clause.size());
        if(!okay)throw std::runtime_error("base formula inconsistent while loading");
        if(is_xor)++xors;else ++ordinary;
    }
    if(ordinary+xors!=declared||ordinary!=82957||xors!=3689||variables!=31533)
        throw std::runtime_error("formula record counts");
    std::cout<<"LOADED "<<variables<<" "<<ordinary<<" "<<xors<<" "
             <<elapsed(load_start)<<std::endl;
    for(int index=0;index<max_codes;++index){
        code=codes[index];std::vector<c_Lit> assumptions;
        for(int j=0;j<7;++j){
            bool bit=(code>>j)&1;
            assumptions.push_back(c_Lit{((wires[j]-1)<<1)|unsigned(!bit)});
        }
        cmsat_set_max_time(solver,cpu_cap);
        auto start=Clock::now();
        c_lbool outcome=cmsat_solve_with_assumptions(solver,assumptions.data(),assumptions.size());
        const char* status=outcome.x==0?"SAT":outcome.x==1?"UNSAT":"UNKNOWN";
        std::cout<<"CODE "<<code<<" "<<status<<" "<<elapsed(start)<<" "
                 <<index+1<<std::endl;
        if(outcome.x==0){
            slice_lbool model=cmsat_get_model(solver);
            std::cout<<"MODEL ";
            for(size_t j=0;j<model.num_vals;++j)
                std::cout<<char('0'+model.vals[j].x);
            std::cout<<std::endl;
            break;
        }
    }
    cmsat_free(solver);
    return 0;
 }catch(const std::exception&e){std::cerr<<"ERROR "<<e.what()<<std::endl;return 2;}
}
