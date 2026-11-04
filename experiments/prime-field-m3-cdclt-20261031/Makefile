CXX ?= c++
CXXFLAGS ?= -O2 -std=c++20 -Wall -Wextra -Wpedantic -Werror

.PHONY: all check check-sanitize clean

all: development_oracle

development_oracle: development_oracle.cpp
	$(CXX) $(CXXFLAGS) $< -o $@

check: development_oracle
	./development_oracle --self-test
	./development_oracle --sizing >/dev/null

check-sanitize:
	$(CXX) -O1 -g -std=c++20 -Wall -Wextra -Wpedantic -Werror \
		-fsanitize=address,undefined -fno-omit-frame-pointer \
		development_oracle.cpp -o development_oracle_sanitize
	./development_oracle_sanitize --self-test
	./development_oracle_sanitize --sizing >/dev/null

clean:
	rm -f development_oracle development_oracle_sanitize
