import threading
import sys
from datetime import datetime
import socket
from thread import start_new_thread
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import xmlrpclib
import time
import random

eventRPC = threading.Event()
eventconsistent = threading.Event()
proposer = 1
roundId  = 0
acceptors = [1,2,3,4,5]
promise_no = 0
proposal = 0
recv_data = 0
busy = 0

def get_red(str):
	print "\033[1;31m"+str+"\033[1;m"
	return

### this gateway is considered to be the leader for PAXOS. 
def RPCServer():
	class RequestHandler(SimpleXMLRPCRequestHandler):
		rpc_paths = ('/RPC2',)
	# Create server
	server = SimpleXMLRPCServer(("localhost", 9001), requestHandler=RequestHandler,logRequests=False, allow_none=True)
	server.register_introspection_functions()

	def start_paxos(data): ## other replicated gateways signals the leader to start paxos as it has encountered write
		global recv_data, busy
		recv_data = data
		busy = 1
		eventRPC.set()
		print "Starting consensus agreement"
		return
	server.register_function(start_paxos)

	def buzy():	## to synchronize between two initiate paxos for write requests 
		global busy
		return busy
	server.register_function(buzy)
		
	try:
		server.serve_forever()
	except KeyboardInterrupt: 
		print "Exiting"
		server.close()
		sys.exit()

## paxos leader performs steps to come to an agreement
def RPCClient():
	global roundId, promise_no, proposal, recv_data, busy
	#eventRPC.set()
	if proposer:
		for i in range(1,15):
			eventRPC.wait()
			eventRPC.clear()
			roundId = roundId + 1
			temp_proposal = []
			temp_roundid  = []
			temp_acc_res  = []
			result = None
			print "\nStarting round", roundId
			for node in acceptors: 		## ask replicas if they are available for index roundid
				nodeproxy = xmlrpclib.ServerProxy('http://localhost:'+str(8000+int(node)))
				result = nodeproxy.prepare(roundId)
				if "NAK" in result:
					continue
				else:
					promise_no = promise_no + 1
					if "accept" not in result:
						temp_proposal.append(str(result.strip().split(":")[1]))
						temp_roundid.append(int(result.strip().split(":")[0]))			
			if promise_no >len(acceptors)/2:  ## initiate the proposal when there is majority vote
				if len(temp_proposal):
					#proposal = max(temp_proposal)	
					temp_proposal = temp_proposal[temp_roundid.index(max(temp_roundid))]
					proposal = recv_data
					if "EMPTY" in temp_proposal:
						proposal = recv_data
				else:
					proposal = recv_data		

				for node in acceptors: ## Finally sends the acceptRequest to replicas indicating them to add the proposal to their database and return success or denial
					nodeproxy = xmlrpclib.ServerProxy('http://localhost:'+str(8000+node))
					acc_result = nodeproxy.acceptRequest(roundId, proposal)	
					if "denied" in acc_result:
						get_red("Round failed !! Starting another round") 
						eventRPC.set()
					else:
						temp_acc_res.append(acc_result)				
				if len(temp_acc_res)==len(acceptors): ## all replicas should accpet the consensus otherwise the leader runs another round
					get_red("All gateways agreed on consensus (node ID: state) "+str(proposal))
					busy = 0
					eventconsistent.set()	
			else:
				print "More number of write denials by the gateways"	
				eventRPC.set()
		print "Exhausted max number of rounds"

def RPCconsistent():  ## this is to indicate the application that the event has been logged and you can proceed with other requests
	global recv_data
	while True:
		eventconsistent.wait()
		eventconsistent.clear()
		node = int(recv_data.strip().split(":")[0])
		proxy = xmlrpclib.ServerProxy('http://localhost:'+str(8010+int(node)))
		proxy.is_write_complete()




thread1 = threading.Thread(target=RPCServer)
thread1.start()
time.sleep(1)
thread2 = threading.Thread(target=RPCClient)
thread2.start()
time.sleep(0.2)
thread3 = threading.Thread(target=RPCconsistent)
thread3.start()
