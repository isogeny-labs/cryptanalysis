// Parse the native-XOR XCNF once, then solve serial branch assumptions.
#include <cryptominisat5/cryptominisat.h>

#include <chrono>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using CMSat::Lit;
using CMSat::SATSolver;

static double seconds_since(std::chrono::steady_clock::time_point start) {
    return std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
}

int main(int argc, char** argv) {
    if (argc != 13) {
        std::cerr << "usage: incremental XCNF MODEL_PREFIX CPU_SECONDS FIRST LAST WIRE0 ... WIRE6\n";
        return 2;
    }
    const std::string formula = argv[1], model_prefix = argv[2];
    const double cpu_seconds = std::stod(argv[3]);
    const int first = std::stoi(argv[4]), last = std::stoi(argv[5]);
    if (cpu_seconds <= 0 || first < 0 || last > 128 || first >= last) return 2;
    std::vector<unsigned> wires;
    for (int i = 6; i < 13; ++i) {
        int wire = std::stoi(argv[i]);
        if (wire <= 0) return 2;
        wires.push_back(static_cast<unsigned>(wire));
    }
    if (wires.size() != 7) return 2;
    std::ifstream input(formula);
    if (!input) return 3;
    std::string line;
    if (!std::getline(input, line)) return 3;
    std::istringstream header(line);
    std::string p, cnf;
    unsigned variables;
    unsigned long expected_rows;
    if (!(header >> p >> cnf >> variables >> expected_rows) || p != "p" || cnf != "cnf") return 3;
    for (unsigned wire : wires) if (wire > variables) return 3;
    SATSolver solver;
    solver.set_num_threads(1);
    solver.set_verbosity(0);
    solver.new_vars(variables);
    auto load_start = std::chrono::steady_clock::now();
    unsigned long rows = 0, cnf_rows = 0, xor_rows = 0;
    while (std::getline(input, line)) {
        if (line.empty() || line[0] == 'c') continue;
        const bool is_xor = line[0] == 'x';
        std::istringstream stream(is_xor ? line.substr(1) : line);
        std::vector<Lit> literals;
        int value;
        bool ended = false;
        while (stream >> value) {
            if (value == 0) { ended = true; break; }
            if (static_cast<unsigned>(std::abs(value)) > variables) return 4;
            literals.emplace_back(static_cast<unsigned>(std::abs(value) - 1), value < 0);
        }
        if (!ended || literals.empty()) return 4;
        bool okay = is_xor ? solver.add_xor_clause(literals, true) : solver.add_clause(literals);
        if (!okay) return 5;
        ++rows;
        if (is_xor) ++xor_rows; else ++cnf_rows;
    }
    if (rows != expected_rows) return 6;
    std::cout << "LOAD " << variables << ' ' << rows << ' ' << cnf_rows << ' '
              << xor_rows << ' ' << seconds_since(load_start) << std::endl;
    for (int index = first; index < last; ++index) {
        std::vector<Lit> assumptions;
        for (int bit = 0; bit < 7; ++bit)
            assumptions.emplace_back(wires[bit] - 1, (index & (1 << bit)) == 0);
        solver.set_max_time(cpu_seconds);
        auto start = std::chrono::steady_clock::now();
        CMSat::lbool value = solver.solve(&assumptions);
        const char* status = value == CMSat::l_True ? "SAT" :
                             value == CMSat::l_False ? "UNSAT" : "UNKNOWN";
        std::cout << "SLICE " << index << ' ' << status << ' ' << seconds_since(start)
                  << ' ' << solver.get_last_conflicts() << std::endl;
        if (value == CMSat::l_True) {
            const auto& model = solver.get_model();
            if (model.size() != variables) return 7;
            std::ofstream out(model_prefix + std::to_string(index) + ".model");
            if (!out) return 8;
            for (unsigned var = 0; var < variables; ++var) {
                if (model[var] == CMSat::l_Undef) return 9;
                out << (model[var] == CMSat::l_True ? static_cast<int>(var + 1)
                                                    : -static_cast<int>(var + 1)) << '\n';
            }
            out.close();
            std::cout << "MODEL " << index << ' ' << model.size() << std::endl;
            return 0;
        }
    }
    return 0;
}
