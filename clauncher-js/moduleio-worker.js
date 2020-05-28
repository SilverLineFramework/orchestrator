/**
 * @fileoverview Worker to publish (stdin/stderr) to mqtt topics and writes messages received on stdin topic to a shared buffer
 *
 * We start an mqtt client per module so that each module is visible to the mqtt server
 *
 * Copyright (C) Wiselab CMU.
 * @date April, 2020
 */
import MqttClient from "/mqtt-client.js";
import * as WorkerMessages from "/worker-msgs.js";
import * as ARTSMessages from "/arts-msgs.js";
import SharedArrayCircularBuffer from "/sa-cbuffer.js";

const stdin_topic_prefix = "realm/proc/debug/stdin/";

// dictionary of shared buffers
var cb = [];

// dictionary of mqtt clients
var mc = [];

// dictionary with info about the modules
var mod = [];

onmessage = async function (e) {
  if (e.data.type == WorkerMessages.msgType.start) {
    let modData = e.data.arts_mod_instance_data;

    // save the shared buffer instance
    mod[modData.uuid] = { cb: e.data.shared_cb };

    // start mqtt client and subscribe to stdin topic
    // (one per module; this way the server can distinguish the module traffic)
    mod[modData.uuid].mc = new MqttClient({
      clientid: modData.uuid, // mqtt client id is the module uuid
      willMessageTopic: modData.reg_topic,
      willMessage: JSON.stringify(ARTSMessages.mod(modData, ARTSMessages.Action.delete)),
      subscribeTopics: [modData.stdin_topic], // subscribe to stdin topic
      onMessageCallback: onMqttMessage.bind(null, modData.uuid),
      dbg: false,
    });

    await mod[modData.uuid].mc.connect();

    //console.log(modData);
    
    // create circular buffer from previously created shared array buffer (for stdin)
    mod[modData.uuid].cb=[];
    mod[modData.uuid].cb[modData.stdin_topic] = new SharedArrayCircularBuffer(e.data.shared_array_buffer, modData.stdin_topic);

    // listen for messages on worker port
    e.data.worker_port.onmessage = onmessage;

    return;
  }

  if (e.data.type == WorkerMessages.msgType.pub_msg) {
    //console.log("publish:", e.data.msg, "->", e.data.dst);
    let modUuid = e.data.mod_uuid;
    mod[modUuid].mc.publish(e.data.dst, e.data.msg);
    return;
  }
  
  if (e.data.type == WorkerMessages.msgType.new_iostream) {
    console.log(e.data)
    
    if (e.data.ch.type == "pubsub") {
      let modUuid = e.data.mod_uuid;

      // create circular buffer from previously created shared array buffer
      mod[modUuid].cb[e.data.ch.params.topic] = new SharedArrayCircularBuffer(e.data.shared_array_buffer, e.data.path+'/data');

      // subscribe to topic
      mod[modUuid].mc.subscribe(e.data.ch.params.topic);
    } else {
      // todo
      console.log(e.data.ch.type, ": Channel type not implemented.")
    }

    return;
  }
  
};

function onMqttMessage(modUuid, message) {
  //console.log ("IO worker received: " + message.payloadString );

  // message to module stdin
  //if (message.destinationName.startsWith(stdin_topic_prefix) == false)

  // convert received message to a byte array and push to shared buffer
  let bytes = new TextEncoder().encode(message.payloadString + "\n");
  mod[modUuid].cb[message.destinationName].push(bytes);
}