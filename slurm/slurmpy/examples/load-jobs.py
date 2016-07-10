
import ctypes
ctypes.PyDLL("slurmpy.so", ctypes.RTLD_GLOBAL)

import gc
gc.set_debug(gc.DEBUG_STATS | gc.DEBUG_LEAK)

import slurmpy

if 1:
	msg = slurmpy.job_info_msg_t_PTR()
	err = slurmpy.slurm_load_jobs(0, msg, slurmpy.SHOW_DETAIL | slurmpy.SHOW_ALL)

	print(err)
	print(msg)
	# print(msg.record_count)
	# print(msg.job_array)
	print(msg[0].record_count)

	for i in range(msg[0].record_count):
		exc_node_inx = []
		j = 0
		while -1 != msg[0].job_array[i].exc_node_inx[j]:
			exc_node_inx += [msg[0].job_array[i].exc_node_inx[j]]
			j += 1

		print(exc_node_inx)

		node_inx = []
		j = 0
		while -1 != msg[0].job_array[i].node_inx[j]:
			node_inx += [msg[0].job_array[i].node_inx[j]]
			j += 1

		print(node_inx)

#		account = msg[0].job_array[i].account
#		alloc_node = msg[0].job_array[i].alloc_node
#		alloc_sid = msg[0].job_array[i].alloc_sid
#		array_job_id = msg[0].job_array[i].array_job_id
#		array_task_id = msg[0].job_array[i].array_task_id
#		assoc_id = msg[0].job_array[i].assoc_id
#		batch_flag = msg[0].job_array[i].batch_flag
#		batch_host = msg[0].job_array[i].batch_host
#		batch_script = msg[0].job_array[i].batch_script
#		command = msg[0].job_array[i].command
#		comment = msg[0].job_array[i].comment
#		contiguous = msg[0].job_array[i].contiguous
#		core_spec = msg[0].job_array[i].core_spec
#		cpus_per_task = msg[0].job_array[i].cpus_per_task
#		dependency = msg[0].job_array[i].dependency
#		derived_ec = msg[0].job_array[i].derived_ec
#		eligible_time = msg[0].job_array[i].eligible_time
#		end_time = msg[0].job_array[i].end_time
#		exc_nodes = msg[0].job_array[i].exc_nodes
#		# int32_t* exc_node_inx = msg[0].job_array[i].exc_node_inx
#		exit_code = msg[0].job_array[i].exit_code
#		features = msg[0].job_array[i].features
#		gres = msg[0].job_array[i].gres
#		group_id = msg[0].job_array[i].group_id
#		job_id = msg[0].job_array[i].job_id
#		job_state = msg[0].job_array[i].job_state
#		licenses = msg[0].job_array[i].licenses
#		max_cpus = msg[0].job_array[i].max_cpus
#		max_nodes = msg[0].job_array[i].max_nodes
#		boards_per_node = msg[0].job_array[i].boards_per_node
#		sockets_per_board = msg[0].job_array[i].sockets_per_board
#		sockets_per_node = msg[0].job_array[i].sockets_per_node
#		cores_per_socket = msg[0].job_array[i].cores_per_socket
#		threads_per_core = msg[0].job_array[i].threads_per_core
#		name = msg[0].job_array[i].name
#		network = msg[0].job_array[i].network
#		nodes = msg[0].job_array[i].nodes
#		nice = msg[0].job_array[i].nice
#		# int32_t* node_inx) = msg[0].job_array[i].node_inx)
#		ntasks_per_core = msg[0].job_array[i].ntasks_per_core
#		ntasks_per_node = msg[0].job_array[i].ntasks_per_node
#		ntasks_per_socket = msg[0].job_array[i].ntasks_per_socket
#		ntasks_per_board = msg[0].job_array[i].ntasks_per_board
#		num_nodes = msg[0].job_array[i].num_nodes
#		num_cpus = msg[0].job_array[i].num_cpus
#		partition = msg[0].job_array[i].partition
#		pn_min_memory = msg[0].job_array[i].pn_min_memory
#		pn_min_cpus = msg[0].job_array[i].pn_min_cpus
#		pn_min_tmp_disk = msg[0].job_array[i].pn_min_tmp_disk
#		pre_sus_time = msg[0].job_array[i].pre_sus_time
#		priority = msg[0].job_array[i].priority
#		profile = msg[0].job_array[i].profile
#		qos = msg[0].job_array[i].qos
#		req_nodes = msg[0].job_array[i].req_nodes
#		# int32_t* req_node_inx = msg[0].job_array[i].req_node_inx
#		req_switch = msg[0].job_array[i].req_switch
#		requeue = msg[0].job_array[i].requeue
#		resize_time = msg[0].job_array[i].resize_time
#		restart_cnt = msg[0].job_array[i].restart_cnt
#		resv_name = msg[0].job_array[i].resv_name
#		shared = msg[0].job_array[i].shared
#		show_flags = msg[0].job_array[i].show_flags
#		start_time = msg[0].job_array[i].start_time
#		state_desc = msg[0].job_array[i].state_desc
#		state_reason = msg[0].job_array[i].state_reason
#		std_err = msg[0].job_array[i].std_err
#		std_in = msg[0].job_array[i].std_in
#		std_out = msg[0].job_array[i].std_out
#		submit_time = msg[0].job_array[i].submit_time
#		suspend_time = msg[0].job_array[i].suspend_time
#		time_limit = msg[0].job_array[i].time_limit
#		time_min = msg[0].job_array[i].time_min
#		user_id = msg[0].job_array[i].user_id
#		preempt_time = msg[0].job_array[i].preempt_time
#		wait4switch = msg[0].job_array[i].wait4switch
#		wckey = msg[0].job_array[i].wckey
#		work_dir = msg[0].job_array[i].work_dir
#
#	 	print(account, alloc_node, alloc_sid, array_job_id, array_task_id, assoc_id, batch_flag, batch_host, batch_script, command, comment, contiguous, core_spec, cpus_per_task, dependency, derived_ec, eligible_time, end_time, exc_nodes, exit_code, features, gres, group_id, job_id, job_state, licenses, max_cpus, max_nodes, boards_per_node, sockets_per_board, sockets_per_node, cores_per_socket, threads_per_core, name, network, nodes, nice, ntasks_per_core, ntasks_per_node, ntasks_per_socket, ntasks_per_board, num_nodes, num_cpus, partition, pn_min_memory, pn_min_cpus, pn_min_tmp_disk, pre_sus_time, priority, profile, qos, req_nodes, req_switch, requeue, resize_time, restart_cnt, resv_name, shared, show_flags, start_time, state_desc, state_reason, std_err, std_in, std_out, submit_time, suspend_time, time_limit, time_min, user_id, preempt_time, wait4switch, wckey, work_dir)

gc.collect()

