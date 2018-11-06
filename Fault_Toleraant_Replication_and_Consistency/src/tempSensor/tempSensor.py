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
flagFailed=0

available_gateways = [8001,9001]
gateway_connected_to = 0 ## updated dynamically


######### Temperature Sensor Process ##########################
#########...... Pull Based ..........##########################

def RPCServer():
	class RequestHandler(SimpleXMLRPCRequestHandler):
		rpc_paths = ('/RPC2',)
	# Create server
	server = SimpleXMLRPCServer(("localhost", 8007), requestHandler=RequestHandler,logRequests=False, allow_none=True)
	server.register_introspection_functions()

	### Heartbeat to check if the node is alive or not
	def is_alive():
		return True
	server.register_function(is_alive)

	##Reconfigure the device in the event of fault recovery.
	def reconfigure(failed):
		global flagFailed
		flagFailed=1
		available_gateways.remove(int(failed))
	server.register_function(reconfigure)

	
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

		def get_state(self, c):			## getting the current temperature 
			if self.clock<=c[0]:
				self.clock=c[0]+1
			else:
				self.clock = self.clock + 1
			self.temp=random.randint(40,80) ## temperature is randomly generated.
			self.clock_plot(c+[self.clock])
			return self.temp

		def clock_plot(self,sequence):		## for reporting the logical clock for event ordering
			return 1
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



def get_red(str):
	print "\033[1;31m"+str+"\033[1;m"
	return



## Temperature sensor registers itself with the gateway.
## It does not do anything on its own after that.(no push only pull)
def RPCClient():
	global gateway_connected_to
	for item in available_gateways:		 
		proxyGateway = xmlrpclib.ServerProxy('http://localhost:'+str(item))
		load = proxyGateway.get_load_status()
		if int(load)>=3:
			continue
		else:
			gateway_connected_to = item
			break
	get_red("tempSensor connected to "+str(gateway_connected_to))
	temp1 = xmlrpclib.ServerProxy('http://localhost:8007')
	newID=proxyGateway.register(temp1.get_type(temp1.Clock()), temp1.get_name(temp1.Clock()))
	temp1.set_ID(newID, temp1.Clock())
	


#Lock = threading.Lock()
thread1 = threading.Thread(target=RPCServer)
thread1.start()
time.sleep(0.1)
thread2 = threading.Thread(target=RPCClient)
thread2.start()




