/**
 * @fileoverview Register the browser runtime and launch WASM modules in a separate worker
 *
 * Copyright (C) Wiselab CMU.
 * @date April, 2020
 */
import { v4 as uuidv4 } from "uuid"; // https://www.npmjs.com/package/uuidjs
import MqttClient from "/mqtt-client.js";

import * as ARTSMessages from "/arts-msgs.js";
import * as WorkerMessages from "/worker-msgs.js";
import SharedArrayCircularBuffer from "/sa-cbuffer.js";
import { SIGNO } from '/signal.js'

import * as LogPanel from "/log-panel.js";

export var runtime;
export var mc;
var ioworker;

const dft_reg_topic = "realm/proc/reg";
const dft_ctl_topic = "realm/proc/control";
const dft_dbg_topic = "realm/proc/debug";

export async function init(settings) {
  // handle default settings
  settings = settings || {};
  runtime = {
    uuid: settings.uuid !== undefined ? settings.uuid : uuidv4(),
    name: settings.name.length > 1 ? settings.name : "rt-" + Math.round(Math.random() * 10000) + "@" + navigator.product,
    max_nmodules: settings.max_nmodules !== undefined ? settings.max_nmodules : 1,
    apis: settings.apis !== undefined ? settings.apis : ["wasi:unstable"],
    reg_topic: settings.reg_topic !== undefined ? settings.reg_topic : dft_reg_topic,
    ctl_topic: settings.ctl_topic !== undefined ? settings.ctl_topic : dft_ctl_topic,
    dbg_topic: settings.dbg_topic !== undefined ? settings.dbg_topic : dft_dbg_topic,
    reg_timeout_seconds: settings.reg_timeout_seconds !== undefined ? settings.reg_timeout_seconds : 5,
    onInitCallback: settings.onInitCallback,
    modules: [],
  };

  runtime.isRegistered = false;

  // create last will message
  let lastWill =  JSON.stringify(ARTSMessages.rt(runtime, ARTSMessages.Action.delete));

  // start mqtt client
  mc = new MqttClient({
    clientid: runtime.uuid, // mqtt client id is the runtime uuid
    willMessageTopic: runtime.reg_topic,
    willMessage: lastWill,
    subscribeTopics: [runtime.reg_topic], // subscribe to reg topic
    onMessageCallback: onMqttMessage,
  });

  // connect
  await mc.connect();

  // subscribe to **all** debug messages; for debug/viz purposes only
  //mc.subscribe(runtime.dbg_topic + "/#");

  // register runtime in ARTS
  registerRuntime(); 

  // create the module io worker
  ioworker = new Worker("moduleio-worker.js");

  if (runtime.onInitCallback != undefined) runtime.onInitCallback();
}

export function signal(modUuid, signo) {
    ioworker.postMessage(
    {
        type: WorkerMessages.msgType.signal,
        mod_uuid: modUuid,
        signo: signo
    });
}

// register runtime
function registerRuntime() {
  if (runtime.isRegistered == true) return;

  var reg_msg = ARTSMessages.rt(runtime, ARTSMessages.Action.create);
  runtime.reg_uuid = reg_msg.object_id; // save message uuid for confirmation

  mc.publish(runtime.reg_topic, JSON.stringify(reg_msg));

  setTimeout(registerRuntime, runtime.reg_timeout_seconds * 1000); // try register again
}

// callback from mqttclient; on reception of message
function onMqttMessage(message) {

  // output module stdout; for debug/viz purposes (in init we subscribed to runtime.dbg_topic/#)
  if (message.destinationName.startsWith(runtime.dbg_topic + "/stdout/")) {
    LogPanel.log("[" + message.destinationName + "] " + message.payloadString);
    return;
  }


  try {
    var msg = JSON.parse(message.payloadString);
  } catch (err) {
    console.log("Could not parse message:", message.payloadString, err);
    return;
  }

  handleARTSMsg(msg);
}

// handle arts messages
function handleARTSMsg(msg) {

  // response from ARTS
  if (msg.type === ARTSMessages.Type.resp) {

    // response to reg request
    if (msg.object_id == runtime.reg_uuid) {

      // check if result was ok
      if (msg.data.result != ARTSMessages.Result.ok) {
        LogPanel.log(
          "Error registering runtime:" + msg.data
        );
        return;
      }
  
      runtime.isRegistered = true;

      // unsubscribe from reg topic and subscribe to ctl/runtime_uuid
      mc.unsubscribe(runtime.reg_topic);
      runtime.ctl_topic += "/" + runtime.uuid + "/#";
      mc.subscribe(runtime.ctl_topic);
  
      return;
  
    }

  }

  // below, only handle module requests
  if (msg.type != ARTSMessages.Type.req || msg.data.type != ARTSMessages.ObjType.mod) return;

  // module create request
  if (msg.action === ARTSMessages.Action.create) {

    let mod = runtime.modules[msg.data.uuid];

    // if this is a module we have not heard about, we need to do some additional stuff
    if (mod === undefined) {
      mod = msg.data;

      // save module data
      runtime.modules[mod.uuid] = mod;

      // add topics where the module
      mod.reg_topic = runtime.reg_topic; // runtime's reg topic; used to send module delete msg
      mod.stdin_topic =
        runtime.dbg_topic + "/stdin/" + mod.uuid; // under runtime's dbg topic
      mod.stdout_topic =
        runtime.dbg_topic + "/stdout/" + mod.uuid; // under runtime's dbg topic

      // create a shared buffer to be used by both workers as a circular buffer
      mod.sb = SharedArrayCircularBuffer.createSharedBuffer();

      // create a (js worker) channel for the workers to talk
      mod.channel = new MessageChannel();

      // start an mqtt client for the module io (in moduleio worker); tranfer ownership of the port
      ioworker.postMessage(
        {
            type: WorkerMessages.msgType.start,
            arts_mod_instance_data: {uuid: mod.uuid, reg_topic: mod.reg_topic, stdin_topic: mod.stdin_topic}, // module object with only needed data
            worker_port: mod.channel.port2,
            shared_array_buffer: mod.sb,
        },[mod.channel.port2]); 
    } 
    
    // wait_state indicated? we will wait for another create message with the state to start the module then
    if (msg.data.wait_state == true) return;

    // start a worker to run the wasm module
    let mworker = new Worker("module-worker.js");

    // post start message to worker
    mworker.postMessage(
    {
        type: WorkerMessages.msgType.start,
        arts_mod_instance_data: {uuid: mod.uuid, filename: mod.filename, stdin_topic: mod.stdin_topic, stdout_topic: mod.stdout_topic, channels: mod.channels}, // module object with only needed data
        worker_port: mod.channel.port1,
        shared_array_buffer: mod.sb,
        wait_state: msg.data.wait_state,
        memory: msg.data.memory,
    }, [mod.channel.port1]); 

    // set event handler to receive messages from the worker; (when the module finishes)
    mworker.addEventListener('message', onWorkerMessage);

    // save worker
    runtime.modules[mod.uuid].mworker = mworker;

    // subscribe to debug messages from the module; for debug/viz purposes only
    mc.subscribe(runtime.dbg_topic + "/stdout/" + mod.uuid);

    return;
  }

  console.log(msg);

  // module delete request
  if (msg.action === ARTSMessages.Action.delete) {
    console.log("here");
    // save send_to_runtime
    runtime.modules[msg.data.uuid].send_to_runtime = msg.send_to_runtime;

    console.time("Module Terminate/Serialize");    
    console.log("Posting kill to module uuid",  msg.data.uuid);
    // send signal to module through moduleio; worker will send message back when done (handled by onWorkerMessage)
    ioworker.postMessage(
      {
          type: WorkerMessages.msgType.signal,
          mod_uuid: msg.data.uuid,
          signo: SIGNO.QUIT
      });
  }
}

// on reception of message from module worker
function onWorkerMessage(e) {
  console.log("Module done:", e.data);

  // expect a module finish message
  if (e.data.type != WorkerMessages.msgType.finish) return;

  let mod = runtime.modules[e.data.mod_uuid];

  if (mod === undefined) {
    console.log("Could not find module.");
    return;
  }

  mc.unsubscribe(runtime.dbg_topic + "/stdout/" + mod.uuid);

  // terminate the worker
  mod.mworker.terminate();

  // clear module data
  delete runtime.modules[e.data.mod_uuid];

  //mod.send_to_runtime = runtime.uuid; // TMP
  if (mod.send_to_runtime === undefined) return;

  // module create msg
  let modCreateMsg = ARTSMessages.mod(mod, ARTSMessages.Action.create);
  modCreateMsg.data.memory = e.data.memory;
  
  // send module create msg
  if (mod.send_to_runtime !== runtime.uuid) {
    console.time("Publish"); 
    mc.publish(dft_ctl_topic + "/" + mod.send_to_runtime, JSON.stringify(modCreateMsg));    
    console.timeEnd("Publish"); 
  } else {
    // move to self ? allow for now... (useful for testing) 
    handleARTSMsg(modCreateMsg);
  }

  console.timeEnd("Module Terminate/Serialize");   
}
