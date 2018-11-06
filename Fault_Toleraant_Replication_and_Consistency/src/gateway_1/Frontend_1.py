#!/usr/bin/python

'''FrontEnd.py: This is the central server.'''
import threading
import sys, os
import time
import socket
from thread import start_new_thread
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import xmlrpclib
from collections import deque, defaultdict
sys.path.append(os.getcwd())
import myParser
#import timePlot

###Caching 
##{sensor/Device name: [timestamp, current_value]}
cacheSize=0
cacheHit=0
cacheMiss=0
cache = defaultdict(list)
printFlag = 0
###
##Initial lamport clock values.
GC = 0 ##GatwayClock.
UC = 0 ##UserClock.

userEvents={}
node_dict = {} ##NAME:TYPE
nodeID_dict  = {} ##NAME:ID
nodeID_socket = {} ##ID:SOCKET ##this is only used in the case of temperature sensor.
no_nodes   = 1
timestamp  = 0
offset 	   = 0
eventRPC    = threading.Event() 
eventReport = threading.Event()
eventnotify = threading.Event()
reportQueue = deque() ##queue for the report.
plot_value  = []
userCount   = 0

def get_red(str):
	print "\033[1;31m"+str+"\033[1;m"
	return

#############GATEWAY FRON END SERVER######################################
##########################################################################	
def ServerFrontend():
	class RequestHandler(SimpleXMLRPCRequestHandler):
		rpc_paths = ('/RPC2',)
	# Create server
	server = SimpleXMLRPCServer(("localhost", 8001), requestHandler=RequestHandler,logRequests=False, allow_none=True)
	server.register_introspection_functions()

	## used for registering the nodes in the network
	def register(nodeType,name):
		global node_dict, nodeID_dict, no_nodes
		no_nodes=no_nodes+1
		node_dict[name]=nodeType
		nodeID_dict[name]=no_nodes
		print "Registering ",name," with gateway 1 with node ID ", no_nodes
		report_state(time.time(),no_nodes, 0,[0],0)
		return no_nodes
	server.register_function(register)

	def is_complete():
		##connecting to other gateway to check the load.
		other_gateway=xmlrpclib.ServerProxy('http://localhost:9001')
		if(other_gateway.is_complete()):
			time.sleep(0.05)
			print '\n'
			print '='*120
			print "All device registered to gateway - 1 are !!! \n"
			print "Node Name and Node Type are:",node_dict
			print "Node Name and ID are:", nodeID_dict
			print '='*120
			eventRPC.set()
			return True
		else:
			return False
	server.register_function(is_complete)

	def get_load_status():
		global node_dict
		return len(node_dict.keys())
	server.register_function(get_load_status)

	def get_timestamp():
		global timestamp,offset
		timestamp = time.time()+offset
		return timestamp
	server.register_function(get_timestamp)

	def get_myDevices():
		return nodeID_dict
	server.register_function(get_myDevices)


	## corrects the time of this node during clock synchronization.
	def correct_time(val):
		global timestamp,offset
		offset = val
		timestamp = timestamp + val
		print "corrected time ", timestamp
	server.register_function(correct_time)


	## maintiaining clock information.
	def clock(callingProcess,calledProcess):
		global GC, UC ##gateway clock and user clock.
		if callingProcess == 'U':		
			UC=UC+1
			print 'Calling', calledProcess, 'from User Process. User current clock value is', UC 
			return [UC,callingProcess,calledProcess]
		elif callingProcess == 'G':		
			GC=GC+1
			print 'Calling', calledProcess, 'from Gateway Front End. Gateway current clock value is', GC 
			return [GC,callingProcess,calledProcess]
		else:
			print 'Unable to process the request.'
	server.register_function(clock)

	

	### Heartbeat to check if the node is alive or not
	def is_alive():
		return True
	server.register_function(is_alive)

	

	## requesting backend to report the state of a particular activity
	def report_state(timestamp, ID, state, clock,cached,proc=['x']):
		
		global UC,GC,userCount
		if GC<clock[0]:
			GC=clock[0]+1
		else:
			GC=GC+1
		global reportQueue, userEvents, printFlag, cacheMiss, cacheHit
		eventnotify.wait()
		eventnotify.clear()
		eventplot([clock[0]]+proc+[GC])
		device_name = [x for x in nodeID_dict.keys() if nodeID_dict[x]==ID]
		dname=device_name[0]
		if 'Q' in proc[0]:
			dname=dname+'Q'
			
		reportQueue.clear()
		reportQueue.append(timestamp)
		reportQueue.append(ID)
		reportQueue.append(dname)
		reportQueue.append(state)
		##caching the current state 
		if int(cached)==1:
			#cacheMiss=cacheMiss+1
			pass
		elif device_name[0] in cache.keys() and cacheSize!=0:
			get_red('Updating the cache in Gateway-1.')
			cache.pop(device_name[0])
			cache[device_name[0]].append(timestamp)
			cache[device_name[0]].append(ID)
			cache[device_name[0]].append(state)
			cache[device_name[0]].append(clock)
			cacheHit=cacheHit+1

		elif len(cache)<=cacheSize and cacheSize!=0 and device_name[0] not in cache.keys():
			if len(cache)==cacheSize:
				get_red('Cache full in GATEWAY-1 Evicting the cache using LRU and caching the current item')
				lru(device_name[0], state, timestamp, ID, clock)
				cacheMiss=cacheMiss+1
			else:		
				get_red('Adding the cache in Gateway-1.')
				cache[device_name[0]].append(timestamp)
				cache[device_name[0]].append(ID)
				cache[device_name[0]].append(state)
				cache[device_name[0]].append(clock)
				cacheHit=cacheHit+1
		else:
			if cacheSize==len(cache)-1 and cacheSize!=0:
				cacheMiss=cacheMiss+1
				get_red('Cache full in GATEWAY-1 Evicting the cache using LRU and caching the current item')
				lru(device_name[0], state, timestamp, ID, clock)
			else:
				if printFlag==0:
					printFlag=1
					get_red('Will Proceed Without Caching as cacheSize is 0')
		eventReport.set()
	server.register_function(report_state)

	## for plotting the events
	def eventplot(sequence):
		global plot_value
		backend = xmlrpclib.ServerProxy('http://localhost:8008')
		backend.saveclockplot(sequence)
		if len(sequence)==4:
			plot_value.append(sequence)
	server.register_function(eventplot)

	##LRU caching
	def lru(name, val, time_now, ID, clock):
		t=[]
		for key, values in cache.iteritems():
			t.append(values[0])
		t_sort=sorted(t)
		min_t=t_sort.pop(0)
		for key, values in cache.iteritems():
			if values[0]==min_t:
				lru_key=key
		cache.pop(lru_key)
		cache[name].append(time_now)
		cache[name].append(ID)
		cache[name].append(val)
		cache[name].append(clock)
		return
	server.register_function(lru)

	##caching implementation
	def caching(name, obj, c):
		global cacheMiss, cacheHit
		val = obj.get_state(c)
		#time_now = obj.get_timestamp()
		time_now=time.time()
		ID=obj.get_ID(c)
		clock=obj.Clock()
		if len(cache)<= cacheSize and cacheSize!=0:
			get_red('caching the new data..!!')
			##caching the contents 
			cache[name].append(time_now)
			cache[name].append(ID)
			cache[name].append(val)
			cache[name].append(clock)
		else:
			if cacheSize!=0:
				cacheMiss=cacheMiss+1
				get_red('Cache full in GATEWAY-1 Evicting the cache using LRU and caching the current item')
				lru(name, val, time_now, ID, clock)
			else:
				get_red('Will Proceed Without Caching as cacheSize is 0')
		return time_now,ID,val, clock
	server.register_function(caching)

	def changeBulbState(value, c):
		global printFlag
		printFlag=0
		bulb = xmlrpclib.ServerProxy('http://localhost:8004')
		bulb.set_state(value, c)
		time.sleep(0.25)
	server.register_function(changeBulbState)

	def changeOutletState(value, c):
		global printFlag
		printFlag=0
		outlet = xmlrpclib.ServerProxy('http://localhost:8005')
		outlet.set_state(value, c)
		time.sleep(0.25)
	server.register_function(changeOutletState)	

	def queryDoorState(c):
		global cacheHit
		name='QdoorSensor'
		proc =[name,'G']
		if name in cache.keys() and cacheSize!=0:
			cacheHit=cacheHit+1
			get_red('Using the cached data.')
			report_state(time.time(), cache[name][1], cache[name][2], cache[name][3], 1,proc)
			time.sleep(0.05)	
		else:
			door = xmlrpclib.ServerProxy('http://localhost:8003')
			time_now,ID,val, clock=caching(name, door, c)
			print "Door sensor state returned is", val
			report_state(time_now,ID,val, clock, 0,proc)
			time.sleep(0.1)
	server.register_function(queryDoorState)

	def queryMotionState(c):
		global cacheHit
		name='QmotionSensor'
		proc =[name,'G']
		if name in cache.keys() and cacheSize!=0:
			cacheHit=cacheHit+1
			get_red('Using the cached data.')
			report_state(time.time(), cache[name][1], cache[name][2], cache[name][3], 1,proc)
			time.sleep(0.05)		
		else:
			motion = xmlrpclib.ServerProxy('http://localhost:8002')
			##Querying the states and caching
			time_now,ID,val, clock=caching(name, motion, c)
			print "Motion sensor state returned is", val
			report_state(time_now,ID,val, clock, 0,proc)
			time.sleep(0.1)
	server.register_function(queryMotionState)

	

	def queryBulbState(c):
		global cacheHit
		name='smartBulb'
		proc =[name,'G']
	
		if name in cache.keys() and cacheSize!=0:
			cacheHit=cacheHit+1
			get_red('Using the cached data.')
			#print cache[name][0], cache[name][1], cache[name][2], cache[name][3], proc
			report_state(time.time(), cache[name][1], cache[name][2], cache[name][3], 1,proc)
			time.sleep(0.05)	
		else:
			bulb = xmlrpclib.ServerProxy('http://localhost:8004')
			time_now,ID,val, clock=caching(name, bulb, c)
			print "Bulb device state returned is", val
			report_state(time_now,ID,val, clock, 0,proc)
			time.sleep(0.1)
	server.register_function(queryBulbState)


	##client can connect to the outlet device and query the state
	def queryOutletState(c):
		global cacheHit
		name='smartOutlet'
		proc =['smartOutlet','G']
		if name in cache.keys() and cacheSize!=0:
			cacheHit=cacheHit+1
			get_red('Using the cached data.')
			#print cache[name][0], cache[name][1], cache[name][2], cache[name][3], proc
			report_state(time.time(), cache[name][1], cache[name][2], cache[name][3],1, proc)
			time.sleep(0.05)	
		else:
			outlet = xmlrpclib.ServerProxy('http://localhost:8005')
			time_now,ID,val, clock=caching(name, outlet, c)
			print "Outlet device state returned is", val
			report_state(time_now,ID,val, clock,0, proc)
			time.sleep(0.1)
	server.register_function(queryOutletState)
	try:
		server.serve_forever()
	except KeyboardInterrupt: ##Not working look into this.
		print "Exiting"
		server.close()
		sys.exit()


####################GATEWAY FRON END ENDS HERE#############################



#################back end GATEWAY#########################################
def ClientFrontend():
	gateway_proxy = xmlrpclib.ServerProxy('http://localhost:8001')
	backend_1 = xmlrpclib.ServerProxy('http://localhost:8008')
	backend_2 = xmlrpclib.ServerProxy('http://localhost:9008')
	eventnotify.set()
	while True:
		eventReport.wait()
		eventReport.clear()
		if len(reportQueue)<1:
			pass
		state = reportQueue.pop()
		name = reportQueue.pop()
		nodeID = reportQueue.pop()
		timestamp = reportQueue.pop()
		print "Sending to the backend :","node ID is",nodeID,", Sensor/Device name is",name,", current state is",state
		backend_1.save_state(timestamp,nodeID,name,state)
		backend_1.history(timestamp,nodeID, name, state)
		backend_2.save_state(timestamp,nodeID,name,state)
		backend_2.history(timestamp,nodeID, name, state)
		reportQueue.clear()
		eventnotify.set()


##FAILURE RECOVERY
########################################################################
def failureRecovery(devices):
	failed=9001
	device_port = {'smartBulb':8004, 'smartOutlet':8005, 'tempSensor':8007, 'motionSensor':8002, 'doorSensor':8003}
	for key, ID in devices.iteritems():
		port=device_port[key]
		node = xmlrpclib.ServerProxy('http://localhost:'+str(port))
		node.reconfigure(failed)
		
########################################################################
def ClientHeartbeat():
	global nodeID_dict
	time.sleep(1)
	replica=xmlrpclib.ServerProxy('http://localhost:9001')
	try:
		while (replica.is_alive()):
			replica_devices=replica.get_myDevices()
			pass
	except:
		nodeID_dict.update(replica_devices)
		print "Devices connected to Failed replica are",replica_devices
		get_red('GATEWAY-2 FAILED. INITIATE FAILURE RECOVERY.')
		failureRecovery(replica_devices)
########FAILURE DETECTION AND RECOVERY ENDS HERE#######################
def eventDetection():
	eventOrder={}
	thefile= open(os.getcwd()+'/gateway_1/DB/history.csv','r')
	thefile.seek(0,2)
	while True:
        	line = thefile.readline()
        	if not line:
            		time.sleep(0.05)
            		continue
		if len(eventOrder)!=2:
			if 'Q' in line:
				pass
			elif 'door' in line:
        			eventOrder['door']=float(line.split(",")[0][1:17])
				#print float(line.split(",")[0][1:17])
			elif 'motion' in line:
				eventOrder['motion']=float(line.split(",")[0][1:17])
				#pass
		else:
			if((eventOrder['motion']-eventOrder['door'])<0):
				get_red("USER EXIT")
			else:
				get_red("USER ENTERED")
			eventOrder={}


###################USE TO PARSE THE EVENT LOG#######
####USed to start the front end server and client###
#####DIFFERENT FROM FRONT END#######################

def main():
	start=time.time()
	Lock = threading.Lock() ##creating the threading lock.
	Event = threading.Event()
	thread1 = threading.Thread(target=ServerFrontend) ##front end server.
	thread4=threading.Thread(target=ClientFrontend) ##back-end client
	thread1.start() ##start the front-end server. 
	thread4.start() ##start the back-end client.
	time.sleep(0.2)
	thread2 = threading.Thread(target=ClientHeartbeat)
	thread2.start()
	##waiting for registeration to complete. 
	gateway=xmlrpclib.ServerProxy('http://localhost:8001')
	while (not gateway.is_complete()):
		pass
	eventRPC.wait() ##Waiting for all the sensors and devices to register.
	#print "G1",time.time()
	thread3= threading.Thread(target=eventDetection)
	thread3.start()
	myParser.parser(gateway, nodeID_dict)
	
	end=time.time()
	print "Total time taken to complete the GATEWAY-1 program is", end-start
	print "Total cache hits are",cacheHit,"and miss are", cacheMiss


	
if __name__=="__main__":
	cacheSize=int(sys.argv[1])
	main()

