#!usr/bin/python
import sys
from thread import *	
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import xmlrpclib
import random
import socket
import threading 
import time

eventWrite_complete = threading.Event()
node_id = 3

def RPCServer():
	class RequestHandler(SimpleXMLRPCRequestHandler):
		rpc_paths = ('/RPC2',)
	# Create server
	server = SimpleXMLRPCServer(("localhost", 8013), requestHandler=RequestHandler,logRequests=False, allow_none=True)
	server.register_introspection_functions()

	def is_write_complete():
		eventWrite_complete.set()
	server.register_function(is_write_complete)

	
	try:
		server.serve_forever()
	except KeyboardInterrupt: ##Not working look into this.
		print "Exiting"
		server.close()
		sys.exit()
	

def get_red(str):
	print "\033[1;31m"+str+"\033[1;m"
	return

def RPCClient():
	global node_id
	print "Waiting to connect"
	proxyGateway = xmlrpclib.ServerProxy('http://localhost:8003')
	#while True:
	for i in range(1,4):
		data = random.choice(["ON","OFF","LOW INTENSITY","HIGH INTENSITY"])
		to_write = str(node_id)+":"+str(data)+" - "+str("SamrtBulb")
		proxyGateway.write(to_write) ## requests for state change
		print "-"*40
		eventWrite_complete.wait() ## waiting for paxos to complete
		eventWrite_complete.clear()
		n_read = 3
		get_red("\nReturned read state: "+str(proxyGateway.read(n_read)))
		print "-"*40
		time.sleep(1)
		proxyGateway.write(str(node_id)+":"+"OFF"+" - "+str("SamrtBulb"))
		print "-"*40
		eventWrite_complete.wait()
		eventWrite_complete.clear()
		eventWrite_complete.wait()



thread1 = threading.Thread(target=RPCServer)
thread1.start()
time.sleep(0.1)
thread2 = threading.Thread(target=RPCClient)
thread2.start()

