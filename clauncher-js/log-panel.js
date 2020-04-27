
var log_panel;

export function init(element_id) {
    log_panel = document.getElementById('log_panel');
}

export function log(message) {
	console.log(message);
	if (message.length > 1)
    	log_panel.innerHTML += message + '<br/>';
    log_panel.scrollTop = log_panel.scrollHeight;
};
