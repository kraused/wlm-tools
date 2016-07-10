
import sys
import os
import time

import ctypes
ctypes.PyDLL(os.getcwd() + "/slurmpy.so", ctypes.RTLD_GLOBAL)

import gc

import slurmpy

def sbatch(name, nnodes, timeLimit, script, environ, argv):
	desc = slurmpy.job_desc_msg_t()
	resp = slurmpy.submit_response_msg_t_PTR()

	slurmpy.slurm_init_job_desc_msg(desc)

	desc.min_nodes = nnodes 
	desc.max_nodes = nnodes

	desc.time_limit = timeLimit
	desc.time_min   = timeLimit

	desc.name = name

	desc.std_in  = "/dev/null"
	desc.std_out = "%s.out" % name
	desc.std_err = "%s.out" % name

	desc.environment = slurmpy.convert_list_to_string_PTR([(k + "=" + environ[k]) for k in sorted(environ.keys())] + [None])
	desc.env_size = len(environ.keys())

	desc.argv = slurmpy.convert_list_to_string_PTR(argv + [None])
	desc.argc = len(argv)

	desc.work_dir = os.getcwd()

	desc.user_id  = os.getuid()
	desc.group_id = os.getgid()

	desc.script = script
	err = slurmpy.slurm_submit_batch_job(desc, resp)

	if err:
		raise Exception("slurm_submit_batch_job() failed: %d (%s)" % (slurmpy.errno, slurmpy.slurm_strerror(slurmpy.errno)))

	return resp[0].job_id

def queryJob(jobId):
	msg = slurmpy.job_info_msg_t_PTR()
	err = slurmpy.slurm_load_job(msg, jobId, slurmpy.SHOW_DETAIL | slurmpy.SHOW_ALL)

	if err:
		raise Exception("slurm_load_job() failed: %d (%s)" % (slurmpy.errno, slurmpy.slurm_strerror(slurmpy.errno)))

	return msg[0].job_array[0]

def queryJobs(jobIds):
	msg = slurmpy.job_info_msg_t_PTR()
	err = slurmpy.slurm_load_job_user(msg, os.getuid(), slurmpy.SHOW_DETAIL | slurmpy.SHOW_ALL)

	if err:
		raise Exception("slurm_load_job_user() failed: %d (%s)" % (slurmpy.errno, slurmpy.slurm_strerror(slurmpy.errno)))

	jobInfos = [None]*len(jobIds)
	for i, jobId in enumerate(jobIds):
		for j in range(msg[0].record_count):
			if jobId == msg[0].job_array[j].job_id:
				jobInfos[i] = msg[0].job_array[j]
				break

	return jobInfos

def jobIsFinished(jobInfo):
	meansDone = [slurmpy.JOB_COMPLETE, slurmpy.JOB_CANCELLED, slurmpy.JOB_FAILED, slurmpy.JOB_TIMEOUT, slurmpy.JOB_NODE_FAIL, slurmpy.JOB_PREEMPTED, slurmpy.JOB_BOOT_FAIL]

	if (jobInfo.job_state & slurmpy.JOB_STATE_BASE) in meansDone:
		return True

script = """\
#!/usr/bin/python2

import sys
import os
import time

print(sys.argv)
print(os.environ)

time.sleep(60)
"""

jobIds = [sbatch("test-%04d" % i, 1, 10, script, os.environ, []) for i in range(10)]

jobIds = []
for i in range(10):
	jobIds += [sbatch("test-%04d" % i, 1, 10, script, os.environ, [])]

	time.sleep(0.5)

while 1:
	jobInfos = queryJobs(jobIds)

	if len(jobIds) == len([x for x in map(jobIsFinished, jobInfos) if x]):
		break

	time.sleep(0.5)

