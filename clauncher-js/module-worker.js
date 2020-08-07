/**
 * @fileoverview Worker to instantiate WASM Module
 *
 * Copyright (C) Wiselab CMU.
 * @date April, 2020
 */
import { WasmFs } from "@wasmer/wasmfs";
import { WASI } from "/wasmer-js/packages/wasi/src";
import browserBindings from "/wasmer-js/packages/wasi/src/bindings/browser.ts";
import { lowerI64Imports } from "@wasmer/wasm-transformer";

import * as Base64 from 'base64-arraybuffer'

import * as WorkerMessages from "/worker-msgs.js";
import * as CSI from "/csi.js";
import moduleIO from "/moduleio.js"

onmessage = async function (e) {
  if (e.data.type == WorkerMessages.msgType.start) {
    let wasmFilePath = e.data.arts_mod_instance_data.filename;
    console.log("Starting new module",  e.data.arts_mod_instance_data);

    console.time("|T: Module Startup/Instanciate");

    // Fetch our Wasm File
    try {
      var response = await fetch(wasmFilePath+"djsd");
    } catch (err) {
      console.log("Could not find file:", wasmFilePath);
      return;
    }
    if (!response.ok) {
      console.log("Could not find file:", wasmFilePath);
      return;
    }
    const wasmBytes = new Uint8Array(await response.arrayBuffer());

    try {
      // Transform the WebAssembly module interface (https://docs.wasmer.io/integrations/js/module-transformation)
      const loweredWasmBytes = await lowerI64Imports(wasmBytes);
    
      // Compile the WebAssembly file
      let wasmModule = await WebAssembly.compile(loweredWasmBytes);
    } catch(err) {
      console.log("Could not compile file (exists?):", wasmFilePath);
      return;
    }
    
    // instance to handle the IO for the new module; creates wasmFs intance
    let mio = new moduleIO({shared_array_buffer: e.data.shared_array_buffer, worker_port: e.data.worker_port, mod_data: e.data.arts_mod_instance_data});

    // create wasi env object out of env param
    let wasi_env={};
    e.data.arts_mod_instance_data.env.split(" ").forEach(function (evar) {
        evarkv = evar.split("=");
        wasi_env[evarkv[0]] = evarkv[1];
    });    

    // if we are restoring the state of the program, set CWLIB_JTEL to indicate that to the module (JTEL = Jump To Event Loop)
    if (e.data.memory !== undefined) {
      wasi_env["CWLIB_JTEL"] = 1;
    }

    // Instantiate new WASI Instance
    let wasi = new WASI({
      preopenDirectories: {'/sys/': '/sys/', ...mio.channelDirectories()},
      // Arguments passed to the Wasm Module
      // The first argument is usually the filepath to the executable WASI module
      // we want to run.
      args: [wasmFilePath],

      // Environment variables that are accesible to the WASI module
      env: wasi_env,

      // Bindings used by the WASI instance (fs, path, etc...)
      bindings: {
        ...browserBindings,
        fs: mio.wasmFs.fs,
        mio: mio // attachIO will attach the read/write functions for channels when wasi path_open is called  
      },
    });

    // wrap wasi path_open to attach our channel IO
    mio.wrapPathOpen(wasi);

    // Set imports
    let imports = wasi.getImports(wasmModule);
    imports.env = CSI.getImports();
    //console.log(imports);

    // Instantiate the WebAssembly module
    let instance = await WebAssembly.instantiate(wasmModule, {
      ...imports, 
    });

    let mem;

    // Restore memory contents, if provided 
    if (e.data.memory !== undefined) { 
      let mem = Base64.decode(e.data.memory); 

      let size = mem.byteLength - instance.exports.memory.buffer.byteLength;
      if (size > 0) { // need to adjust memory size
        let nb = size / 64000;
        console.log("blocks",nb);
        instance.exports.memory.grow(nb);
      }
      // restore bytes
      let sv = new BigUint64Array(mem);
      let tv = new BigUint64Array(instance.exports.memory.buffer);
      for (let i=0; i<instance.exports.memory.buffer.byteLength/BigUint64Array.BYTES_PER_ELEMENT; i++) {
        tv[i] = sv[i];
      }
    }

    console.timeEnd("|T: Module Startup/Instanciate");

    console.time("|T: Module Executed for");
    // Start the WASI instance
    try {
      wasi.start(instance); 
    } catch(e) {
      // WASI throws exception on non-zero return; ignore
      //console.log(e);  
    }
    console.timeEnd("|T: Module Executed for");

    // Get instance memory and send finish message
    mem = Base64.encode(instance.exports.memory.buffer);

    this.postMessage({
      type: WorkerMessages.msgType.finish,
      mod_uuid: e.data.arts_mod_instance_data.uuid,
      memory: mem,
    });
  }
};
