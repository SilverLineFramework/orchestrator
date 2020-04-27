import * as RuntimeMngr from '/runtime_mngr.js'
import * as MqttClient from '/mqtt-client.js'
import * as LogPanel from '/log-panel.js'

LogPanel.init('log_panel');

// get name
let namePrompt = ""
//namePrompt = prompt(
//  `Enter a name to identify your client\n`
//);

LogPanel.log("Hi " + namePrompt);

RuntimeMngr.init({ onInitCallback: runtimeInitDone, name: namePrompt });

function runtimeInitDone() {
  console.log("runtime init done");  
}
