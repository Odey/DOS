#!usr/bin/python
import threading
import sys
from thread import *
import socket               # Import socket module
'''smartOutlet.py:Push/Pull Based.
Return type: int
''' 
	
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import xmlrpclib
import random
import socket
import sys
import threading 
import time
from datetime import datetime
flag=0
eventElection = threading.Event()
event      = threading.Event()
eventSync  = threading.Event()
i_am_leader= 0
our_leader = 0
def RPCServer():
	class RequestHandler(SimpleXMLRPCRequestHandler):
		rpc_paths = ('/RPC2',)
	# Create server
	server = SimpleXMLRPCServer(("localhost", 8005), requestHandler=RequestHandler,logRequests=False, allow_none=True)
	server.register_introspection_functions()

	### Heartbeat to check if the node is alive or not
	def is_alive():
		return True
	server.register_function(is_alive)

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

	### to indicate the clock syncrinization is complete.
	def synced():
		eventSync.set()
	server.register_function(synced)

	### creating smart outlet device object with various attributes and associated get() and set() functions.
	class smartOutlet:
			def __init__(self):
				self.name="smartOutlet"		    
				self.ID=0
				self.clock=0
				self.timestamp=0
				self.state=0 ##0 or 1 (closed/Open)
				self.timestamp = 0
				self.offset = 0

			def Clock(self):	## reporting the clock in case of events 
				return [self.clock]

			def get_type(self, c):	## getting type of the node: sensor/device
				if self.clock<=c[0]:
					self.clock=c[0]+1
				else:
					self.clock = self.clock + 1
				return "Device"

			def set_state(self, value, c): ##to be called to set a particular state based on the event
				if self.clock<=c[0]:
					self.clock=c[0]+1
				else:
					self.clock = self.clock + 1
				self.state=value
				self.clock_plot(c+[self.clock])
				event.set()
				print "set_state of outlet is being called."
				if value!=self.state:
					flag = 1

			def clock_plot(self,sequence):	## for reporting the logical clock for event ordering
				gateway = xmlrpclib.ServerProxy('http://localhost:8001')
				gateway.eventplot(sequence)

			def get_state(self, c):	## reporting the current status
				if self.clock<=c[0]:
					self.clock=c[0]+1
				else:
					self.clock = self.clock + 1
				self.clock_plot(c+[self.clock])
				#print "clock value is", self.clock,"in",self.name
				return self.state
	
			def get_timestamp(self):## returns synced timestamp for any event
				self.timestamp = time.time()+self.offset
				return self.timestamp

			def correct_time(self, val):## corrects the time of this node during clock synchronization.
				self.offset = val
				self.timestamp = self.timestamp + val
				print "corrected time ", self.timestamp


			def get_ID(self, c):
				if self.clock<=c[0]:
					self.clock=c[0]+1
				else:
					self.clock = self.clock + 1
				return self.ID
			
			def set_ID(self, ID):
				self.ID=ID

			def get_name(self, c):
				if self.clock<=c[0]:
					self.clock=c[0]+1
				else:
					self.clock = self.clock + 1
				return self.name
	server.register_instance(smartOutlet())
	
	try:
		server.serve_forever()
	except KeyboardInterrupt: ##Not working look into this.
		print "Exiting"
		server.close()
		sys.exit()
	
## smart outlet device registers itself to the gateway 
## waits for any state change(done manually be user) and reports to the gateway without explicitly being asked(Push based)
def RPCClient():
	global flag
	proxyGateway = xmlrpclib.ServerProxy('http://localhost:8001')
	outlet = xmlrpclib.ServerProxy('http://localhost:8005')
	##Registering the Device to the gateway
	outlet.set_ID(proxyGateway.register(outlet.get_type(outlet.Clock()), outlet.get_name(outlet.Clock())))
	##wait for an event from the users.
	while flag==0: ## waiting for leader lection and clock sync to complete
		pass
	eventSync.wait()
	while True:
		event.wait()
		event.clear()
		#proc = ['Ot','G']
		proxyGateway.report_state(outlet.get_timestamp(),outlet.get_ID(outlet.Clock()), outlet.get_state(outlet.Clock()), outlet.Clock(), ['smartOutlet','G'])
	#print "here"

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
thread2 = threading.Thread(target=RPCClient)
thread2.start()
time.sleep(0.1)
thread3 = threading.Thread(target=LeaderMaster)
thread3.start()

