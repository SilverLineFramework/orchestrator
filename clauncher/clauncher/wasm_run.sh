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

wasmrt=/usr/local/bin/wasmer 
wget=/usr/local/bin/wget
mosquitto_pub=/usr/local/bin/mosquitto_pub
mosquitto_sub=/usr/local/bin/mosquitto_sub

work_dir=`mktemp -d`

cd ${work_dir}
${wget} --no-check-certificate "https://docs.google.com/uc?export=download&id=${fid}" -O ${filename}
fn=$(basename -- "${work_dir}/${filename}")
ext="${fn##*.}"
fn="${fn%.*}"

if [ "${pipe_stdin_stdout}" = "True" ]; then
    echo "Running: ${wasmrt} ${filename} | ${pub_topic}"
    ${wasmrt} ${filename} | ${mosquitto_pub} -h o${mqtt_srv} -t ${pub_topic} -l
else
    echo "Running: ${wasmrt} ${filename} "
    ${wasmrt} ${filename}
fi

echo "Module done."
${mosquitto_pub} -h ${mqtt_srv} -t ${done_topic} -m ${done_msg}