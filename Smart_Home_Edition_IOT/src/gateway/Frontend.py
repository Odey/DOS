#!/usr/bin/python

'''FrontEnd.py: This is the central server.'''
import threading
import sys
import time
import socket
from thread import start_new_thread
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import xmlrpclib
from collections import deque
##import timePlot


##Initial lamport clock values.
GC = 0 ##GatwayClock.
UC = 0 ##UserClock.

userEvents={}
node_dict = {} ##NAME:TYPE
nodeID_dict  = {} ##NAME:ID
nodeID_socket = {} ##ID:SOCKET ##this is only used in the case of temperature sensor.
no_nodes   = 1
flag	   = 0
i_am_leader= 0
our_leader = 0
timestamp  = 0
offset 	   = 0
eventElection = threading.Event()
eventRPC    = threading.Event() 
eventReport = threading.Event()
eventnotify = threading.Event()
eventSync   = threading.Event()
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
		report_state(get_timestamp(),no_nodes, 0, [0])
		if(no_nodes == 6):
			time.sleep(0.05)
			print '\n'
			print '='*120
			print "All device registered !!! \n"
			print "Node Name and Node Type are:",node_dict
			print "Node Name and ID are:", nodeID_dict
			print '='*120
			eventRPC.set()
		return no_nodes
	server.register_function(register)

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

	### Function to indicate that leader election is complete and now the application can start
	def start_client():
		global flag
		flag = 1
		eventElection.set()

	server.register_function(start_client)

	### Heartbeat to check if the node is alive or not
	def is_alive():
		return True
	server.register_function(is_alive)

	### to indicate the clock syncrinization is complete.
	def synced():
		eventSync.set()
	server.register_function(synced)

	## requesting backend to report the state of a particular activity
	def report_state(timestamp, ID, state, clock, proc=['x']):
		global UC,GC,userCount
		if GC<clock[0]:
			GC=clock[0]+1
		else:
			GC=GC+1
		global reportQueue, userEvents
		eventnotify.wait()
		eventnotify.clear()
		eventplot([clock[0]]+proc+[GC])
		device_name = [x for x in nodeID_dict.keys() if nodeID_dict[x]==ID]
		reportQueue.clear()
		reportQueue.append(timestamp)
		reportQueue.append(ID)
		reportQueue.append(device_name[0])
		reportQueue.append(state)
		if device_name[0]=='motionSensor' or device_name[0]=='doorSensor':
			if	state==0:
				pass
			else:
				userEvents[device_name[0]]=UC
		if len(userEvents)==2:
			print userEvents
			if userEvents['motionSensor']<userEvents['doorSensor']:
				userCount=userCount-1
				if userCount<0:
					get_red("NO USER INSIDE HOME. CAN'T EXIT HOME!!")
				else:
					get_red('USER EXITING!! TURN ON SECURITY SYSTEM')
			else:
				userCount=userCount+1
				get_red('USER ENTERING!! TURN OFF SECURITY SYSTEM')
			userEvents={}
		print 'Clock value returned from',device_name[0], "is", clock[0],'.'
		print "State reported by", (device_name[0]), "is", state
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


	try:
		server.serve_forever()
	except KeyboardInterrupt: ##Not working look into this.
		print "Exiting"
		server.close()
		sys.exit()


#########################Time Server#######################################
###########################################################################
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

##CHANGE STATE INTERFACE###################################################
###########################################################################
def changeBulbState(value, c):
	bulb = xmlrpclib.ServerProxy('http://localhost:8004')
	bulb.set_state(value, c)
	time.sleep(0.5)
	#print "Bulb device current state returned is", bulb.get_state(c)

##client can connect to the outlet device and change its state.
def changeOutletState(value, c):
	outlet = xmlrpclib.ServerProxy('http://localhost:8005')
	outlet.set_state(value, c)
	time.sleep(0.5)
	#print "Outlet Device current state returned is", outlet.get_state(c)

##QUERY STATE INTERFACES###################################################
###########################################################################
##client can connect to the door sensor and query the state
def queryDoorState(c):
	door = xmlrpclib.ServerProxy('http://localhost:8003')
	print "Door sensor state returned is", door.get_state(c)

##client can connect to the motion sensor and query the state
def queryMotionState(c):
	motion = xmlrpclib.ServerProxy('http://localhost:8002')
	print "Motion sensor state returned is", motion.get_state(c)

##client can connect to the bulb device and query the state
def queryBulbState(c):
	bulb = xmlrpclib.ServerProxy('http://localhost:8004')
	print "Bulb device state returned is", bulb.get_state(c)

##client can connect to the outlet device and query the state
def queryOutletState(c):
	outlet = xmlrpclib.ServerProxy('http://localhost:8005')
	print "Outlet Device state returned is", outlet.get_state(c)

###########################################################################
###########################################################################	
###########################################################################
####################GATEWAY FRON END ENDS HERE#############################

#################back end client#########################################
def ClientFrontend():
	gateway_proxy = xmlrpclib.ServerProxy('http://localhost:8001')
	backend = xmlrpclib.ServerProxy('http://localhost:8008')
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
		backend.save_state(timestamp,nodeID,name,state)
		backend.history(timestamp,nodeID, name, state)
		reportQueue.clear()
		eventnotify.set()


###################USE TO PARSE THE EVENT LOG#######
####USed to start the front end server and client###
#####DIFFERENT FROM FRONT END#######################

def main():
	global flag
	Lock = threading.Lock() ##creating the threading lock.
	Event = threading.Event()
	thread1 = threading.Thread(target=ServerFrontend) ##front end server.
	thread4=threading.Thread(target=ClientFrontend) ##back-end client
	thread3 = threading.Thread(target=LeaderMaster)
	thread1.start() ##start the front-end server. 
	thread4.start() ##start the back-end client.
	thread3.start()
	#eventnotify.set()	## in case: backend doesnot start and does not set the eventnotify
	eventRPC.wait() ##Waiting for all the sensors and devices to register.
	#while flag==0:
	#	pass
	eventElection.wait()	
	eventElection.clear()
	eventSync.wait()
	##start Parsing the eventLog here. 
	with open('eventLog',"r+") as f:
		gateway = xmlrpclib.ServerProxy('http://localhost:8001')
		user = xmlrpclib.ServerProxy('http://localhost:8006')
		for line in f:
			if '#' in line:
				pass
			elif line.startswith(' '):
				pass
			
			elif 'START' in line.strip():
				print '--'*40
				print 'Started parsing the Event log.'
				print '--'*40
			elif line.startswith('USER'):
					##connecting to user server.
				print '--'*40
				UEVENT=line.split(':')[1].strip()
				print 'This is an User Event:', UEVENT
				if 'DOOR OPEN PS'==UEVENT:
					user.changeDoorState(1,gateway.clock('U', 'doorSensor'))
				if 'DOOR OPEN'==UEVENT:
					get_red('INTRUDER!! SOUND ALARM!!')
				if 'DOOR CLOSE' in line.strip():
					user.changeDoorState(0,gateway.clock('U', 'doorSensor'))
				if 'MOTION ACTIVE' in line.strip():
					user.changeMotionState(1,gateway.clock('U', 'motionSensor'))
				if 'MOTION INACTIVE' in line.strip():
					user.changeMotionState(0,gateway.clock('U', 'motionSensor'))
				if 'BULB ON' in line.strip():
					##connect to user. 
					user.changeBulbState(1,gateway.clock('U','smartBulb'))
				if 'BULB OFF' in line.strip():
					user.changeBulbState(0,gateway.clock('U','smartBulb'))
				if 'OUTLET ON' in line.strip():
					user.changeOutletState(1,gateway.clock('U','smartOutlet'))
				if 'OUTLET OFF' in line.strip():
					user.changeOutletState(0,gateway.clock('U','smartOutlet'))
				if 'ENTER' in line:
					print 'Order of Events are: doorSensorOpen-->motionSensorActive-->doorSensorClose'
					user.enters()
				if 'EXIT' in line:
					print 'Order of Events are: motionSensorActive-->doorSensorOpen-->doorSensorClose-->motionSensorInactive'
					user.exits()
			elif line.startswith('GATEWAY'):
				print '--'*40
				GEVENT=line.split(':')[1].strip()
				print 'This is an Gateway event:', GEVENT
				if 'QUERY TEMPERATURE' in line:
					temp = xmlrpclib.ServerProxy('http://localhost:8007')
					c=gateway.clock('G','tempSensor')
					val=temp.get_temp(c)
					tc=temp.Clock()
					proc =['tempSensor','G']
					gateway.report_state(temp.get_timestamp(),temp.get_ID(c),val, tc, proc)
				if 'QUERY BULB STATE' in line:
					queryBulbState(gateway.clock('G', 'smartBulb'))
				if 'QUERY DOOR STATE' in line:
					queryDoorState(gateway.clock('G', 'doorSensor'))
				if 'QUERY MOTION STATE' in line:
					queryMotionState(gateway.clock('G', 'motionSensor'))
				if 'QUERY OUTLET STATE' in line:
					queryOutletState(gateway.clock('G', 'smartOutlet'))
				if 'BULB ON' in line:
					changeBulbState(1, gateway.clock('G','smartBulb'))
				if 'BULB OFF' in line:
					changeBulbState(0, gateway.clock('G','smartBulb'))
				if 'OUTLET ON' in line:
					changeOutletState(1, gateway.clock('G','smartOutlet'))
				if 'OUTLET OFF' in line:
					changeOutletState(0, gateway.clock('G','smartOutlet'))
			elif 'STOP' in line.strip():
				print '--'*40
				time.sleep(0.1)
				print 'Reached end of log file. Finished Parsing.'
				print '--'*40
				#print "plot :", plot_value
				#timePlot.plot(plot_value)
			elif '#' in line.strip():
				pass
			else:
				pass
				#print 'This is an unrecognized Event', line.strip()



	
if __name__=="__main__":
	main()

