#!usr/bin/python
import threading
import sys
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import xmlrpclib
import time
from thread import *
import socket               # Import socket module
'''user.py: .
Return type: int
''' 
flag=0
eventElection = threading.Event()
eventSync  = threading.Event()
i_am_leader= 0
our_leader = 0
timestamp  = 0
offset 	   = 0
def RPCServer():
	class RequestHandler(SimpleXMLRPCRequestHandler):
		rpc_paths = ('/RPC2',)
	# Create server
	server = SimpleXMLRPCServer(("localhost", 8006), requestHandler=RequestHandler,logRequests=False, allow_none=True)
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

	### Heartbeat to check if the node is alive or not		
	def is_alive():
		return True
	server.register_function(is_alive)

	### to indicate the clock syncrinization is complete.
	def synced():
		eventSync.set()
	server.register_function(synced)

	def changeBulbState(value, c):
		bulb = xmlrpclib.ServerProxy('http://localhost:8004')
		bulb.set_state(value, c)
		time.sleep(0.5)
	server.register_function(changeBulbState)

	def changeOutletState(value, c):
		outlet = xmlrpclib.ServerProxy('http://localhost:8005')
		outlet.set_state(value, c)
		time.sleep(0.5)
	server.register_function(changeOutletState)

	def changeDoorState(value,c):
		gateway = xmlrpclib.ServerProxy('http://localhost:8001')
		door = xmlrpclib.ServerProxy('http://localhost:8003') ##connecting to Door sensor
		door.set_state(int(value), c) ##opens/closes door.
		time.sleep(0.1)
		if int(value)==1:
			print "Closing Door Automatically."
			door.set_state(0, gateway.clock('U', 'doorSensor')) ##closes door.
		time.sleep(0.5)
	server.register_function(changeDoorState)

	def changeMotionState(value,c):
		gateway = xmlrpclib.ServerProxy('http://localhost:8001')
		motion = xmlrpclib.ServerProxy('http://localhost:8002') ##connecting to motion sensor
		motion.set_state(int(value), c) ##motion sensor activated.
		time.sleep(0.1)
		if int(value)==1:
			print "Turning on Lights."
			bulb = xmlrpclib.ServerProxy('http://localhost:8004')
			bulb.set_state(1, gateway.clock('U', 'smartBulb'))
		time.sleep(0.5)
	server.register_function(changeMotionState)
			
	def enters():
		###doorOpen--->doorCloses--->motionDetected.
		gateway = xmlrpclib.ServerProxy('http://localhost:8001')
		door = xmlrpclib.ServerProxy('http://localhost:8003') ##connecting to Door sensor
		door.set_state(1, gateway.clock('U', 'doorSensor')) ##opens door.
		time.sleep(0.1)
		door.set_state(0, gateway.clock('U', 'doorSensor')) ##closes door.
		motion = xmlrpclib.ServerProxy('http://localhost:8002') ##connecting to motion sensor
		motion.set_state(1, gateway.clock('U', 'motionSensor')) ##motion sensor activated.
		time.sleep(0.5)
	server.register_function(enters)

	def exits():
		###motionDetcted-->doorOpens-->doorCloses-->motionInactive.
		gateway = xmlrpclib.ServerProxy('http://localhost:8001')
		motion = xmlrpclib.ServerProxy('http://localhost:8002') ##connecting to motion sensor
		motion.set_state(1, gateway.clock('U', 'motionSensor')) ##active motion sensors.
		door = xmlrpclib.ServerProxy('http://localhost:8003') ##connecting to Door sensor
		door.set_state(1, gateway.clock('U', 'doorSensor')) ##open Door 
		time.sleep(0.1)
		door.set_state(0, gateway.clock('U', 'doorSensor'))##Door Closes
		#motion.set_state(0, gateway.clock('U', 'motionSensor'))##motion sensor is inactive.
		time.sleep(0.5)
	server.register_function(exits)

	try:
		server.serve_forever()
	except KeyboardInterrupt: ##Not working look into this.
		print "Exiting"
		server.close()
		sys.exit()


def RPCClient():
	global flag
	while flag==0:
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

thread1 = threading.Thread(target=RPCServer)
thread1.start()
time.sleep(0.1)
thread2 = threading.Thread(target=RPCClient)
thread2.start()
time.sleep(0.1)
thread3 = threading.Thread(target=LeaderMaster)
thread3.start()

		

