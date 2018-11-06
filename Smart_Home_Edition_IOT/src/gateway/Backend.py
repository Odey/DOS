import threading
import sys
from datetime import datetime
import socket
from thread import start_new_thread
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import xmlrpclib
import csv
import shutil
import os
import time

eventElection = threading.Event()
eventSync   = threading.Event()
i_am_leader = 0
our_leader  = 0
timestamp   = 0
flag        = 0
offset      = 0		
def RPCServer():
	class RequestHandler(SimpleXMLRPCRequestHandler):
		rpc_paths = ('/RPC2',)
	# Create server
	server = SimpleXMLRPCServer(("localhost", 8008), requestHandler=RequestHandler,logRequests=False, allow_none=True)
	server.register_introspection_functions()

	f = open('current_status_temp.txt', 'w+')
	g = open('history.csv','w+')
	h = open('LamportEventLog.txt', 'w+')
	### file to maintain current state

	### Heartbeat to check if the node is alive or not
	def is_alive():
		return True
	server.register_function(is_alive)

	### to indicate the clock syncrinization is complete.
	def synced():
		eventSync.set()
	server.register_function(synced)

	### Function to indicate that leader election is complete and now the application can start
	def start_client():
		global flag
		flag = 1
		eventElection.set()
	server.register_function(start_client)

	### Function with which its background leader election process tells if it has been elected as leader or not
	def is_leader():
		global i_am_leader
		i_am_leader = 1
		return
	server.register_function(is_leader)

	### leader election process circulates the new leader information to all the nodes.
	def who_leader(val):
		global our_leader
		our_leader = val
		return
	server.register_function(who_leader)

	## saving the lamport clock and activity details for plotting
	def saveclockplot(sequence):
		with open('LamportEventLog.txt', 'a+') as f:
			if len(sequence)==4:
				f.write(str(sequence)+"\n")
				#print "\nsequence:",sequence
	server.register_function(saveclockplot)
		
	def get_timestamp():
		global timestamp,offset
		timestamp = time.time()+offset
		return timestamp
	server.register_function(get_timestamp)

	## corrects the time of this node during clock synchronization.
	def correct_time(val):
		global timestamp,offset
		offset = val
		timestamp = timestamp + val
		print "corrected time ", timestamp
		
	server.register_function(correct_time)

	## saves the current state requested by frontend
	def save_state(timestamp,nodeID, name, curr_state):
		#print "\nSaving current state ..."
		with open('current_status_temp.txt', 'w+') as f:
			have = 0
			with open('current_status.txt', 'a+') as fp:
				for line in fp:
					if not line:
						f.write("{} {} {} {} \n".format(timestamp,nodeID,name,curr_state))
						have =1
						break
					if str(name) in line:
						f.write("{} {} {} {} \n".format(timestamp,nodeID,name,curr_state))
						have = 1
					else:
						f.write(line)
				if(have==0):
					f.write('{} {} {} {} \n'.format(timestamp,nodeID,name,curr_state))
		shutil.move("current_status_temp.txt","current_status.txt")
		return
	server.register_function(save_state)
	## saves all activities of each node requested by frontend
	def history(timestamp,nodeID, name, state):
		h_file = open('history.csv','a+')
		wr = csv.writer(h_file, quoting=csv.QUOTE_ALL)
		curr_time =0
		max_state =0
		already = 0
		for line in h_file:
			if name in line:
				already = 1
				time = line.split(",")[0][18:27]
				if time>curr_time:
					curr_time = time
					max_state = line[3]
		if already!=0 and max_state!=state:
			wr.writerow([timestamp,nodeID, name, state])
		if already==0:
			wr.writerow([timestamp,nodeID, name, state])

	server.register_function(history)
		
	try:
		server.serve_forever()
	except KeyboardInterrupt: ##Not working look into this.
		print "Exiting"
		server.close()
		sys.exit()


## This thread runs for clock synchronization purpose. If this is elected as the master then this thread becomes the time server
## and synchronize with others.
def LeaderMaster():
	global i_am_leader
	eventSync.clear()
	while True: 
		while (i_am_leader==0):
			pass
		#eventSync.wait()
		print "--"*20
		print "Time to Syncronize the clock !!"
		sys_time =0
		timestamps_list =[]
		temp_socket =[]
		offset = 0
		total_nodes = 8

		## accepting timestamps from all the nodes
		for node in xrange(1,total_nodes+1):
			try:
				temp = xmlrpclib.ServerProxy('http://localhost:'+str(8000+int(node)))
				temp_socket.append(temp)
				timestamps_list.append(temp.get_timestamp())
			except:	
				timestamps_list.append(0)
				total_nodes = total_nodes-1
	
		print "--"*20
		print "Initial Timestamps reported by every nodes\n",timestamps_list
		avg_time = (sum(x for x in timestamps_list))/total_nodes
		print "average time ", avg_time
	
		## sending offset to each node for correction.	
		for i in range(1,len(temp_socket)+1):
			offset = avg_time-timestamps_list[i-1]
			print "offset for ",i," is",offset
			try:
				temp_socket[i-1].correct_time(offset)
			except:
				pass

		print "##"*20
		i_am_leader=0
		## indicates the node that they are synchronized.
		for i in temp_socket:
			i.synced()


thread1 = threading.Thread(target=RPCServer)
thread1.start()
time.sleep(0.1)
thread3 = threading.Thread(target=LeaderMaster)
thread3.start()

