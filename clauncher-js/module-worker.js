// Worker to instantiate WASM Module
// Largely based on https://docs.wasmer.io/integrations/js/wasi/browser/examples/hello-world
import { WasmFs } from '@wasmer/wasmfs'
import { WASI } from '@wasmer/wasi'
import browserBindings from "@wasmer/wasi/lib/bindings/browser"
import { lowerI64Imports } from "@wasmer/wasm-transformer"

import MqttClient from '/mqtt-client.js'
import * as ARTSMessages from '/arts-msgs.js'
import * as WorkerMessages from '/worker-msgs.js'
import * as CSI from "/csi.js"


class moduleIO {

    constructor () {


        // Instantiate new WasmFs Instance
        this.wasmFs = new WasmFs();

        // stdout/stderr write calls
        this.wasmFs.volume.fds[1].write = this.stdWrite.bind(this, 'stdout');
        this.wasmFs.volume.fds[2].write = this.stdWrite.bind(this, 'stderr');
    }

    async start(modData) {
        this.moduleData = modData;
        // start mqtt client
        this.mc = new MqttClient({
            clientid: modData.uuid, // mqtt client id is the runtime uuid
            willMessageTopic: modData.reg_topic,
            willMessage: JSON.stringify(ARTSMessages.mod(modData, ARTSMessages.Action.delete)),
            subscribeTopics: [ modData.stdin_topic ], // subscribe to stdin dbg topic
            onMessageCallback: this.onMessage 
        });     

        return this.mc.connect();
    }

    onMessage() {
        // stdin ?
    }

    stdWrite(desc, buffer) {
        let str_msg = buffer.toString();
        if (str_msg == '\n') return buffer.length; // dont send just '\n' 
        console.log("WASM", desc, str_msg);
        this.mc.publish(this.moduleData.stdout_topic, str_msg); 
        return buffer.length;
    }

}

onmessage = async function(e) {

    if (e.data.type == WorkerMessages.msgType.start ) {

        let wasmFilePath = '/'+e.data.arts_mod_instance_data.filename;
        console.log('Starting new module: ', wasmFilePath);

        // Fetch our Wasm File
        const response  = await fetch(wasmFilePath)
        const wasmBytes = new Uint8Array(await response.arrayBuffer())

        // Transform the WebAssembly module interface (https://docs.wasmer.io/integrations/js/module-transformation)
        const loweredWasmBytes = await lowerI64Imports(wasmBytes)

        // Compile the WebAssembly file
        let wasmModule = await WebAssembly.compile(loweredWasmBytes);

        // module IO instantiate a new mqtt client and wasmFs for the new module 
        let mio = new moduleIO();
        await mio.start(e.data.arts_mod_instance_data);

        // Instantiate new WASI Instance
        let wasi = new WASI({
            // Arguments passed to the Wasm Module
            // The first argument is usually the filepath to the executable WASI module
            // we want to run.
            args: [wasmFilePath],

            // Environment variables that are accesible to the WASI module
            env: {},

            // Bindings used by the WASI instance (fs, path, etc...)
            bindings: {
                ...browserBindings,
                fs: mio.wasmFs.fs
            }
        });
        console.log(wasi);

        // Set imports 
        let imports = wasi.getImports(wasmModule);
        imports.env = CSI.getImports();
        //imports.wasi_unstable.poll_oneoff = poll_oneoff;
        console.log(imports);

        // Instantiate the WebAssembly module
        let instance = await WebAssembly.instantiate(wasmModule, {
            ...imports
        });

        wasi.start(instance); // Start the transformed WASI instance
    }
};

