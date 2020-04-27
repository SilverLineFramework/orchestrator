var Paho = require('paho-mqtt');
import * as UUID from '/vendor/uuidv4.min'; // https://github.com/uuidjs/uuid

var parameters;

export function mqttClient(parameters) {
        // handle default parameters
        parameters = parameters || {};
        parameters = {
            host: parameters.host !== undefined ? parameters.host : 'oz.andrew.cmu.edu',
            port: parameters.port !== undefined ? parameters.port : 9001,
            //clientid: parameters.clientid !== undefined ? parameters.clientid : UUID.uuidv4(),
            clientid: parameters.clientid !== undefined ? parameters.clientid : 'mqttc-js-client-' + parseInt(Math.random() * 1000),
            subs_topics: parameters.subs_topics !== undefined ? parameters.subs_topics : []
        };
        //clientid: parameters.clientid !== undefined ? parameters.clientid : uuidv4(); // 'mqttc-js-client-' + parseInt(Math.random() * 1000),

        console.log(parameters);
        this.startConnect();
    }

    startConnect() {

        // Initialize new Paho client connection
        this.mqttc = new Paho.Client(this.parameters.host, Number(this.parameters.port), this.parameters.clientid);

        // Set callback handlers
        this.mqttc.onConnectionLost = this.onConnectionLost;
        this.mqttc.onMessageArrived = this.onMessageArrived;
        
        // Connect the client, if successful, call onConnect function
        var _this = this;
        this.mqttc.connect({
            invocationContext: { a: "a"},
            onSuccess: this.onConnect()
        });
    }

    reConnect() {
        try {
            this.mqttc.disconnect();
        } catch (err) {
            console.log("Not connected..");
        }
        startConnect();
    }

    onConnect(invocationContext) {
        console.log(invocationContext);
        console.log('Subscribing to: ' + parameters.subs_topics + '\n');

        // Subscribe to the requested topic
        if (parameters.subs_topics.length > 0)
            mqttc.subscribe(parameters.subs_topics);
    }

    // Called when the client loses its connection
    onConnectionLost(responseObject) {
        console.log('Mqtt client disconnected...');

        if (responseObject.errorCode !== 0) {
            console.log('Mqtt ERROR: ' + responseObject.errorMessage + '\n');
        }
    }

    // Called when a message arrives
    onMessageArrived(message) {
        console.log('Mqtt Msg: ' + message.payloadString + '\n');
    }

    // Called when the disconnection button is pressed
    startDisconnect() {
        this.mqttc.disconnect();
        console.log('Disconnected\n');
    }

};