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
import * as LogPanel from "/log-panel.js";
import SharedArrayCircularBuffer from "/sa-cbuffer.js";

var runtime;
export var mc;
var ioworker;

export async function init(settings) {
  // handle default settings
  settings = settings || {};
  runtime = {
    uuid: settings.uuid !== undefined ? settings.uuid : uuidv4(),
    name: settings.name !== undefined ? "rt-" + Math.round(Math.random() * 10000) + "@" + navigator.product + "-" + settings.name: "rt-" + Math.round(Math.random() * 10000) + "@" + navigator.product,
    max_nmodules: settings.max_nmodules !== undefined ? settings.max_nmodules : 1,
    apis: settings.apis !== undefined ? settings.apis : ["wasi:unstable"],
    reg_topic: settings.reg_topic !== undefined ? settings.reg_topic : "realm/proc/reg",
    ctl_topic: settings.ctl_topic !== undefined ? settings.ctl_topic : "realm/proc/control",
    dbg_topic: settings.dbg_topic !== undefined ? settings.dbg_topic : "realm/proc/debug",
    reg_timeout_seconds: settings.reg_timeout_seconds !== undefined ? settings.reg_timeout_seconds : 5,
    onInitCallback: settings.onInitCallback,
    modules: [],
  };

  runtime.isRegistered = false;

  // start mqtt client
  mc = new MqttClient({
    clientid: runtime.uuid, // mqtt client id is the runtime uuid
    willMessageTopic: runtime.reg_topic,
    willMessage: JSON.stringify(
      ARTSMessages.rt(runtime, ARTSMessages.Action.delete)
    ),
    subscribeTopics: [runtime.reg_topic], // subscribe to reg topic
    //onConnectCallback: registerRuntime, // ask for callback after connect
    onMessageCallback: onMqttMessage,
  });

  // connect
  await mc.connect();

  mc.subscribe(runtime.dbg_topic + "/#");
  //registerRuntime(); // TMP: do not register

  // create the module io worker
  ioworker = new Worker("moduleio-worker.js");

  if (runtime.onInitCallback != undefined) runtime.onInitCallback();
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
  // reg
  if (message.destinationName.startsWith(runtime.reg_topic)) {
    var msg_reg = JSON.parse(message.payloadString);

    if (msg_reg.type != ARTSMessages.Type.resp) return; // silently return if type is not arts_resp!

    if (msg_reg.object_id != runtime.reg_uuid) return; // we only look at messages to confirm our registration

    // check if result was ok
    if (msg_reg.data.result != ARTSMessages.Result.ok) {
      LogPanel.log(
        "Error registering runtime; details:" + msg_reg.data.details
      );
      return;
    }

    runtime.isRegistered = true;

    LogPanel.log("** Runtime registered.");

    // unsubscribe from reg topic and subscribe to ctl/runtime_uuid
    mc.unsubscribe(runtime.reg_topic);
    runtime.ctl_topic += "/" + runtime.uuid;
    mc.subscribe(runtime.ctl_topic);
    mc.subscribe(runtime.dbg_topic + "/#");

    return;
  }

  // ctl
  if (message.destinationName.startsWith(runtime.ctl_topic)) {
    var msg_ctl = JSON.parse(message.payloadString);
    console.log(msg_ctl);
    if (msg_ctl.type != ARTSMessages.Type.resp) {
      if (msg_ctl.action == ARTSMessages.Action.create) {
        var rcvModInstance = msg_ctl.data.details;
      }

      runtime.modules[rcvModInstance.uuid] = rcvModInstance;
      //console.log(rcvModInstance);

      // add topics where the module
      rcvModInstance.reg_topic = runtime.reg_topic; // runtime's reg topic; used to send module delete msg
      rcvModInstance.stdin_topic =
        runtime.dbg_topic + "/stdin/" + rcvModInstance.uuid; // under runtime's dbg topic
      rcvModInstance.stdout_topic =
        runtime.dbg_topic + "/stdout/" + rcvModInstance.uuid; // under runtime's dbg topic
      rcvModInstance.ctl_topic =
      runtime.ctl_topic + "/" + rcvModInstance.uuid; // under runtime's dbg topic

      // create a shared buffer to be used by both workers as a circular buffer
      let sb = SharedArrayCircularBuffer.createSharedBuffer();

      // create module worker
      let mworker = new Worker("module-worker.js");

      // create a channel for the workers to talk
      const channel = new MessageChannel();

      // send message to workers; tranfer ownership of the respective ports

      // start the wasm module
      mworker.postMessage(
      {
          type: WorkerMessages.msgType.start,
          arts_mod_instance_data: rcvModInstance,
          worker_port: channel.port1,
          shared_array_buffer: sb,
      }, [channel.port1]); 

      // start an mqtt client for the module std io
      ioworker.postMessage(
      {
          type: WorkerMessages.msgType.start,
          arts_mod_instance_data: rcvModInstance,
          worker_port: channel.port2,
          shared_array_buffer: sb,
      },[channel.port2]); 
    }
  }

  // module stdout
  if (message.destinationName.startsWith(runtime.dbg_topic + "/stdout/")) {
    LogPanel.log("[" + message.destinationName + "] " + message.payloadString);
  }
}
