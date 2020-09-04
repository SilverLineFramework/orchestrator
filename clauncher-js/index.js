import * as RuntimeMngr from '/runtime-mngr.js'
import { SIGNO } from '/signal.js'
import * as ARTSMessages from "/arts-msgs.js";

// make RuntimeMngr available 
window.WASMRuntimeManager = RuntimeMngr;

/* start runtime after page and other scripts are loaded; */
window.addEventListener('onauth', (event) => {
  let mqtt_uri;
  let name;

  if (globals) {
    let mqttParamZ;
    if (defaults) mqttParamZ=defaults.mqttParamZ;
    // use globals.mqttParam/defaults.mqttParamZ for mqtt server, if exists; fallback to mqqt server uri from browser location
    mqtt_uri = globals.mqttParam !== undefined ? globals.mqttParam : mqttParamZ !== undefined ? "wss://" + defaults.mqttParamZ + "/mqtt/" : "wss://" + location.hostname + (location.port ? ':'+location.port : '') + "/mqtt/";
    // use globals.userParam for runtime name, if exists; otherwise let the runtime manager assign one
    name = globals.userParam !== undefined ? "rt-"+Math.round(Math.random() * 10000)+"-"+globals.userParam : undefined;
  }

  RuntimeMngr.init({ 
    mqtt_uri: mqtt_uri, 
    onInitCallback: runtimeInitDone, 
    name: name,
    dbg: true
  });
});

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

