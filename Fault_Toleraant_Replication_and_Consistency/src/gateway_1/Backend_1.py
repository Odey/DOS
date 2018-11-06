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



timestamp   = 0
offset      = 0	

#Set the current path of DB
path = os.getcwd() + '/gateway_1/DB/'
	
def RPCServer():
	 
	class RequestHandler(SimpleXMLRPCRequestHandler):
		rpc_paths = ('/RPC2',)
	# Create server
	server = SimpleXMLRPCServer(("localhost", 8008), requestHandler=RequestHandler,logRequests=False, allow_none=True)
	server.register_introspection_functions()

	
	f = open(path+'current_status_temp.txt', 'w+')
	g = open(path+'history.csv','w+')
	h = open(path+'LamportEventLog.txt', 'w+')
	i = open(path+'current_status.txt','w+')
	### file to maintain current state

	### Heartbeat to check if the node is alive or not
	def is_alive():
		return True
	server.register_function(is_alive)
	
	## saving the lamport clock and activity details for plotting
	def saveclockplot(sequence):
		with open(path+'LamportEventLog.txt', 'a+') as f:
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
		with open(path+'current_status_temp.txt', 'w+') as f:
			have = 0
			with open(path+'current_status.txt', 'a+') as fp:
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
		shutil.move(path+"current_status_temp.txt",path+"current_status.txt")
		return
	server.register_function(save_state)
	## saves all activities of each node requested by frontend
	def history(timestamp,nodeID, name, state):
		h_file = open(path+'history.csv','a+')
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


thread1 = threading.Thread(target=RPCServer)
thread1.start()

