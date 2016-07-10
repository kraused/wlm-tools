
import sys
import os

import ctypes
ctypes.PyDLL("slurmpy.so", ctypes.RTLD_GLOBAL)

import gc
gc.set_debug(gc.DEBUG_STATS | gc.DEBUG_LEAK)

import slurmpy

if 1:
	msg = slurmpy.node_info_msg_t_PTR()
	err = slurmpy.slurm_load_node(0, msg, slurmpy.SHOW_DETAIL | slurmpy.SHOW_ALL)

	slurmpy.slurm_print_node_info_msg(sys.stdout, msg[0], 1)

#	print(err)
#	print(msg)
#	print(msg[0].record_count)
#
#	for i in range(msg[0].record_count):
#
#		arch = msg[0].node_array[i].arch
#		boards = msg[0].node_array[i].boards
#		boot_time = msg[0].node_array[i].boot_time
#		cores = msg[0].node_array[i].cores
#		cpus = msg[0].node_array[i].cpus
#		energy = msg[0].node_array[i].energy
#		ext_sensors = msg[0].node_array[i].ext_sensors
#		features = msg[0].node_array[i].features
#		gres = msg[0].node_array[i].gres
#		cpu_load = msg[0].node_array[i].cpu_load
#		free_mem = msg[0].node_array[i].free_mem
#		name = msg[0].node_array[i].name
#		node_addr = msg[0].node_array[i].node_addr
#		node_hostname = msg[0].node_array[i].node_hostname
#		node_state = msg[0].node_array[i].node_state
#		os = msg[0].node_array[i].os
#		real_memory = msg[0].node_array[i].real_memory
#		reason = msg[0].node_array[i].reason
#		reason_time = msg[0].node_array[i].reason_time
#		reason_uid = msg[0].node_array[i].reason_uid
#		slurmd_start_time = msg[0].node_array[i].slurmd_start_time
#		sockets = msg[0].node_array[i].sockets
#		threads = msg[0].node_array[i].threads
#		tmp_disk = msg[0].node_array[i].tmp_disk
#		weight = msg[0].node_array[i].weight
#		version = msg[0].node_array[i].version
#
#		print(arch, boards, boot_time, cores, cpus, energy, ext_sensors, features, gres, cpu_load, free_mem, name, node_addr, node_hostname, node_state, os, real_memory, reason, reason_time, reason_uid, slurmd_start_time, sockets, threads, tmp_disk, weight, version)

gc.collect()

