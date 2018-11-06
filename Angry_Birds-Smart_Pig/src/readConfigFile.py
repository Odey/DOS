#!usr/bin/python


''' readConfigFile.py: Parses Config file and has a function to find target coordinate'''
__authors__   =  "Rahul Raj, Olenka Dey"
__email__     =  "rraj@umass.edu/odey@umass.edu"

from createPeers import create_peers, create_grid
import random
import math
from physicalNeighbor import find_physical_neighbors
from initializePeers import init_peers
####GLOBAL VARIABLES##############################
pigs_location=[]
stone_location = []
physical_neighbors ={}
###################################################
##Read the config file#############################
def read_config(pwd):
    conf_path = pwd+'/config'
    with open(conf_path,'r') as f:
        for line in f:
	    if ('#') in line:
		pass
            elif ('Number of pigs') in line:
                line=line.split('=')
                number_pigs=line[1].strip()
                create_peers(number_pigs,pwd)
	

	    elif ('Number of stones') in line:
		line=line.split('=')
                number_stones=line[1].strip()
		
	    elif ('Bird launch Coordinate') in line:
		line=line.split('=')
                bird_coordinates=line[1].strip()
		bird_coordinates= eval(bird_coordinates)
		pigs_location, stone_location, physical_neighbors = create_grid(number_pigs, bird_coordinates, number_stones)	
		print "\n\nBird launch coordinates are: ", bird_coordinates

	    elif ('Bird Speed') in line:
		line=line.split('=')
                bird_speed=line[1].strip()
		#print bird_speed

	    elif ('Bird Direction') in line:
		line=line.split('=')
                bird_direction=line[1].strip()
		#print bird_direction
	
    	    elif('Bird Time in the air') in line:
		line=line.split('=')
                bird_air_time=line[1].strip()
		target_coordinate, hopcount = get_target(number_pigs,bird_coordinates, bird_direction, bird_speed, bird_air_time)
		print "Target coordinates of the birds are: ", target_coordinate
		#print target_coordinate, pigs_location
		if target_coordinate not in  pigs_location:
			if target_coordinate in stone_location:
				c=0
				print "Bird is falling on the Stone!!"
				temp = find_physical_neighbors(target_coordinate[0], target_coordinate[1])
				print "Stones neighbors: ", temp
				for items in temp:
					if items in pigs_location:
						target_coordinate = items
						c=1
						print "Stone is falling on Bird location", target_coordinate
				if(c==0):
					print "Brid falling in open location!!"	
					return -1
			else:			
				return -1
	    elif ('Hop delay') in line:
		line=line.split('=')
                hop_delay=line[1].strip()
		print "Delay in each hop is", hop_delay, "seconds.."
    	    
            elif ('Pigs Neighbors') in line:
		#print "Inside elif"
                line=line.split('=')
                pigs_neighbors=line[1].strip()
                dict_pigs_neighbors = eval(pigs_neighbors)
    		init_peers(number_pigs, dict_pigs_neighbors, pwd, bird_coordinates,target_coordinate, hopcount, pigs_location, physical_neighbors, hop_delay)

	    
	    else:
		pass
		
    return number_pigs #, dict_pigs_neighbors,number_stones, bird_direction, bird_speed, bird_air_time 
#######################################################################################
#######################################################################################
#######################################################################################
##get the bird target location
def get_target(grid_boundary,start_pos, bird_direc, bird_speed, bird_airtime):
	steps_covered = math.ceil((float(bird_speed)*float(bird_airtime)))
	print "Bird will travel ",steps_covered," steps.."
	x = int(start_pos[0])
	y = int(start_pos[1])
	if bird_direc in ['N','NE','NW']: ## managing x direction
		for i in range(int(steps_covered)):
			x = x-1
	elif bird_direc in ['S','SW','SE']:
		for i in range(int(steps_covered)):
			x = x+1
	if bird_direc in ['NW','W','SW']:  ## managing y direction
		for i in range(int(steps_covered)):
			y = y-1
	elif bird_direc in ['NE','E','SE']:
		for i in range(int(steps_covered)):
			y = y+1
	if x not in range(int(grid_boundary)) or y not in range(int(grid_boundary)): ## check if bird goes out of the boundary
		print ("Bird Died !!!") ### try to relaunch the program 
	else:	
		pass
		#print "Target coordinate : ", (x,y) ### send the coordinate to the nearest server  to initiate the game
	return (x,y), steps_covered	



	 

######################################################################################
