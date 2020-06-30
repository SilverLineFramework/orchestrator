
var log_panel;

export function init(element_id) {
    log_panel = document.getElementById(element_id);
}

export function log(message) {
	//console.log(message);
	if (message.length > 1)
		log_panel.innerHTML += escapeHtml(message) + '<br/>';
	log_panel.scrollTop = log_panel.scrollHeight;
};

// Use the browser's built-in functionality to quickly and safely escape
// the string
export function escapeHtml(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}