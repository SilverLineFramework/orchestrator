
export function getImports() {
	return { 
		csi_set_timer: csi_set_timer
	};
}
export function csi_set_timer(label, interval) {
  setInterval ( function() { instance.imports['timer_'+label] }, interval);
}
