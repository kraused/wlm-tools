
SLURM = /tmp

CC       = /usr/bin/gcc
CPPFLAGS = -I$(SLURM)/include -I$(HOME)/Python-2.7.11/include
CCFLAGS  = -std=gnu99 -Wall -fPIC -O0 -ggdb
CXX      = /usr/bin/g++
# By default clang and llvm are compiled without RTTI. Arch explicitly
# enables RTTI when building clang but Fedora, for example, does not.
CXXFLAGS = -std=c++11 -Wall -fPIC -O0 -ggdb -fno-rtti
LD       = /usr/bin/gcc
LDFLAGS  = -std=gnu99 -Wall -fPIC -O0 -ggdb -L$(SLURM)/lib/
LIBS     = -lslurm -lslurmdb
AR       = /usr/bin/ar

CLANG    = -lclangTooling -lclangFrontendTool -lclangFrontend -lclangDriver -lclangSerialization -lclangCodeGen -lclangParse -lclangSema -lclangStaticAnalyzerFrontend -lclangStaticAnalyzerCheckers -lclangStaticAnalyzerCore -lclangAnalysis -lclangARCMigrate -lclangRewrite -lclangRewriteFrontend -lclangEdit -lclangAST -lclangLex -lclangBasic
LLVM     = $(shell /usr/bin/llvm-config --libs) $(shell /usr/bin/llvm-config --system-libs)


SLURMHDR = $(SLURM)/include/slurm/slurm_errno.h $(SLURM)/include/slurm/slurm.h $(SLURM)/include/slurm/slurmdb.h

default:	all
all:		slurmpy.so

parse-slurmh.py: plugin.so

plugin.so: plugin.cpp
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -o $@ $< -shared $(CLANG) $(LLVM)

api.json: parse-slurmh.py $(SLURM)/include/slurm/slurm.h
	/usr/bin/python2 parse-slurmh.py $(SLURMHDR) $@

slurmpy.c: write-pymodule.py api.json
	/usr/bin/python2 write-pymodule.py api.json $@

slurmpy-macros.c: slurmpy.c
slurmpy-enums.c : slurmpy.c

%.o: %.c
	$(CC) $(CPPFLAGS) $(CCFLAGS) -o $@ -c $<

slurmpy.so: slurmpy.o slurmpy-macros.o slurmpy-enums.o
	$(CC) $(CPPFLAGS) $(CCFLAGS) -o $@ $^ -shared $(LDFLAGS) $(LIBS)

clean:
	-/bin/rm -f api.json
	-/bin/rm -f plugin.so
	-/bin/rm -f slurmpy.c
	-/bin/rm -f slurmpy.o
	-/bin/rm -f slurmpy-*.c
	-/bin/rm -f slurmpy-*.o
	-/bin/rm -f slurmpy.so

