#!/bin/bash

config_file=${RTCONF_CONF_FILE:-config.json}
echo "Config file: "$config_file
pwd_file=$(grep '"pwd"' $config_file | cut -d'"' -f 4)
echo "Pwd file   : "$pwd_file

if [[ ! -z "${RTCONF_PWD_FILE_CONTENTS}" ]]; then
  echo "Creating mqtt_pwd.txt from env."
  echo ${RTCONF_PWD_FILE_CONTENTS} > $pwd_file
fi

for key in $(tail -n +2 config.json | head -n -1 | cut -d':' -f1 | sed 's/\"//g')
do
  conf_key=RTCONF_`echo $key | tr '[:lower:]' '[:upper:]'`
  if [[ ! -z "${!conf_key}" ]]; then
    echo  "Replacing conf: "${conf_key}:${!conf_key}
    sed -i "s/\"$key\"\:.*/\"$key\"\:${!conf_key},/" $config_file
  fi 
done 

#make migrate
#python manage.py runserver 0.0.0.0:8000
