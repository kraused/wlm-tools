
SLURM = /usr

CC       = /usr/bin/gcc
CPPFLAGS = -I$(SLURM)/include -I$(HOME)/Python-2.7.11/include
CCFLAGS  = -std=gnu99 -Wall -fPIC -O0 -ggdb
LD       = /usr/bin/gcc
LDFLAGS  = -std=gnu99 -Wall -fPIC -O0 -ggdb -L$(SLURM)/lib/
LIBS     = -lslurm
AR       = /usr/bin/ar

default:	all
all:		slurmpy.so

api.json: parse-slurmh.py fixup.py $(SLURM)/include/slurm/slurm.h
	/usr/bin/python2 parse-slurmh.py $(SLURM)/include/slurm/slurm.h $(SLURM)/include/slurm/slurm_errno.h $@
	/usr/bin/python2 fixup.py $@

slurmpy.c: write-pymodule.py api.json
	/usr/bin/python2 write-pymodule.py api.json $@

slurmpy.so: slurmpy.c
	$(CC) $(CPPFLAGS) $(CCFLAGS) -o $@ $< -shared $(LDFLAGS) $(LIBS)

clean:
	/bin/rm api.json
	/bin/rm slurmpy.c
	/bin/rm slurmpy.so

