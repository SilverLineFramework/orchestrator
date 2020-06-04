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
    let wasmFilePath = "./" + e.data.arts_mod_instance_data.filename;
    console.log("Starting new module",  e.data.arts_mod_instance_data);

    // Fetch our Wasm File
    const response = await fetch(wasmFilePath);
    const wasmBytes = new Uint8Array(await response.arrayBuffer());

    // Transform the WebAssembly module interface (https://docs.wasmer.io/integrations/js/module-transformation)
    const loweredWasmBytes = await lowerI64Imports(wasmBytes);

    // Compile the WebAssembly file
    let wasmModule = await WebAssembly.compile(loweredWasmBytes);

    // instance to handle the IO for the new module; creates wasmFs intance
    let mio = new moduleIO({shared_array_buffer: e.data.shared_array_buffer, worker_port: e.data.worker_port, mod_data: e.data.arts_mod_instance_data});
    
    // Instantiate new WASI Instance
    let wasi = new WASI({
      preopenDirectories: {'/sys/': '/sys/', ...mio.channelDirectories()},
      // Arguments passed to the Wasm Module
      // The first argument is usually the filepath to the executable WASI module
      // we want to run.
      args: [wasmFilePath],

      // Environment variables that are accesible to the WASI module
      env: {},

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
    try {
      wasi.start(instance); // Start the transformed WASI instance
    } catch(e) {
      // WASI throws exception on non-zero return; ignore
      //console.log(e);  
    }

    //console.log(instance.globals);
    let mem = Base64.encode(instance.exports.memory.buffer);

    mio.IOWorkerPort.postMessage({
      type: WorkerMessages.msgType.mem,
      mod_uuid: e.data.arts_mod_instance_data.uuid,
      mem: mem
    });
  }
};
