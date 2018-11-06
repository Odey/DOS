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
start_node = 0
def RPCServer():
	class RequestHandler(SimpleXMLRPCRequestHandler):
		rpc_paths = ('/RPC2',)
	# Create server
	server = SimpleXMLRPCServer(("localhost", 8014), requestHandler=RequestHandler,logRequests=False, allow_none=True)
	server.register_introspection_functions()
	
	class node:
		def __init__(self):
			self.id = 4
			self.active_nodes = []
			self.state = "normal" ## state can be normal. election, crashed
			self.neighbors =[5,6]
			self.leader = 0 
			self.connected_to = 0
		
		def is_alive(self):
			return True

		def set_active_nodes(self, nodes):
			global start_node
			if self.id in self.active_nodes:
				self.active_nodes =nodes
				print "election starts .. initiated by", self.id
				self.state = "election"
				start_node =1
				eventRPC.set()
				return
			self.active_nodes = self.active_nodes + nodes
			#print "active nodes are", self.active_nodes
			if start_node ==0:			
				eventRPC.set()

		def get_active_nodes(self):
			return self.active_nodes

		def set_connected_to(self, nodes):
			self.connected_to = int(nodes)
			return

		def get_connected_to(self):
			return self.connected_to
		
		def reset_active_nodes(self):
			self.active_nodes =[]

		def election_started(self):
			self.state="election"
		
		def leader_is(self, node):
			if self.leader != 0:
				print "Election completed"
				print "The leader information is circulated to all the nodes. Leader Node: ",self.leader 
				return
			self.leader = node
			self.state="normal"
			eventRPC.set()

		def get_leader(self):
			return self.leader
		
		def get_state(self):
			return self.state
		
		def reset_leader(self):
			self.leader =0

		def get_id(self):
			return self.id
		
		def get_neighbors(self):
			return self.neighbors
	
		def elect_leader(self):
			return max(self.active_nodes)

	server.register_instance(node())
		
	try:
		server.serve_forever()
	except KeyboardInterrupt: ##Not working look into this.
		print "Exiting"
		server.close()
		sys.exit()


def RPCClient():
	global start_node
	'''if start_node==1:  ### explicityly set the start node
		eventRPC.set()
		start_node = 0'''
	node = xmlrpclib.ServerProxy('http://localhost:8014')
	while True:#node.get_state() == "normal":
		eventRPC.wait()
		eventRPC.clear()
		start_node = 0
		node.reset_leader()
		if (node.is_alive()):
			node.set_active_nodes([int(node.get_id())])
			eventRPC.clear()
			neighbor = node.get_neighbors()
			for it in neighbor:
				try:
					s =  xmlrpclib.ServerProxy('http://localhost:'+str(8010+int(it)))
					s.is_alive()
					time.sleep(0.5)
					s1 =  xmlrpclib.ServerProxy('http://localhost:'+str(8000+int(it)))
					s1.is_alive()
					print "\nMy neighbor",it," is active"
					s.set_active_nodes(node.get_active_nodes())
					print "active nodes are", node.get_active_nodes()
					node.set_connected_to(it)
					break
				except: 
					pass
			print "connection established with node: ",node.get_connected_to()
			eventRPC.wait()
			eventRPC.clear()
			if start_node == 1:
				print "Election started from ", node.get_id()	
				leader = node.elect_leader()
				node.leader_is(leader)
				start_node =0
			leader = node.get_leader()
			print "leader elected is ", leader, " reported to",node.get_id()
			s = xmlrpclib.ServerProxy('http://localhost:'+str(8010+int(node.get_connected_to())))
			s.leader_is(node.get_leader())
			node_id = node.get_id()
			node_leader = node.get_leader()				
			time.sleep(0.5)
			try:
				s1 = xmlrpclib.ServerProxy('http://localhost:'+str(8000+4))#int(node.get_connected_to())))
				s1.who_leader(node_leader)
				if node_id==node_leader:
					s1.is_leader()
				s1.start_client()
			except:
				pass
			node.reset_active_nodes()
			start_node = 0
			eventRPC.clear()	


def RPCClient_heartbeat():
	global start_node
	app = xmlrpclib.ServerProxy('http://localhost:8004')
	node = xmlrpclib.ServerProxy('http://localhost:8014')
	neighbor = node.get_neighbors()[0]
	if start_node==1:  ### explicityly set the start node
		eventRPC.set()
		start_node = 0
	while(node.is_alive() and app.is_alive()):
		try:
			neighbor_app = xmlrpclib.ServerProxy('http://localhost:'+str(8000+int(neighbor)))
			while(neighbor_app.is_alive()):
				pass
		except:
			if int(neighbor)==int(node.get_leader()):
				print "Neighbor down ... Starting Leader Election again from doorsensor"
				start_node = 1
				eventRPC.set()
			neighbor=(neighbor+1)%8


thread1 = threading.Thread(target=RPCServer)
thread1.start()
time.sleep(0.5)
thread3 = threading.Thread(target=RPCClient_heartbeat)
thread3.start()
time.sleep(0.5)
thread2 = threading.Thread(target=RPCClient)
thread2.start()
