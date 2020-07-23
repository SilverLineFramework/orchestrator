import * as RuntimeMngr from '/runtime-mngr.js'
import { SIGNO } from '/signal.js'
import * as ARTSMessages from "/arts-msgs.js";

// make entrypoints available 
window.WASMRuntimeManager = { 
  rtsettings: RuntimeMngr.runtime, // runtime settings (uuid, name, ...)  
  init: RuntimeMngr.init, // runtime init
  signal: RuntimeMngr.signal, // send a signal to a module
  msgs: ARTSMessages, 
  SIGNO: SIGNO 
};