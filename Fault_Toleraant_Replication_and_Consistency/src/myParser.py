##start Parsing the eventLog here. 
import xmlrpclib
import time
gnum=0
def get_red(str):
	print "\033[1;31m"+str+"\033[1;m"
	return
def parser(gateway, nodeID_dict):
	if '9001' in str(gateway):
		gnum=2
	else:
		gnum=1
	with open('eventLog',"r+") as f:
		user = xmlrpclib.ServerProxy('http://localhost:8006')
		for line in f:
			if '#' in line:
				pass
			elif line.startswith(' '):
				pass
			elif 'START' in line.strip():
				print '--'*40
				print 'Started parsing the Event log, GATEWAY.'
				
			elif line.startswith('USER'):
				UEVENT=line.split(':')[1].strip()
				time.sleep(0.5)
				if 'DOOR OPEN PS'==UEVENT and 'doorSensor' in nodeID_dict:
					print '--'*40
					print 'This is an User Event:', UEVENT
					user.changeDoorState(1,gateway.clock('U', 'doorSensor'))
				if 'DOOR OPEN'==UEVENT and 'doorSensor' in nodeID_dict:
					print '--'*40
					print 'This is an User Event:', UEVENT
					get_red('INTRUDER!! SOUND ALARM!!')

				if 'DOOR CLOSE' in line.strip() and 'doorSensor' in nodeID_dict:
					print '--'*40
					print 'This is an User Event:', UEVENT
					user.changeDoorState(0,gateway.clock('U', 'doorSensor'))
				
				if 'MOTION ACTIVE' in line.strip() and 'motionSensor' in nodeID_dict:
					print '--'*40
					print 'This is an User Event:', UEVENT
					user.changeMotionState(1,gateway.clock('U', 'motionSensor'))
				
				if 'MOTION INACTIVE' in line.strip() and 'motionSensor' in nodeID_dict:
					print '--'*40
					print 'This is an User Event:', UEVENT
					user.changeMotionState(0,gateway.clock('U', 'motionSensor'))
				
				if 'BULB ON' in line.strip() and 'smartBulb' in nodeID_dict:
					##connect to user. 
					print '--'*40
					print 'This is an User Event:', UEVENT
					user.changeBulbState(1,gateway.clock('U','smartBulb'))
				
				if 'BULB OFF' in line.strip() and 'smartBulb' in nodeID_dict:
					print '--'*40
					print 'This is an User Event:', UEVENT
					user.changeBulbState(0,gateway.clock('U','smartBulb'))
				
				if 'OUTLET ON' in line.strip() and 'smartOutlet' in nodeID_dict:
					print '--'*40
					print 'This is an User Event:', UEVENT
					user.changeOutletState(1,gateway.clock('U','smartOutlet'))
				
				if 'OUTLET OFF' in line.strip() and 'smartOutlet' in nodeID_dict:
					print '--'*40
					print 'This is an User Event:', UEVENT
					user.changeOutletState(0,gateway.clock('U','smartOutlet'))
				
				if 'ENTER' in line:
					print '--'*40
					print 'This is an User Event:', UEVENT
					print 'Order of Events are: doorSensorOpen-->motionSensorActive-->doorSensorClose'
					user.enters()
				if 'EXIT' in line:
					print '--'*40
					print 'This is an User Event:', UEVENT
					print 'Order of Events are: motionSensorActive-->doorSensorOpen-->doorSensorClose-->motionSensorInactive'
					user.exits()
				else:
					pass
					#time.sleep(0.3)
			elif line.startswith('GATEWAY'):
				GEVENT=line.split(':')[1].strip()
				if 'QUERY TEMPERATURE' in line and 'tempSensor' in nodeID_dict:
					print '--'*40
					proc =['tempSensor','G']
					print 'This is an Gateway-'+str(gnum)+' event:', GEVENT
					name='tempSensor'
					temp = xmlrpclib.ServerProxy('http://localhost:8007')
					c=gateway.clock('G','tempSensor')
					gateway.report_state(time.time(),temp.get_ID(c),temp.get_state(c), c,1, proc)
					time.sleep(0.1)

				if 'QUERY BULB STATE' in line and 'smartBulb' in nodeID_dict:
					print '--'*40
					print 'This is an Gateway-'+str(gnum)+' event:', GEVENT
					gateway.queryBulbState(gateway.clock('G', 'smartBulb'))
				
				if 'QUERY DOOR STATE' in line and 'doorSensor' in nodeID_dict:
					print '--'*40
					print 'This is an Gateway-'+str(gnum)+' event:', GEVENT					
					gateway.queryDoorState(gateway.clock('G', 'QdoorSensor'))
				if 'QUERY MOTION STATE' in line and 'motionSensor' in nodeID_dict:
					print '--'*40
					print 'This is an Gateway-'+str(gnum)+' event:', GEVENT	
					gateway.queryMotionState(gateway.clock('G', 'QmotionSensor'))
				if 'QUERY OUTLET STATE' in line and 'smartOutlet' in nodeID_dict:
					print '--'*40
					print 'This is an Gateway-'+str(gnum)+' event:', GEVENT			
					gateway.queryOutletState(gateway.clock('G', 'smartOutlet'))
				if 'BULB ON' in line and 'smartBulb' in nodeID_dict:
					print '--'*40
					print 'This is an Gateway-'+str(gnum)+' event:', GEVENT	
					gateway.changeBulbState(1, gateway.clock('G','smartBulb'))
				if 'BULB OFF' in line and 'smartBulb' in nodeID_dict:
					print '--'*40
					print 'This is an Gateway-'+str(gnum)+' event:', GEVENT		
					gateway.changeBulbState(0, gateway.clock('G','smartBulb'))
				if 'OUTLET ON' in line and 'smartOutlet' in nodeID_dict:
					print '--'*40
					print 'This is an Gateway-'+str(gnum)+' event:', GEVENT	
					gateway.changeOutletState(1, gateway.clock('G','smartOutlet'))
				if 'OUTLET OFF' in line and 'smartOutlet' in nodeID_dict:
					print '--'*40
					print 'This is an Gateway-'+str(gnum)+' event:', GEVENT		
					gateway.changeOutletState(0, gateway.clock('G','smartOutlet'))
				else:
					pass
			elif 'STOP' in line.strip():
				print '--'*40
				time.sleep(0.05)
				print 'Reached end of log file. Finished Parsing.'
				print '--'*40
			elif '#' in line.strip():
				pass
			else:
				pass
			time.sleep(0.3)

