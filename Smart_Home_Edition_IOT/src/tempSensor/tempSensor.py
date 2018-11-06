#!/usr/bin/python

'''tempSensor.py: Returns the current temperature value to the Gateway on request from it. Pull Based.
Return types: float, int
''' 
import xmlrpclib
import random
import socket
import sys
import threading 
import time
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import xmlrpclib


######### Global declarations of events and variables #########

eventElection = threading.Event()
eventSync  	  = threading.Event()
i_am_leader   = 0
our_leader    = 0
flag          = 0


######### Temperature Sensor Process ##########################
#########...... Pull Based ..........##########################

def RPCServer():
	class RequestHandler(SimpleXMLRPCRequestHandler):
		rpc_paths = ('/RPC2',)
	# Create server
	server = SimpleXMLRPCServer(("localhost", 8007), requestHandler=RequestHandler,logRequests=False, allow_none=True)
	server.register_introspection_functions()

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

	### Heartbeat to check if the node is alive or not
	def is_alive():
		return True
	server.register_function(is_alive)

	### to indicate the clock syncrinization is complete.
	def synced():
		eventSync.set()
	server.register_function(synced)

	### creating Temperature sensor object with various attributes and associated get() and set() functions.
	class tempSensor:
		def __init__(self):
			self.name 	  ="tempSensor"		    
			self.ID	  	  =0
			self.timestamp=0
			self.clock	  =0
			self.temp	  =0 			## initially the temperature is set to 0
			self.offset   =0
 
		def get_type(self, c): 			## getting type of the node: sensor/device
			if self.clock<=c[0]:
				self.clock=c[0]+1
			else:
				self.clock = self.clock + 1
			return "Sensor"

		def Clock(self):				## reporting the clock in case of events 
			self.clock=self.clock+1
			return [self.clock]

		def get_temp(self, c):			## getting the current temperature 
			if self.clock<=c[0]:
				self.clock=c[0]+1
			else:
				self.clock = self.clock + 1
			self.temp=random.randint(40,80) ## temperature is randomly generated.
			self.clock_plot(c+[self.clock])
			return self.temp

		def clock_plot(self,sequence):		## for reporting the logical clock for event ordering
			gateway = xmlrpclib.ServerProxy('http://localhost:8001')
			gateway.eventplot(sequence)

	
		def get_timestamp(self):			## returns synced timestamp for any event
			self.timestamp = time.time()+self.offset
			return self.timestamp

		def correct_time(self, val):		## corrects the time of this node during clock synchronization.
			self.offset = val
			self.timestamp = self.timestamp + val
			print "corrected time ", self.timestamp


		def get_ID(self, c):				## id of this node
			if self.clock<=c[0]:
				self.clock=c[0]+1
			else:
				self.clock = self.clock + 1
			return self.ID

		def get_name(self, c):				## name of this node
			if self.clock<=c[0]:
				self.clock=c[0]+1
			else:
				self.clock = self.clock + 1
			return self.name

		def set_ID(self, ID, c):			## setting ID,happens only once during registration with the gateway.
			if self.clock<=c[0]:
				self.clock=c[0]+1
			else:
				self.clock = self.clock + 1
			self.ID=ID
	
	server.register_instance(tempSensor())
	try:
		server.serve_forever()
	except KeyboardInterrupt: ##Not working look into this.
		print "Exiting"
		server.close()
		sys.exit()

## Temperature sensor registers itself with the gateway.
## It does not do anything on its own after that.(no push only pull)
def RPCClient():
	proxyGateway = xmlrpclib.ServerProxy('http://localhost:8001')
	temp1 = xmlrpclib.ServerProxy('http://localhost:8007')
	newID=proxyGateway.register(temp1.get_type(temp1.Clock()), temp1.get_name(temp1.Clock()))
	temp1.set_ID(newID, temp1.Clock())
	while flag==0:## waiting for leader lection and clock sync to complete
		pass
	eventSync.wait()


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



#Lock = threading.Lock()
thread1 = threading.Thread(target=RPCServer)
thread1.start()
time.sleep(0.1)
thread2 = threading.Thread(target=RPCClient)
thread2.start()
time.sleep(0.1)
thread3 = threading.Thread(target=LeaderMaster)
thread3.start()




