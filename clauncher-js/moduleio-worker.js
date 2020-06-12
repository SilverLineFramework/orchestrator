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

    // object to store module info
    mod[modData.uuid] = { };

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

    // create circular buffer from previously created shared array buffer (for stdin)
    mod[modData.uuid].cb=[];
    mod[modData.uuid].cb[modData.stdin_topic] = new SharedArrayCircularBuffer(e.data.shared_array_buffer, modData.stdin_topic);

    // listen for messages on worker port
    mod[modData.uuid].worker_port = e.data.worker_port;
    
    // set event handler to receive messages from the worker; (when the module finishes)
    //mod[modData.uuid].worker_port.addEventListener('message', onmessage);
    mod[modData.uuid].worker_port.onmessage = onmessage;
    //this.worker_port.onmessage = onmessage;
    return;
  }

  if (e.data.type == WorkerMessages.msgType.pub_msg) {
    //console.log("publish:", e.data.msg, "->", e.data.dst);
    let modUuid = e.data.mod_uuid;
    if (mod[modUuid] === undefined) return; // TODO: save messages sent after signal 
    mod[modUuid].mc.publish(e.data.dst, e.data.msg);
    return;
  }
  if (e.data.type == WorkerMessages.msgType.new_stream) {

    let modUuid = e.data.mod_uuid;
        
    if (e.data.channel.type === "pubsub") {

      // create circular buffer from previously created shared array buffer
      mod[modUuid].cb[e.data.channel.params.topic] = new SharedArrayCircularBuffer(e.data.shared_array_buffer, e.data.path+'/data');

      // subscribe to topic
      mod[modUuid].mc.subscribe(e.data.channel.params.topic);
    } else if (e.data.channel.type === "signalfd") {

      // create circular buffer from previously created shared array buffer
      mod[modUuid].cb["signalfd"] = new SharedArrayCircularBuffer(e.data.shared_array_buffer, "signalfd");
      
    } else {
      // todo
      console.log(e.data.channel.type, ": Channel type not implemented.")
    }

    return;
  }

  if (e.data.type == WorkerMessages.msgType.signal) {
    let modUuid = e.data.mod_uuid;

    console.log("sending signal");
    // signalfd_siginfo struct is 128 bytes
    let bytes = new Uint8Array(128);
    bytes[0] = e.data.signo; // set the first byte (ssi_signo) indicating the signal number

    if (mod[modUuid].cb["signalfd"] === undefined) {
      console.log("WASM module must open signalfd.");
      return;
    }
    mod[modUuid].cb["signalfd"].push(bytes);
  
    // disconnect mqtt client
    mod[modUuid].mc.disconnect();

    // free data about this module
    delete mod[modUuid];

    return;
  }

};

function onMqttMessage(modUuid, message) {
  //console.log ("IO worker received: " + message.payloadString , message.destinationName);

  // convert received message to a byte array and push to shared buffer
  let bytes = new TextEncoder().encode(message.payloadString + "\n");
  mod[modUuid].cb[message.destinationName].push(bytes);
}