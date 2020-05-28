import * as RuntimeMngr from '/runtime-mngr.js'
import * as LogPanel from '/log-panel.js'

import SharedArrayCircularBuffer from '/sa-cbuffer.js'

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
}

setTimeout( function () {
  let fn = "stdinread.wasm";
  //let fn = "counter.wasm";
  RuntimeMngr.mc.moduleCreateTestMsg(fn); 
}, 1000);