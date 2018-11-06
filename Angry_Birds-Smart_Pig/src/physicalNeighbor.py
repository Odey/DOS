#!usr/bin/python

''' physicalNeighbor.py: Returns the physical neighbors for a given location'''
__authors__   =  "Rahul Raj, Olenka Dey"
__email__     =  "rraj@umass.edu/odey@umass.edu"

from functools import partial
########################################################			
#########################################################
def find_physical_neighbors(x,y):
    neigh = []
    neigh.append((x-1,y-1))
    neigh.append((x-1,y))
    neigh.append((x-1,y+1))
    neigh.append((x,y-1))
    neigh.append((x,y+1))
    neigh.append((x+1,y-1))
    neigh.append((x+1,y))
    neigh.append((x+1,y+1))
    return neigh

#### find the nearest pig from the bird's launch coordinate
def Find_nearest_pig(bird_coordinates, pigs_location):
	pigs_coord = pigs_location
	dist=lambda s,d: (s[0]-d[0])**2+(s[1]-d[1])**2 #a little function which calculates the distance between two coordinates
	nearest_pig = min(pigs_coord, key=partial(dist, bird_coordinates)) #find the min value using the distance function with coord parameter
	print "Nearest pig to the bird is: ", nearest_pig
	pigs_location = list(sorted(pigs_coord, key=partial(dist, nearest_pig))) 
	return nearest_pig, pigs_location
