import * as RuntimeMngr from '/runtime-mngr.js'

import { SIGNO } from '/signal.js'

import * as ARTSMessages from "/arts-msgs.js";

var log_panel;

function logPanelInit(element_id) {
    log_panel = document.getElementById(element_id);
}

function logPanelLog(message) {
  //console.log(message);
  if (message.length > 1)
    log_panel.innerHTML += logPanelLogEscapeHtml(message) + '<br/>';
  log_panel.scrollTop = log_panel.scrollHeight;
};

// Use the browser's built-in functionality to quickly and safely escape
// the string
function logPanelLogEscapeHtml(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}

logPanelInit('log_panel');

// get name
let namePrompt = "r1"

namePrompt = prompt(
  `Enter a name to identify your client\n`
);

logPanelLog("Hi " + namePrompt + ".");

RuntimeMngr.init({ onInitCallback: runtimeInitDone, name: namePrompt });

function runtimeInitDone() {
  console.log("Runtime init done.");

  let persistm = {
    object_id: "18881342-4111-488d-9301-064ad9b4d39b",
    type: "program",
    data: {
      name: "user1/program1",
      instantiate: "single",
      filename: "program1.wasm",
      filetype: "WA",
      affinity: "any",
      args: ["${scene} ${test1}"],
      env: [],
      channels: []
    }
  }
  RuntimeMngr.createModule(persistm);

/*
  setTimeout( function () {
    //let fn = "stdinread.wasm";
    //let fn = "counter.wasm";
    let fn = "arena_example.wasm";
    let mod_uuid = "44c72c87-c4ec-4759-b587-30ddc8590f6b";
    let rt_uuid = RuntimeMngr.info().uuid;
    let modCreateMsg = ARTSMessages.mod( {
      uuid: mod_uuid,
      parent: { uuid:  rt_uuid },
      filename: fn,
      channels: [{ path: "/ch/wasm-demo", type: "pubsub", mode: "rw", params: { topic: "realm/s/wasm-demo" }}]
    }, ARTSMessages.Action.create);
    // simulate the arrival of a module create message
    RuntimeMngr.directMessage(RuntimeMngr.info().ctl_topic + "/" + rt_uuid, modCreateMsg); 
  }, 500);  
*/
    /*    
    let fn = "cwlib_example.wasm";
    let mod_uuid = "44c72c87-c4ec-4759-b587-30ddc8590f6b";
    let rt_uuid = RuntimeMngr.runtime.uuid;
    let modCreateMsg = ARTSMessages.mod( {
      uuid: mod_uuid,
      parent: { uuid:  rt_uuid },
      filename: fn,
      channels: [{ path: "/ch/light", type: "pubsub", mode: "rw", params: { topic: "kitchen/light" }}]
    }, ARTSMessages.Action.create);
    // simulate the arrival of a module create message
    RuntimeMngr.mc.simulatePublish(RuntimeMngr.runtime.ctl_topic + "/" + rt_uuid, modCreateMsg); 
  }, 1000);  
*/
/*
  setTimeout( function () {
    let fn = "counter.wasm";
    let mod_uuid = "44c72c87-c4ec-4759-b587-30ddc8590f6c";
    let rt_uuid = RuntimeMngr.runtime.uuid;
    let modCreateMsg = ARTSMessages.mod( {
      uuid: mod_uuid,
      parent: { uuid:  rt_uuid },
      filename: fn
    }, ARTSMessages.Action.create);
    // simulate the arrival of a module create message
    RuntimeMngr.mc.simulatePublish(RuntimeMngr.runtime.ctl_topic + "/" + rt_uuid, modCreateMsg); 
  }, 2000);  
*/
/*
  setTimeout( function () {
    let mod_uuid = "44c72c87-c4ec-4759-b587-30ddc8590f6b";
    let rt_uuid = RuntimeMngr.runtime.uuid;
    let modDelMsg = ARTSMessages.mod( {
      uuid: mod_uuid,
      parent: { uuid:  rt_uuid },
    }, ARTSMessages.Action.delete);
    modDelMsg.send_to_runtime = rt_uuid;
    
    // simulate the arrival of a module del message
    RuntimeMngr.mc.simulatePublish(RuntimeMngr.runtime.ctl_topic + "/" + rt_uuid, modDelMsg); 
  }, 2000);  

  setTimeout( function () {
    RuntimeMngr.signal("44c72c87-c4ec-4759-b587-30ddc8590f6b", SIGNO.QUIT);
}, 5000);  
*/
}