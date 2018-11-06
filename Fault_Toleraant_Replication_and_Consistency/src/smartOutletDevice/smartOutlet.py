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

flagFailed=0
event=threading.Event()
available_gateways = [8001,9001]
gateway_connected_to = 0 ## updated dynamically

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
	
	##Reconfigure the device in the event of fault recovery.
	def reconfigure(failed):
		global flagFailed
		flagFailed=1
		available_gateways.remove(int(failed))
	server.register_function(reconfigure)


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



def get_red(str):
	print "\033[1;31m"+str+"\033[1;m"
	return

	
## smart outlet device registers itself to the gateway 
## waits for any state change(done manually be user) and reports to the gateway without explicitly being asked(Push based)
def RPCClient():
	global gateway_connected_to, flagFailed
	for item in available_gateways:		 
		proxyGateway = xmlrpclib.ServerProxy('http://localhost:'+str(item))
		load = proxyGateway.get_load_status()
		if int(load)>=3:
			continue
		else:
			gateway_connected_to = item
			break
	get_red("smartOutletDevice connected to "+str(gateway_connected_to))
	outlet = xmlrpclib.ServerProxy('http://localhost:8005')
	##Registering the Device to the gateway
	outlet.set_ID(proxyGateway.register(outlet.get_type(outlet.Clock()), outlet.get_name(outlet.Clock())))
	while True:
		try:
			event.wait()
			event.clear()
			proxyGateway.report_state(outlet.get_timestamp(),outlet.get_ID(outlet.Clock()), outlet.get_state(outlet.Clock()), outlet.Clock(), 0,['smartOutlet','G'])
		except:
			get_red('Reconfiguring the Device.')
			proxyGateway = xmlrpclib.ServerProxy('http://localhost:'+str(available_gateways[0]))
			event.wait()
			event.clear()
			proxyGateway.report_state(outlet.get_timestamp(),outlet.get_ID(outlet.Clock()), outlet.get_state(outlet.Clock()), outlet.Clock(), 0,['smartOutlet','G'])
	

thread1 = threading.Thread(target=RPCServer)
thread1.start()
time.sleep(0.1)
thread2 = threading.Thread(target=RPCClient)
thread2.start()


