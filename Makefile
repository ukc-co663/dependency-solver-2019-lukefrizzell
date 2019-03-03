all: deps

deps:   
	./install_deps.sh

test: deps
	./run_tests.sh

clean:
	rm -rf build

reallyclean: clean

.PHONY: all compile test clean reallyclean
