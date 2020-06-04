import * as RuntimeMngr from '/runtime-mngr.js'
import * as LogPanel from '/log-panel.js'

import { SIGNO } from '/signal.js'

import * as ARTSMessages from "/arts-msgs.js";

LogPanel.init('log_panel');

// get name
let namePrompt = ""
//namePrompt = prompt(
//  `Enter a name to identify your client\n`
//);

LogPanel.log("Hi " + namePrompt + ".");

RuntimeMngr.init({ onInitCallback: runtimeInitDone, name: namePrompt });

function runtimeInitDone() {
  console.log("Runtime init done.");

  setTimeout( function () {
    //let fn = "stdinread.wasm";
    //let fn = "counter.wasm";
    let fn = "signalfd.wasm";
    let mod_uuid = "44c72c87-c4ec-4759-b587-30ddc8590f6b";
    let rt_uuid = RuntimeMngr.runtime.uuid;
    let modCreateMsg = ARTSMessages.mod( {
      uuid: mod_uuid,
      parent: { uuid:  rt_uuid },
      filename: fn,
      channels: [{ path: "/ch/light", type: "pubsub", mode: "rw", params: { topic: "kitchen/light" }}]
    }, ARTSMessages.Action.create);
    RuntimeMngr.mc.simulatePublish(RuntimeMngr.runtime.ctl_topic + "/" + rt_uuid, modCreateMsg); 
  }, 1000);  

/*
  setTimeout( function () {
      RuntimeMngr.signal("44c72c87-c4ec-4759-b587-30ddc8590f6b", SIGNO.QUIT);
  }, 2000);  
*/
}



