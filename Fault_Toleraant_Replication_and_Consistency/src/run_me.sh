#!/bin/sh
echo "Starting and registering All the Devices and Sensors with the Gateway."
echo 'Waiting...'
find . -name \*~ -type f -delete
find . -name \*.pyc -type f -delete
#fuser -k 8001/tcp
#fuser -k 12347/tcp
kill -9 `pgrep python`

if [ "$#" -ne 2 ]; then
    echo "Illegal number of parameters.."
    echo "USAGE: ./run_me.sh Gateway-1_CacheSize Gateway-2_CacheSize"
    exit
fi
## starting the application process
/bin/sleep 0.0	
##Starting the First Replica of Gateway
python gateway_1/Frontend_1.py $1 &
python gateway_1/Backend_1.py &
##Starting the Second Replica of Gateway
python gateway_2/Frontend_2.py $2 &
python gateway_2/Backend_2.py &
##Starting all the Sensors and Devices
python tempSensor/tempSensor.py &
/bin/sleep 0.1
python smartOutletDevice/smartOutlet.py &
/bin/sleep 0.1
python doorSensor/doorSensor.py &
/bin/sleep 0.1
python smartBulbDevice/smartBulb.py &
/bin/sleep 0.1
python motionSensor/motionSensor.py & 
python user/user.py &
/bin/sleep 1.5
pkill -f Frontend_1.py



