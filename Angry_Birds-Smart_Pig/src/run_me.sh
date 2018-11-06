#!/bin/sh
#Below script will kill all the peers created from the same program. 
for _dir in pig*; do
	dir_name=$_dir
	number=$(echo $dir_name| sed 's/[^0-9]*//g')
	name='/peer'
	extn='.py'
	filepath=$dir_name$name$number$extn
	pkill -f $filepath
done
#Start the main program and start all the servers
python 'main.py' 
for _dir in `ls -d -v pig*`; do
	dir_name=$_dir
	number=$(echo $dir_name| sed 's/[^0-9]*//g')
	name='/peer'
	extn='.py'
	start_port=8000
	#Kill any process running on the peers ports
	port_number=$(expr "$start_port" + "$number")  
	fuser -k $port_number/tcp
	#Start the server
	#filename=$dir_name$name$number$extn
	python $dir_name$name$number$extn 2> log &
	
done
echo $array


