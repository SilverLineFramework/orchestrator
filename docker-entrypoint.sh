#!/bin/bash
# writes env variables to config files
# important:
#    - json config file must exist and have the entries with some default values
#    - to insert a string value in the json config double quotes must be escaped: \"some-string-value\"
#
# supports:
#    OCONF_CONF_FILE: json config filename (default: config.json)
#    OCONF_PWD_FILE_CONTENTS: writes env var value into password file (password filename as given in config file)
#    OCONF_<any key in config file in caps: HTTP, HTTP_PORT, DEBUG>: set the value of any entry in the config file 
#
config_file=${OCONF_CONF_FILE:-config.json}
echo "Config file: "$config_file
pwd_file=$(grep '"pwd"' $config_file | cut -d'"' -f 4)
echo "Pwd file   : "$pwd_file

if [[ ! -z "${OCONF_PWD_FILE_CONTENTS}" ]]; then
  echo "Creating mqtt_pwd.txt from env."
  echo ${OCONF_PWD_FILE_CONTENTS} > $pwd_file
fi

for key in $(tail -n +2 config.json | head -n -1 | cut -d':' -f1 | sed 's/\"//g')
do
  conf_key=OCONF_`echo $key | tr '[:lower:]' '[:upper:]'`
  if [[ ! -z "${!conf_key}" ]]; then
    echo  "Replacing conf: "${conf_key}:${!conf_key}
    sed -i "s/\"$key\"\:.*/\"$key\"\:${!conf_key},/" $config_file
  fi 
done 

port=$(grep '"http_port"' $config_file | cut -d':' -f2 | sed 's/[^0-9]*//g')
echo "Starting on port "${port:-8000}
make migrate
python manage.py runserver 0.0.0.0:${port:-8000}
