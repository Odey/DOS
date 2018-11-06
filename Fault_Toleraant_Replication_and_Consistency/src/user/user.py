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



timestamp  = 0
offset 	   = 0
def RPCServer():
	class RequestHandler(SimpleXMLRPCRequestHandler):
		rpc_paths = ('/RPC2',)
	# Create server
	server = SimpleXMLRPCServer(("localhost", 8006), requestHandler=RequestHandler,logRequests=False, allow_none=True)
	server.register_introspection_functions()

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
		try:
			gateway = xmlrpclib.ServerProxy('http://localhost:8001')
		except:		
			gateway = xmlrpclib.ServerProxy('http://localhost:9001')
		door = xmlrpclib.ServerProxy('http://localhost:8003') ##connecting to Door sensor
		door.set_state(int(value), c) ##opens/closes door.
		time.sleep(0.1)
		if int(value)==1:
			print "Closing Door Automatically."
			try:
				gateway = xmlrpclib.ServerProxy('http://localhost:8001')
				door.set_state(0, gateway.clock('U', 'doorSensor')) ##closes door.
			except:
				gateway = xmlrpclib.ServerProxy('http://localhost:9001')
				door.set_state(0, gateway.clock('U', 'doorSensor')) ##closes door.
			
		time.sleep(0.5)
	server.register_function(changeDoorState)

	def changeMotionState(value,c):
		try:
			gateway = xmlrpclib.ServerProxy('http://localhost:8001')
		except:		
			gateway = xmlrpclib.ServerProxy('http://localhost:9001')
		motion = xmlrpclib.ServerProxy('http://localhost:8002') ##connecting to motion sensor
		motion.set_state(int(value), c) ##motion sensor activated.
		time.sleep(0.1)
		if int(value)==1:
			print "Turning on Lights."
			bulb = xmlrpclib.ServerProxy('http://localhost:8004')
			try:
				gateway = xmlrpclib.ServerProxy('http://localhost:8001')
				bulb.set_state(1, gateway.clock('U', 'smartBulb'))
			except:
				gateway = xmlrpclib.ServerProxy('http://localhost:9001')
				bulb.set_state(1, gateway.clock('U', 'smartBulb'))
		time.sleep(0.5)
	server.register_function(changeMotionState)
			
	def enters():
		###doorOpen--->doorCloses--->motionDetected.
		try:
			gateway = xmlrpclib.ServerProxy('http://localhost:8001')
		except:		
			gateway = xmlrpclib.ServerProxy('http://localhost:9001')
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
		try:
			gateway = xmlrpclib.ServerProxy('http://localhost:8001')
		except:		
			gateway = xmlrpclib.ServerProxy('http://localhost:9001')
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


#def RPCClient():

thread1 = threading.Thread(target=RPCServer)
thread1.start()
#time.sleep(0.1)
#thread2 = threading.Thread(target=RPCClient)
#thread2.start()


		

