#!usr/bin/python

''' peer.py: This will create the peers. Contains a Server class and client definition and starts 2 different threads'''
__authors__   =  "Rahul Raj, Olenka Dey"
__email__     =  "rraj@umass.edu/odey@umass.edu"



import xmlrpclib
import threading
import time
import socket
import os
import random
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

'''
class myThread (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name

    def run(self):
        print "Starting " + self.name
        # Get lock to synchronize threads
        threadLock.acquire()
        if 'Server' in self.name:
            print ('Starting XMLRPC Server..')
            RPCServer()
        else:
            print ('Starting XMLRPC Client..')
            RPCClient()
        # Free lock to release next thread
        threadLock.release()
'''

def RPCServer():
    # Restrict to a particular path.
    global once_reached
    once_reached = False
    global my_coordinate
    visited = xyz
    my_coordinate = p
    #target1_coordinate = -99
    #hop1count = -99
    try:
        class RequestHandler(SimpleXMLRPCRequestHandler):
            rpc_paths = ('/RPC2',)

            # Create server
    
        server = SimpleXMLRPCServer(("localhost", portNumberServer), requestHandler=RequestHandler, logRequests=False)
        
        server.register_introspection_functions()

        # Register pow() function; this will use the value of
        # pow.__name__ as the name, which is just 'pow'.
        server.register_function(pow)

	##Call my_location to get information about the servers location.
	def my_location():
		return my_coordinate
	server.register_function(my_location, 'my_loc')
	
	## get target coordinates and hopcount
	

	def set_target(tc, hc):
		global target_coordinate
		global hopcount
		target_coordinate = tc
		hopcount = hc
		tmp_path = visited+'/tmp.txt'
		#print tmp_path
		with open(visited+'/tmp'+'.txt','w+') as f2:
		    f2.write("target_coordinate = "+str(target_coordinate)+'\n')
		    f2.write("hopcount = "+str(int(hopcount)-1)+'\n')
		f2.close()
		return target_coordinate, hopcount
	server.register_function(set_target, 'set_target')
	
	def get_visited():
		#global visited
		return (os.path.exists(visited+'/tmp'+'.txt'))
	server.register_function(get_visited, 'get_visited')


	###################################################################
	def get_target():
		global target_coordinate
		global hopcount
		#global visited
		count = 1 
		target_coordinate = -99
		hopcount = -99 
		if (target_coordinate!= -99):
		    print "Target Coordinate is ", target_coordinate
		    print "Hopcount at location ",my_coordinate," is ", hopcount,"\n"
		    return target_coordinate,hopcount
		#tmp_path = visited+'/tmp.txt'
		while(not os.path.exists(visited+'/tmp'+'.txt')):
			time.sleep(count)
			count = 2*count
			pass
		with open(visited+'/tmp.txt','r') as f1:
		    for line in f1:
			if "target_coordinate = " in line:
			    target_coordinate = line.split('=')[1].strip()
			if "hopcount = " in line:
			    hopcount = line.split('=')[1].strip()
		print "Target Coordinate is ", target_coordinate
		print "Hopcount at location ",my_coordinate," is ", hopcount,"\n" 
		return target_coordinate, hopcount
	server.register_function(get_target, 'get_target')
	#return target_coordinate, hopcount
	
	#############################################################################
	##Check coordinate
	def check_coordinate(target_coordinate, hopcount):
		global my_coordinate
		tar_cord = list(my_coordinate)
		if int(hopcount) > 0:
			#if(str(tar_cord) > str(target_coordinate)):
				
			if str(tar_cord)==str(target_coordinate):
				#check if neigbor exists or not
				#print "Need to move to nearest available location" 
		    		print "\033[1;31mNeed to move to nearest available location\033[1;m"
				#new_my_coordinate=my_phy_neighbors[random.randint(0,len(my_phy_neighbors))]
				if(len(my_phy_neighbors)==0):
					print "\033[1;3mPig Died !! No nearset location available to move.\033"
					return 0
				new_my_coordinate=my_phy_neighbors.pop(0)
				print "Pig at location",my_coordinate,"moved to",new_my_coordinate,"in order to avoid bird!!"
				print "\033[1;31mPig moved to safe location. Bird Dies!!\033[1;m"
				
				my_coordinate = new_my_coordinate
		    		return 0
			else: 
		    		print "sending location to my next peer"
		    		return 1
		elif int(hopcount) == 0:
		    if str(tar_cord)==str(target_coordinate):
			print "\033[1;31mBird just Hit the pig !! This pig died\033[1;m"
		    else:
		    	print "\npig at location ", list(eval(target_coordinate)), " died !!"
			
		    return 0

	server.register_function(check_coordinate, 'check_coordinate')


        # Register an instance; all the methods of the instance are
        # published as XML-RPC methods (in this case, just 'div').
        class MyFuncs:
            def div(self, x, y):
                return x // y

        server.register_instance(MyFuncs())

        # Run the server's main loop
        server.serve_forever()
        
    except:
        print ("Server on the specified port already running..")



def RPCClient():
    time.sleep(2)

    s = xmlrpclib.ServerProxy('http://localhost:'+portNumberToConnect)
    
    # Print list of available methods
    #print s.system.listMethods()


threadLock = threading.Lock()
threads = []
# Create new threads
#thread1 = myThread(1, "Thread-Server")
#thread2 = myThread(2, "Thread-Client")

thread1 = threading.Thread(target=RPCServer)
thread2 = threading.Thread(target=RPCClient)
# Start new Threads
thread1.start()
thread2.start()

# Add threads to thread list
threads.append(thread1)
threads.append(thread2)

# Wait for all threads to complete
for t in threads:
    t.join()
print "Exiting Main Thread"
exit()
