import * as RuntimeMngr from '/runtime-mngr.js'
import { SIGNO } from '/signal.js'
import * as ARTSMessages from "/arts-msgs.js";

// make RuntimeMngr available 
window.WASMRuntimeManager = RuntimeMngr;

/* start runtime after page and other scripts are loaded; */
window.onload = (event) => {
  let mqtt_uri;
  let name;

  if (globals) {
    // use globals.mqttParam for mqtt server, if exists; otherwise build mqqt server uri from hostname
    mqtt_uri = globals.mqttParam !== undefined ? globals.mqttParam : "wss://" + location.hostname + (location.port ? ':'+location.port : '') + "/mqtt/";
    // use globals.userParam for runtime name, if exists; otherwise let the runtime manager assign one
    name = globals.userParam !== undefined ? "rt-"+globals.userParam : undefined;
  }

  RuntimeMngr.init({ 
    mqtt_uri: mqtt_uri, 
    onInitCallback: runtimeInitDone, 
    name: name,
    dbg: true
  });
};

function runtimeInitDone() {
  console.log("Runtime init done.");

  // check if we have modules to start
  if (pendingModules.length > 0) {
    pendingModules.forEach(function(persistm) {
      console.log("Starting:", persistm.data.name);
      RuntimeMngr.createModule(persistm);
    });
  }
  // empty pending modules
  pendingModules = [];
}

