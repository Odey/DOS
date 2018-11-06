#!/bin/sh
echo 'Waiting...'
find . -name \*~ -type f -delete
find . -name \*.pyc -type f -delete
kill -9 `pgrep python`

## starting the application process
/bin/sleep 0.2
python gateway1.py &
python gateway2.py &
python gateway3.py &
python gateway4.py &
python gateway5.py &
/bin/sleep 0.5
python Gateway6.py &
/bin/sleep 1
python Tempsensor.py &
/bin/sleep 0.1
python Motionsensor.py &
/bin/sleep 0.1
python smartBulb.py &



