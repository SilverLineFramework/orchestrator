/**
 * @fileoverview Register the browser runtime and launch WASM modules in a separate worker
 *
 * Copyright (C) Wiselab CMU.
 * @date April, 2020
 */
import { v4 as uuidv4 } from "uuid"; // https://www.npmjs.com/package/uuidjs
import * as QueryString from "query-string";

import MqttClient from "/mqtt-client.js";
import * as ARTSMessages from "/arts-msgs.js";
import * as WorkerMessages from "/worker-msgs.js";
import SharedArrayCircularBuffer from "/sa-cbuffer.js";
import { SIGNO } from "/signal.js";

var runtime;
var mc;
var ioworker;

const dft_realm = "realm";
const dft_reg_topic = "proc/reg";
const dft_ctl_topic = "proc/control";
const dft_dbg_topic = "proc/debug";
const dft_apis = ["wasi:unstable"];
const dft_store_location = "/store/users/";

export async function init(settings) {
  // handle default settings
  settings = settings || {};

  let rrealm = settings.realm !== undefined ? settings.realm : dft_realm;
  let ruuid = settings.uuid !== undefined ? settings.uuid : uuidv4();
  runtime = {
    realm: rrealm,
    uuid: ruuid,
    name:
      settings.name !== undefined > 1
        ? settings.name
        : "rt-" + Math.round(Math.random() * 10000) + "@" + navigator.product,
    max_nmodules:
      settings.max_nmodules !== undefined ? settings.max_nmodules : 1,
    apis: settings.apis !== undefined ? settings.apis : dft_apis,
    reg_topic:
      settings.reg_topic !== undefined
        ? settings.reg_topic
        : rrealm + "/" + dft_reg_topic,
    ctl_topic:
      settings.ctl_topic !== undefined
        ? settings.ctl_topic
        : rrealm + "/" + dft_ctl_topic + "/" + ruuid + "/#",
    dbg_topic:
      settings.dbg_topic !== undefined
        ? settings.dbg_topic
        : rrealm + "/" + dft_dbg_topic,
    arts_ctl_topic:
      settings.arts_ctl_topic !== undefined
        ? settings.arts_ctl_topic
        : rrealm + "/" + dft_ctl_topic, // arts messages sent here
    reg_timeout_seconds:
      settings.reg_timeout_seconds !== undefined
        ? settings.reg_timeout_seconds
        : 5,
    mqtt_uri: settings.mqtt_uri,
    onInitCallback: settings.onInitCallback,
    modules: [],
    client_modules: [],
    filestore_location:
      settings.filestore_location != undefined
        ? settings.filestore_location
        : dft_store_location,
    dbg: settings.dbg !== undefined ? settings.dbg : false,
  };

  console.log(runtime);
  runtime.isRegistered = false;

  // create last will message
  let lastWill = JSON.stringify(
    ARTSMessages.rt(runtime, ARTSMessages.Action.delete)
  );

  // on unload, send delete client modules requests
  window.onbeforeunload = function() {
    runtime.client_modules.forEach(mod => {
      let modDelMsg = ARTSMessages.mod(mod, ARTSMessages.Action.delete);      
      mc.publish(runtime.arts_ctl_topic, modDelMsg);
    });
  };

  // start mqtt client
  mc = new MqttClient({
    uri: runtime.mqtt_uri,
    clientid: runtime.uuid, // mqtt client id is the runtime uuid
    willMessageTopic: runtime.reg_topic,
    willMessage: lastWill,
    subscribeTopics: [runtime.reg_topic], // subscribe to reg topic
    onMessageCallback: onMqttMessage,
    dbg: runtime.dbg,
  });

  // connect
  try {
    await mc.connect();
  } catch (error) {
    console.log(error); // Failure!
    return;
  }
  // subscribe to **all** debug messages; for debug/viz purposes only
  //mc.subscribe(runtime.dbg_topic + "/#");

  // register runtime in ARTS
  registerRuntime();

  // create the module io worker
  ioworker = new Worker("moduleio-worker.js");
}

// get runtime settings
export function info() {
  return runtime;
}

// send a signal to local module
export function signal(modUuid, signo) {
  ioworker.postMessage({
    type: WorkerMessages.msgType.signal,
    mod_uuid: modUuid,
    signo: signo,
  });
}

// create module from persist object
// will create a module in this runtime or send request message to ARTS
export function createModule(persist_mod) {
  let pdata = persist_mod.data;

  // function to replace variables
  function replaceVars(text, rvars) {
    let result;
    for (const [key, value] of Object.entries(rvars)) {
      if (value !== undefined) {
        let re = new RegExp("\\$\\{" + key + "\\}", "g");
        result = text.replace(re, value);
        text = result;
      }
    }
    return result;
  }


  // get mqtt host from globals
  let mqtthost = window.globals ? window.globals.mqttParamZ : undefined;
  if (mqtthost) { 
    // remove port, scheme and path it exist
    let n = mqtthost.lastIndexOf(":");
    if (mqtthost.lastIndexOf(":") > -1) { 
      mqtthost = mqtthost.substring(0, n);    
    }
    mqtthost.replace("wss://", "");
    mqtthost.replace("ws://", "");
    mqtthost.replace("/mqtt/", "");
    mqtthost.replace("/mqtt", "");
  }

  // get query string
  let qstring = QueryString.parse(location.search);

  // variables we replace 
  let rvars = {
    scene: window.globals ? window.globals.renderParam : qstring["scene"],
    mqtth: mqtthost,
    cameraid: window.globals ? window.globals.camName : undefined,
    username: window.globals ? window.globals.userParam : qstring["name"],
    runtimeid: runtime.uuid,
    ...qstring, // add all url params
  };

  // convert args and env to strings and replace variables
  let args, env;
  if (pdata.args) args = replaceVars(pdata.args.join(" "), rvars);
  if (pdata.env) env = replaceVars(pdata.env.join(" "), rvars);

  // replace variables in channel path and params
  if (pdata.channels) {
    for (let i = 0; i < pdata.channels.length; i++) {
      pdata.channels[i].path = replaceVars(pdata.channels[i].path, rvars);
      pdata.channels[i].params.topic = replaceVars(pdata.channels[i].params.topic, rvars);
    }
  }

  let muuid = undefined;
  // check instantiate (single/per 'client')
  if (pdata.instantiate == "single") {
    // object_id in persist obj is used as the uuid, if it is a valid uuid
    let uuid_regex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-5][0-9a-f]{3}-[089ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    if (uuid_regex.test(persist_mod.object_id)) muuid = persist_mod.object_id;
    else {
      console.log(
        "Error! Object id must be a valid uuid (for instantiate=single)!"
      );
    }
  } // for per client, let ARTSMessages.mod() create a random uuid;

  let fn;
  if (pdata.filetype == 'WA') {
    // full filename using file store location, name (in the form namespace/program-folder), entry filename
    fn = [runtime.filestore_location, pdata.name, pdata.filename]
      .join("/")
      .replace(/([^:])(\/\/+)/g, "$1/");
  } else fn = pdata.filename; // just the filename

  // create new ARTS message using persist obj data
  let modCreateMsg = ARTSMessages.mod(
    {
      name: pdata.name,
      uuid: muuid,
      parent: pdata.affinity == "client" ? { uuid: runtime.uuid } : undefined, // parent is this runtime if affinity is client; otherwise, undefined to let ARTS decide
      filename: fn,
      filetype: pdata.filetype,
      channels: pdata.channels,
      env: env,
      args: args,
    },
    ARTSMessages.Action.create
  );

  // check affinity
  if (pdata.affinity == "single") {
    // object_id in persist obj is used as the uuid, if it is a valid uuid
    let regex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-5][0-9a-f]{3}-[089ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    if (regex.test(persist_mod.object_id))
      modCreateMsg.data.uuid = persist_mod.object_id;
    else console.log("Error! Object id must be a valid uuid!");
  } // nothing to do for multiple; a random uuid is created in ARTSMessages.mod(undefined, ARTSMessages.Action.create);

  // if instanciate 'per client', save this module uuid to delete before exit
  if (pdata.instantiate == "client") {
    console.log("Saving:", modCreateMsg.data);
    runtime.client_modules.push(modCreateMsg.data);

  }

  // TODO: save pending req uuid and check arts responses
  // NOTE: object_id of arts messages are used as a transaction id
  // runtime.pending_req.push(modCreateMsg.object_id); // pending_req is a list with object_id of requests waiting arts response

  console.log(modCreateMsg);
  mc.publish(runtime.arts_ctl_topic, modCreateMsg);
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
    console.log("[" + message.destinationName + "] " + message.payloadString);
    return;
  }

  try {
    var msg = JSON.parse(message.payloadString);
  } catch (err) {
    console.log(
      "Could not parse message: [" + message.destinationName + "==" + +"]",
      message.payloadString,
      err
    );
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
        console.log("Error registering runtime:" + msg.data);
        return;
      }

      runtime.isRegistered = true;

      // unsubscribe from reg topic and subscribe to ctl/runtime_uuid
      mc.unsubscribe(runtime.reg_topic);
      mc.subscribe(runtime.ctl_topic);

      // runtime registered; signal init is done and ready to roll
      if (runtime.onInitCallback != undefined) runtime.onInitCallback();

      return;
    }
  }

  // below, only handle module requests
  if (msg.type != ARTSMessages.Type.req || msg.data.type != ARTSMessages.ObjType.mod) {
    console.log("Not an valid ARTS request. Ignoring.")
    return;
  }

  // module create request
  if (msg.action === ARTSMessages.Action.create) {
    let mod = runtime.modules[msg.data.uuid];

    // if this is a module we have not heard about, we need to do some additional stuff
    if (mod === undefined) {
      mod = msg.data;

      // also return if filetype is not WASM
      if (mod.filetype !== 'WA') {
        console.log("Received module request for filetype not supported.")
        return;
      }

      // save module data
      runtime.modules[mod.uuid] = mod;

      // add topics where the module
      mod.reg_topic = runtime.reg_topic; // runtime's reg topic; used to send module delete msg
      mod.stdin_topic = runtime.dbg_topic + "/stdin/" + mod.uuid; // under runtime's dbg topic
      mod.stdout_topic = runtime.dbg_topic + "/stdout/" + mod.uuid; // under runtime's dbg topic

      // create a shared buffer to be used by both workers as a circular buffer
      mod.sb = SharedArrayCircularBuffer.createSharedBuffer();

      // create a (js worker) channel for the workers to talk
      mod.channel = new MessageChannel();

      // start an mqtt client for the module io (in moduleio worker); tranfer ownership of the port
      ioworker.postMessage(
        {
          type: WorkerMessages.msgType.start,
          arts_mod_instance_data: {
            uuid: mod.uuid,
            reg_topic: mod.reg_topic,
            stdin_topic: mod.stdin_topic,
          }, // module object with only needed data
          worker_port: mod.channel.port2,
          shared_array_buffer: mod.sb,
        },
        [mod.channel.port2]
      );
    }

    // wait_state indicated? we will wait for another create message with the state to start the module then
    if (msg.data.wait_state == true) return;

    // start a worker to run the wasm module
    let mworker = new Worker("module-worker.js");

    console.log(msg);
    if (msg.migratetx_start)
      console.log(
        "|T: Migration - State Publish to Module Startup:",
        Date.now() - msg.migratetx_start,
        "ms"
      ); // TMP: assumes module is migrating in the same machine/in synched machines

    // post start message to worker
    mworker.postMessage(
      {
        type: WorkerMessages.msgType.start,
        arts_mod_instance_data: {
          uuid: mod.uuid,
          filename: mod.filename,
          stdin_topic: mod.stdin_topic,
          stdout_topic: mod.stdout_topic,
          env: mod.env,
          args: mod.args,
          channels: mod.channels,
        }, // module object with only needed data
        worker_port: mod.channel.port1,
        shared_array_buffer: mod.sb,
        wait_state: msg.data.wait_state,
        memory: msg.data.memory,
      },
      [mod.channel.port1]
    );

    // set event handler to receive messages from the worker; (when the module finishes)
    mworker.addEventListener("message", onWorkerMessage);

    // save worker
    runtime.modules[mod.uuid].mworker = mworker;

    // subscribe to debug messages from the module; for debug/viz purposes only
    mc.subscribe(runtime.dbg_topic + "/stdout/" + mod.uuid);

    return;
  }

  // module delete request
  if (msg.action === ARTSMessages.Action.delete) {
    // save send_to_runtime
    runtime.modules[msg.data.uuid].send_to_runtime = msg.send_to_runtime;

    runtime.modules[msg.data.uuid].del_start = Date.now(); // TMP

    console.log("Posting kill to module uuid", msg.data.uuid);
    // send signal to module through moduleio; worker will send message back when done (handled by onWorkerMessage)
    ioworker.postMessage({
      type: WorkerMessages.msgType.signal,
      mod_uuid: msg.data.uuid,
      signo: SIGNO.QUIT,
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

  if (mod.send_to_runtime === undefined) return;

  // module create msg
  let modCreateMsg = ARTSMessages.mod(mod, ARTSMessages.Action.create);
  modCreateMsg.data.memory = e.data.memory;

  modCreateMsg.migratetx_start = Date.now(); // TMP

  console.log(
    "|T: Module Terminate/Serialize/Post State:",
    Date.now() - mod.del_start,
    "ms"
  ); // TMP

  // send module create msg
  if (mod.send_to_runtime !== runtime.uuid) {
    console.time("|T: Publish (part of State Publish)");
    mc.publish(
      dft_ctl_topic + "/" + mod.send_to_runtime,
      JSON.stringify(modCreateMsg)
    );
    console.timeEnd("|T: Publish (part of State Publish)");
  } else {
    // move to self ? allow for now... (useful for testing)
    handleARTSMsg(modCreateMsg);
  }
}
