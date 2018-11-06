#!usr/bin/python


''' initializePeers.py: Initialize the peers with the server and client code.'''
__authors__   =  "Rahul Raj, Olenka Dey"
__email__     =  "rraj@umass.edu/odey@umass.edu"


import os
import random
from shutil import copyfile
from physicalNeighbor import Find_nearest_pig
######################################################################################
##Initialize peers with the port numbers and coordinates
def init_peers(n, neighbors, pwd, bird_coordinates, target_coordinate, hopcount, pigs_location, physical_neighbors, hop_delay):
    hop_delay = float(hop_delay)/1000
    ## check the nearest pig from the birds coordinate to send the target coordinate
    nearest_pig, pigs_location = Find_nearest_pig(bird_coordinates, pigs_location)
    print "Pigs locations are ", pigs_location 
    print "\n"   
    for i in xrange(int(n)):
        num=int(i+1)
        target=(pwd+'/pig'+str(num))
        if not os.path.exists(os.path.dirname(target)):
            print "Peer doesn't exists..Exiting!!"
            exit(1)
        else:
            ##Copy the peer (server code) with the desired port number 
            #copyfile(pwd+'/peer.py', target+'/peer'+str(num)+'.py')
            with open(pwd+'/peer'+'.py') as f1:
                 with open(target+'/peer'+str(num)+'.py','w+') as f2:
                     for line in f1:
                         if 'portNumberServer' in line:
                             f2.write('        '+'server = SimpleXMLRPCServer(("localhost",'+str(8000+num)+')'+', requestHandler=RequestHandler, logRequests=False, allow_none=True)')
                         else:
                             f2.write(line)
            f1.close()
            f2.close()

	##Copy the peer (client code) with the desired port numbers
	if num in [int(x) for x in neighbors.keys()]: ##neighbors exists
            with open(target+'/peer'+str(num)+'.py') as f1:
                 with open(target+'/tmp'+'.py','w+') as f2:
                     for line in f1:
                         if 'portNumberToConnect' in line:
			     f2.write('    '+'s1'+"= xmlrpclib.ServerProxy('http://localhost:"+str(8000+num)+"')"+'\n')			
			     f2.write('    print "=============================================================="\n')
			     f2.write('    print '+"'Client - "+str(num)+" Connected to its own server..'"+'\n')
			     f2.write('    my_location = s1.my_loc()'+'\n')
			     f2.write('    cord,hop = s1.get_target()'+'\n')
			     #if (pigs_location[num-1]!=nearest_pig):
			         #f2.write('    while(not s1.get_visited()):'+'\n')
			         #f2.write('    	time.sleep(1)'+'\n')
			     #f2.write('    print s1.get_target()'+'\n')
			     f2.write('    print '+ "'Location of peer-"+str(num)+" with port number ',"+str(8000+num)+', "is ",'+'my_location'+'\n')
			     f2.write('    ret = s1.check_coordinate(cord,hop)'+'\n')
			     f2.write('    if ret:'+'\n')
                             for nbr in neighbors[num]:
                                 f2.write('        '+'s'+"= xmlrpclib.ServerProxy('http://localhost:"+str(8000+nbr)+"')"+'\n')
				 f2.write('        print '+"'Client "+str(8000+num)+ ' Established connection with the server '+str(8000+nbr)+"'\n")
				 #f2.write('    cord,hop=s1.get_target()'+'\n')
				 #f2.write('    ret = s1.check_coordinate(cord,hop)'+'\n')
				 #f2.write('    if ret:'+'\n')
				 f2.write('        time.sleep('+str(hop_delay)+')'+'\n')
				 f2.write('        s.set_target(cord,hop)'+'\n')
			     f2.write('    else:'+'\n')
			     f2.write('        print  "Have to restart the game"'+'\n')
                                 #f2.write('    '+'print s.pow('+str(nbr)+','+str(num-5)+')'+'\n')
			 elif 'my_coordinate = p' in line:
			     f2.write('    '+'my_phy_neighbors = '+str(physical_neighbors[pigs_location[num-1]])+'\n')
			     f2.write('    '+'my_coordinate = '+str(pigs_location[num-1])+'\n')
			     
			 elif 'target_coordinate = -99' in line and (pigs_location[num-1]==nearest_pig):
			     f2.write('                '+'target_coordinate = '+str(target_coordinate)+'\n')
			 elif 'hopcount = -99' in line  and (pigs_location[num-1]==nearest_pig):
			     f2.write('                '+'hopcount = '+str(hopcount)+'\n')
			     #f2.write('    '+'visited = True'+'\n')
			 elif 'visited = xyz' in line: # and (pigs_location[num-1]==nearest_pig):
			     f2.write('    '+'visited = os.getcwd()+'+"'/pig"+str(num)+"'"+'\n')
                         else:
                             f2.write(line)
            f1.close()
            f2.close()
	    ##if no neighbor of pig then make the first pig as its neighbor. Otherwise there are chances that we have unconnected peer. 
        else:
            with open(target+'/peer'+str(num)+'.py') as f1:
                 with open(target+'/tmp'+'.py','w+') as f2:
                     for line in f1:
                         if 'portNumberToConnect' in line:
			     #f2.write('    time.sleep(5)'+'\n')
			     f2.write('    '+'s1'+"= xmlrpclib.ServerProxy('http://localhost:"+str(8000+num)+"')"+'\n')			
			     f2.write('    print "=============================================================="\n')
			     f2.write('    print '+"'Client - "+str(num)+" Connected to its own server..'"+'\n')
			     f2.write('    my_location = s1.my_loc()'+'\n')
			     f2.write('    cord,hop = s1.get_target()'+'\n')
			     f2.write('    print ' +"'Location of peer-"+str(num)+" with port number ',"+str(8000+num)+' ,"is ",'+'my_location'+'\n')
			     #f2.write('    cord,hop=s.get_target()'+'\n')
			     f2.write('    ret = s1.check_coordinate(cord,hop)'+'\n')
			     f2.write('    if ret:'+'\n')
                             f2.write('        '+'s'+"= xmlrpclib.ServerProxy('http://localhost:"+str(8001)+"')"+'\n')
			     f2.write('        print '+"'Client "+str(int(8000+num))+ ' Established connection with the server '+str(8001)+"'\n")
			     #f2.write('    cord,hop=s1.get_target()'+'\n')
			     #f2.write('    ret = s1.check_coordinate(cord,hop)'+'\n')
			     #f2.write('    if ret:'+'\n')
			     f2.write('        time.sleep('+str(hop_delay)+')'+'\n')
			     f2.write('        s.set_target(cord,hop)'+'\n')
                 	     f2.write('    else:'+'\n')
		             f2.write('        print  "Have to restart the game"'+'\n')
			 elif 'my_coordinate = p' in line:
			     f2.write('    '+'my_phy_neighbors = '+str(physical_neighbors[pigs_location[num-1]])+'\n')
			     f2.write('    '+'my_coordinate = '+str(pigs_location[num-1])+'\n')     
			 elif 'target_coordinate = -99' in line and (pigs_location[num-1]==nearest_pig):
			     f2.write(line.replace('-99',str(target_coordinate)))
			 elif 'hopcount = -99' in line  and (pigs_location[num-1]==nearest_pig):
			     f2.write('        '+'hopcount = '+str(hopcount)+'\n')
			     #f2.write('    '+'visited = True'+'\n')
			 elif 'visited = xyz' in line:
			     f2.write('    '+'visited = os.getcwd()+'+"'/pig"+str(num)+"'"+'\n')
                         else:
                             f2.write(line)	
                         
            f1.close()
            f2.close() 
       
        copyfile(target+'/tmp.py', target+'/peer'+str(num)+'.py')
        os.remove(target+'/tmp.py')
            
    #print "Peers Initialized..."
    return 
