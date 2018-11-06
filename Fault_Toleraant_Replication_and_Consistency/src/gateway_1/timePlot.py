import matplotlib.pyplot as plt
import string
import numpy as np

proc = {'G':1,'motionSensor':2,'doorSensor':3,'smartBulb':4,'smartOutlet':5,'U': 6, 'tempSensor':7}
proc_name = ['G','motionSensor','doorSensor','smartBulb','smartOutlet','U', 'tempSensor']

def diff_color():
    return plt.cm.gist_ncar(np.random.random())

def plot(plot_value):
	global proc
	num_process = 9
	max_timestamp=20
	#print plot_value
	
	##horizontal lines
	for i in range(max_timestamp):
		plt.plot([0, num_process - 1], [i, i], "k--", linewidth=0.5)

    	#vertical lines
	for i in range(num_process):
		plt.plot([i, i], [-0.5, max_timestamp+0.5], "k")
	
	
	#process labels
	for i in range(num_process):
		if i==0 or i==8:
			pass
		else:
			plt.text(i, max_timestamp+0.5, "P_${}$".format(proc_name[i-1]), rotation="vertical", horizontalalignment="center", fontsize=12)

	## plotting the events
	for i in plot_value:	
		plt.plot((proc[i[1]],proc[i[2]]),(i[0],i[3]),'k',linewidth=3, color=diff_color())

	plt.show()		

