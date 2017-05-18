#!/bin/bash 
log_name=`date +"%F_%H-%M-%S"`
python3 ./bot.py > ./out_$log_name.log 2> ./error_$log_name.log
