import threading
import sys
from datetime import datetime
import socket
from thread import start_new_thread
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import xmlrpclib
import time

eventRPC = threading.Event()
proposer = 0
roundId  = 0
acceptors = [1,2,3,4,5]
proposals = {}
promise = 0
in_mem_data = {}

def RPCServer():
	class RequestHandler(SimpleXMLRPCRequestHandler):
		rpc_paths = ('/RPC2',)
	# Create server
	server = SimpleXMLRPCServer(("localhost", 8002), requestHandler=RequestHandler,logRequests=False, allow_none=True)
	server.register_introspection_functions()

	f = open('event_log2.txt', 'w+')
	
	def prepare(N):## responds to leader if they are ready to accept or not using promise or NAK
		global roundId
		if roundId < N:
			result = promise(N)
			return result
		else:
			return "NAK"
	server.register_function(prepare)
			

	def promise(N):## sends the index and data of last logged sensor/device events to its database
		global roundId, promise
		promise = max(promise,N)
		roundId = N
		proposerproxy = xmlrpclib.ServerProxy('http://localhost:9001')
		if len(proposals.keys()):
			#result = str(proposals.itervalues.next())
			key,value = proposals.popitem()
			result = str(key)+":"+str(value)
		else:
			#result = "accept"
			result = str(roundId)+":"+str("EMPTY")
		return result
	server.register_function(promise)

	def acceptRequest(N, val):## leader sends the consensus and the gateway accpets it and make changes to its database by logging the sensor/device events
		global roundId, promise, proposals
		if N >= promise:
			roundId = N
			proposals[roundId]=val
			print "Accepted write request:",N," Consensus on node:state :",val," my id: 2"
			write_log(N,val)
			return "accepted" 
		else:
			return "denied"
	server.register_function(acceptRequest)

	def write(data): ## the sensor/device connected to it calls this when it requests for state changes
		leaderproxy = xmlrpclib.ServerProxy('http://localhost:9001')
		print "Write request recieved", data
		while(leaderproxy.buzy()):
			pass
		leaderproxy.start_paxos(data)
	server.register_function(write)

	def write_log(N,val): ## to write to its database
		global in_mem_data
		with open('event_log2.txt', 'a+') as fp:
			fp.write("Seq No. "+str(N)+" Device:State -> "+str(val)+'\n')
		in_mem_data[int(N)]= val
		return
	server.register_function(write_log)

	def read(N): ## responds to any read type requests 
		global in_mem_data
		print "Gateway 2: Reading data"
		return in_mem_data[N]
	server.register_function(read)
		
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		print "Exiting"
		server.close()
		sys.exit()


def RPCClient():
	node = xmlrpclib.ServerProxy('http://localhost:8002')


thread1 = threading.Thread(target=RPCServer)
thread1.start()
time.sleep(4)
#thread2 = threading.Thread(target=RPCClient)
#thread2.start()
