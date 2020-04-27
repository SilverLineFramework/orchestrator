#!/bin/bash

# assumes the env variables are given:
# ${mqtt_srv}
# ${filename}
# ${fid}
# ${pipe_stdin_stdout}
# ${sub_topic}
# ${pub_topic}
# ${args}
# ${done_topic}
# ${done_msg}

python3=/usr/local/bin/python3 
pip=/usr/local/bin/pip3
wget=/usr/local/bin/wget
mosquitto_pub=/usr/local/bin/mosquitto_pub
mosquitto_sub=/usr/local/bin/mosquitto_sub
work_dir=`mktemp -d`

cd ${work_dir}
${wget} --no-check-certificate "https://docs.google.com/uc?export=download&id=${fid}" -O ${filename}
fn=$(basename -- "${work_dir}/${filename}")
ext="${fn##*.}"
fn="${fn%.*}"

test -d venv || virtualenv venv
. venv/bin/activate

if [ "$ext" = "zip" ]; then
    unzip ${work_dir}/${filename}
    ${pip} install -Ur requirements.txt
fi

if [ "${pipe_stdin_stdout}" = "True" ]; then
     echo "Running: ${mosquitto_sub} -h ${mqtt_srv} -t ${sub_topic} | ${python3} -u ${fn}.py ${args} | ${mosquitto_pub} -h ${mqtt_srv} -t ${pub_topic} -l"
     ${mosquitto_sub} -h ${mqtt_srv} -t ${sub_topic} | { ${python3} -u ${fn}.py ${args}; pkill -g 0; } | ${mosquitto_pub} -h ${mqtt_srv} -t ${pub_topic} -l
    # echo "Running: ${python3} -u ${fn}.py ${args} | ${mosquitto_pub} -h ${mqtt_srv} -t ${pub_topic} -l"
    # { ${python3} -u ${fn}.py ${args}; pkill -g 0; } | ${mosquitto_pub} -h ${mqtt_srv} -t ${pub_topic} -l
else
    echo "Running: ${python3} ${fn}.py"
    ${python3} ${fn}.py
fi

echo "Module done. -t ${done_topic} -m ${done_msg}"

${mosquitto_pub} -h ${mqtt_srv} -t ${done_topic} -m "${done_msg}"

touch venv/bin/activate