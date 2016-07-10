import sys
import os
import re
import json


api = json.loads(open(sys.argv[1], "r").read())

# We use gcc. CRAPPY_COMPILER is not defined.
done = 0
while not done:
	done = 1
	for i, d in enumerate(api["defines"]):
		if d["name"] in ["TRUE", "FALSE"]:
			del api["defines"][i]
			done = 0
			break

	# slurm_step_io_fds contains an anonymous structure and three members of that
	# type. This is not properly handled by the parser.
	for i, d in enumerate(api["structs"]):
		if "slurm_step_io_fds" == d["name"]:
			del api["structs"][i]
			done = 0
			break
		if "slurm_trigger_callbacks_t" == d["typedef"]:
			if len(d["members"]) > 0:
				d["members"] = []
				done = 0

# We currently cannot parse slurm_errno.h correctly since the functions are not declared as extern
api["functions"] += [{"name": "slurm_strerror", "args": [{"name": "errnum", "type": "int"}], "retVal": "char *"}]
api["functions"] += [{"name": "slurm_seterrno", "args": [{"name": "errnum", "type": "int"}], "retVal": "void"}]
api["functions"] += [{"name": "slurm_get_errno", "args": [], "retVal": "int"}]
api["functions"] += [{"name": "slurm_perror", "args": [{"name": "msg", "type": "char *"}], "retVal": "void"}]

# # Treat the opaque hostlist_t as a structure with one pointer
# api["structs"] += [{"name": "hostlist_p", "typedef": "hostlist_t", "members": [{"name": "opaqueptr", "type": "void*"}]}]

with open(sys.argv[1], "w") as f:
	f.write(json.dumps(api))

