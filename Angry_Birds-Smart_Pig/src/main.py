#!/usr/bin/python

''' main.py: Starts the program by reading the config File'''
__authors__   =  "Rahul Raj, Olenka Dey"
__email__     =  "rraj@umass.edu/odey@umass.edu"


import os
from readConfigFile import read_config

pigs_location=[]
stone_location = []
physical_neighbors ={}
#############################################################
#############################################################
def get_red(str):
	print "\033[1;31m"+str+"\033[1;m"
	return
           
def main():
    pwd=os.getcwd()
    n = read_config(pwd)
    while n==-1:
	get_red("Bird Died..")
	#print "Bird died.."
	try:
		inp=input("Press 1 to restart or 2 to change config file and press Enter..: ")
	except:
		print("Invalid Input..Exiting!!")
	if inp==1:	
		print ("Restarting..")
		n=read_config(pwd)
	elif inp==2:
		print "Opening config file, Change config file and try again, Exiting!!"
		try:
			subprocess.Popen(['gedit','config'])
		except:
			pass
		exit(1)
	else:
		print "Invalid input..Exiting!"
		exit(1)

if __name__== '__main__':
    main()
