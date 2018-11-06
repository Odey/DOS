#!/bin/sh
echo "Starting and registering All the Devices and Sensors with the Gateway."
echo 'Waiting...'
find . -name \*~ -type f -delete
find . -name \*.pyc -type f -delete
fuser -k 8001/tcp
fuser -k 12347/tcp
kill -9 `pgrep python`

## starting the application process
/bin/sleep 1
python gateway/Frontend.py &
python gateway/Backend.py &
/bin/sleep 1
python tempSensor/tempSensor.py &
python motionSensor/motionSensor.py & 
python doorSensor/doorSensor.py &
python smartBulbDevice/smartBulb.py &
python smartOutletDevice/smartOutlet.py &
python user/user.py &

## starting the leader election process
if true
then
echo "Running Leader Election algorithm at all the nodes."
python gateway/leaderElection_frontend.py &
python gateway/leaderElection_backend.py &
python tempSensor/leaderElection_tempSensor.py &
python motionSensor/leaderElection_motionSensor.py & 
python doorSensor/leaderElection_doorSensor.py &
python smartBulbDevice/leaderElection_smartBulb.py &
python smartOutletDevice/leaderElection_smartOutlet.py &
python user/leaderElection_user.py &
fi

