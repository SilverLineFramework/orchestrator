import * as RuntimeMngr from '/runtime-mngr.js'
import * as LogPanel from '/log-panel.js'

import { SIGNO } from '/signal.js'

import * as ARTSMessages from "/arts-msgs.js";

LogPanel.init('log_panel');

// get name
let namePrompt = "r1"

namePrompt = prompt(
  `Enter a name to identify your client\n`
);

LogPanel.log("Hi " + namePrompt + ".");

RuntimeMngr.init({ onInitCallback: runtimeInitDone, name: namePrompt });

function runtimeInitDone() {
  console.log("Runtime init done.");
/*
  setTimeout( function () {
    //let fn = "stdinread.wasm";
    //let fn = "counter.wasm";
    let fn = "arena_example.wasm";
    let mod_uuid = "44c72c87-c4ec-4759-b587-30ddc8590f6b";
    let rt_uuid = RuntimeMngr.runtime.uuid;
    let modCreateMsg = ARTSMessages.mod( {
      uuid: mod_uuid,
      parent: { uuid:  rt_uuid },
      filename: fn,
      channels: [{ path: "/ch/wasm-demo", type: "pubsub", mode: "rw", params: { topic: "realm/s/wasm-demo" }}]
    }, ARTSMessages.Action.create);
    // simulate the arrival of a module create message
    RuntimeMngr.mc.simulatePublish(RuntimeMngr.runtime.ctl_topic + "/" + rt_uuid, modCreateMsg); 
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