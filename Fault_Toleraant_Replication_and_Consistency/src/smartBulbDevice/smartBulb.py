#!usr/bin/python
import threading
import sys
from thread import *
import socket               # Import socket module
'''smartBulb.py:Push/Pull Based.
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
flagFailed=0
event = threading.Event()
available_gateways = [8001,9001]
gateway_connected_to = 0 ## updated dynamically

def RPCServer():
	class RequestHandler(SimpleXMLRPCRequestHandler):
		rpc_paths = ('/RPC2',)
	# Create server
	server = SimpleXMLRPCServer(("localhost", 8004), requestHandler=RequestHandler,logRequests=False, allow_none=True)
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

	### creating smart bulb device object with various attributes and associated get() and set() functions.
	class smartBulb:
			def __init__(self):
				self.name="smartBulb"		    
				self.ID=0
				self.timestamp=0
				self.clock=0
				self.state=0 ##0 or 1 (closed/Open)
				self.timestamp =0
				self.offset = 0

			def get_type(self, c):	## getting type of the node: sensor/device
				if self.clock<=c[0]:
					self.clock=c[0]+1
				else:
					self.clock = self.clock + 1
				return "Device"

			def Clock(self):	## reporting the clock in case of events 
				return [self.clock]

			def set_state(self, value, c): ##to be called to set a particular state based on the event
								
				if self.clock<=c[0]:
					self.clock=c[0]+1
				else:
					self.clock = self.clock + 1
				self.state=value
				self.clock_plot(c+[self.clock])
				event.set()
				print "set_state of bulb is being called."

			

			def clock_plot(self,sequence):	## for reporting the logical clock for event ordering
				return 1
				gateway = xmlrpclib.ServerProxy('http://localhost:8001')
				gateway.eventplot(sequence)
				

			def get_state(self, c):	## reporting the current status
				if self.clock<=c[0]:
					self.clock=c[0]+1
				else:
					self.clock = self.clock + 1
				self.clock_plot(c+[self.clock])
				#print "clock value is", self.clock,"in", self.name
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
	server.register_instance(smartBulb())
	
	try:
		server.serve_forever()
	except KeyboardInterrupt: ##Not working look into this.
		print "Exiting"
		server.close()
		sys.exit()
	
	
def get_red(str):
	print "\033[1;31m"+str+"\033[1;m"
	return



## smart bulb device registers itself to the gateway 
## waits for any state change(done manually be user) and reports to the gateway without explicitly being asked(Push based)
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
	get_red("smartBulbDevice connected to "+str(gateway_connected_to))
	bulb = xmlrpclib.ServerProxy('http://localhost:8004')
	##Registering the Device to the gateway
	bulb.set_ID(proxyGateway.register(bulb.get_type(bulb.Clock()), bulb.get_name(bulb.Clock())))
	while True:	
		try:
			event.wait()
			event.clear()
			proxyGateway.report_state(bulb.get_timestamp(),bulb.get_ID(bulb.Clock()), bulb.get_state(bulb.Clock()), bulb.Clock(),0,['smartBulb','G'])
			event.clear()
		except:
			get_red('Reconfiguring the Device.')
			proxyGateway = xmlrpclib.ServerProxy('http://localhost:'+str(available_gateways[0]))
			#while True:
			event.wait()
			event.clear()
			proxyGateway.report_state(bulb.get_timestamp(),bulb.get_ID(bulb.Clock()), bulb.get_state(bulb.Clock()), bulb.Clock(),0,['smartBulb','G'])
			
		



thread1 = threading.Thread(target=RPCServer)
thread1.start()
time.sleep(0.1)
thread2 = threading.Thread(target=RPCClient)
thread2.start()


