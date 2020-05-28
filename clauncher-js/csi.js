/**
 * @fileoverview "CONIX Standard Interface"; For test/prototype purposes
 * 
 * Copyright (C) Wiselab CMU. 
 * @date April, 2020 
 */

export function getImports() {
	return { 
		csi_set_timer: csi_set_timer
	};
} 

export function csi_set_timer(label, interval) {
  setInterval ( function() { instance.imports['timer_'+label] }, interval);
}
