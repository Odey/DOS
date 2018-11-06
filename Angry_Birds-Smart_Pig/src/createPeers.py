#!usr/bin/python

''' createPeers.py: This will create n different Directories for n peers also prints grid to the console'''
__authors__   =  "Rahul Raj, Olenka Dey"
__email__     =  "rraj@umass.edu/odey@umass.edu"

import shutil
from shutil import copyfile
import os
import glob
import random
from physicalNeighbor import find_physical_neighbors
###############################################################################
##############################################################################          

##Delete any existing peers and create n new peers node
def create_peers(n,pwd):
    print '\nWill create',n,'new peers...'
    ##For deleting existing peers
    pattern = os.path.join(pwd, "pig*")
    for dirs in glob.glob(pattern):
        #print 'Deleting exiting peers...',dirs
        shutil.rmtree(dirs)
    ##creating n new peers
    for i in xrange(int(n)):
        num=i+1
        #print 'Creating pig (peers)',num,'...'
        os.makedirs(pwd+'/pig'+str(num))
    print '\n'
    return 

#########################################################	
##Create grid############################################
def create_grid(n, bird_coordinates, n_stones):
    bird_coordinates=tuple(bird_coordinates)
    global pigs_location
    pigs_location = []
    global stone_location
    stone_location = []
    global physical_neighbors
    physical_neighbors = {}
    
    n=int(n)
    grid = [['-' for i in range(n)] for j in range(n)] 
    count=0
    random.seed(random.randint(200,900))
    ## coordinate for pigs    
    while (len(pigs_location)<n):
    	x=random.randint(0,n-1)
	y=random.randint(0,n-1)
	if (x,y)!=bird_coordinates:
		pigs_location.append((x,y))
		pigs_location=set(pigs_location)
		pigs_location=list(pigs_location)
    ## coordinates for stones
    while(len(stone_location)< int(n_stones)):
	x = random.randint(0,n-1)
	y = random.randint(0,n-1)
	if (x,y) not in (list(pigs_location)+list(stone_location)+list(bird_coordinates)): #and (x,y) not in (stone_location) and (x,y) not in (bird_coordinates):
		stone_location.append((x,y))
		
    for i in stone_location:
	grid[i[0]][i[1]]='S'
    for i in pigs_location:
	count+=1
	grid[i[0]][i[1]]='P'
    try:
    	grid[int(bird_coordinates[0])][int(bird_coordinates[1])]='B' 
    except:
	print ("Bird are too far from the pigs. Please try again..Exiting!!")
	exit(0) 
    #### create physical neighbors 
    for i in pigs_location:
	p_neighbors = []
	temp = find_physical_neighbors(i[0],i[1])
	for items in temp:
	    if 0<=int(items[0])<(n) and 0<=int(items[1])<(n):
		#pass
	        if grid[items[0]][items[1]]=='-':
		    p_neighbors.append(items)
	physical_neighbors[i]=p_neighbors
    #print physical_neighbors	
    # use generators to create list
    print("                    " + " ".join(str(i) for i in range(n))) 
    # " ".join() puts the " " between each string in the list
    for y in range(n): 
        print("                  "+str(y) + " " + " ".join(grid[y]))
    return pigs_location, stone_location, physical_neighbors
#################################################################################
#################################################################################
