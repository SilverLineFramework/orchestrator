/**
 * @fileoverview Paho mqtt client wrapper
 *
 */
import * as Paho from "paho-mqtt"; //https://www.npmjs.com/package/paho-mqtt

var _this;

/**
 * Mqtt client wrapper class
 */
export default class MqttClient {
  /**
   * Create an mqtt client instance
   * @param st an object with the client setting
   */
  constructor(st) {
    // handle default this.settings
    st = st || {};
    if (st.host == undefined) {
      st.uri = st.uri !== undefined ? st.uri : "wss://spatial.andrew.cmu.edu:4443/mqtt/";
      let match = st.uri.match(/^(wss?):\/\/((\[(.+)\])|([^\/]+?))(:(\d+))?(\/.*)$/);
      if (match) {
        st.host = match[4]||match[2];
        st.port = parseInt(match[7]);
        st.path = match[8];
        if (match[1] == 'ws') st.useSSL = false;
        else st.useSSL = true;
      } else {
        throw new Error("Invalid URI.");
      }
    } else if (st.uri != undefined) console.log("Host defined; Ignoring URI");
    this.settings = {
      uri: st.uri !== undefined ? st.uri : "wss://spatial.andrew.cmu.edu:4443/mqtt/",
      host: st.host !== undefined ? st.host : "spatial.andrew.cmu.edu",
      port: st.port !== undefined ? st.port : 8083,
      path: st.path !== undefined ? st.path : "/mqtt/",
      clientid:
        st.clientid !== undefined
          ? st.clientid
          : "this.mqttc-client-" + Math.round(Math.random() * 10000),
      subscribeTopics: st.subscribeTopics,
      onConnectCallback: st.onConnectCallback,
      onConnectCallbackContext: st.onConnectCallbackContext,
      onMessageCallback: st.onMessageCallback,
      willMessage:
        st.willMessage !== undefined
          ? new Paho.Message(st.willMessage)
          : undefined,
      dbg: st.dbg !== undefined ? st.dbg : false,
      reconnect: st.reconnect !== undefined ? st.reconnect : true,
      useSSL: st.useSSL !== undefined ? st.useSSL : true,
    };

    if (this.settings.willMessage !== undefined)
      this.settings.willMessage.destinationName = st.willMessageTopic;

    if (this.settings.dbg == true) console.log(this.settings);

    _this = this;
  }

  async connect() {
    if (this.settings.dbg == true) {
      let wss = this.settings.useSSL == true ? "wss://": "ws://";
      console.log("Connecting: " + wss + this.settings.host + ":" + this.settings.port + this.settings.path);
    }

    // init Paho client connection
    this.mqttc = new Paho.Client(
      this.settings.host,
      Number(this.settings.port),
      this.settings.path,
      this.settings.clientid
    );

    // callback handlers
    this.mqttc.onConnectionLost = this.onConnectionLost.bind(this);
    this.mqttc.onMessageArrived = this.onMessageArrived.bind(this);

    let _this = this;
    return new Promise(function (resolve, reject) {
      // connect the client, if successful, call onConnect function
      _this.mqttc.connect({
        onSuccess: () => {
          if (_this.settings.subscribeTopics != undefined) {
            // Subscribe to the requested topic
            if (_this.settings.subscribeTopics.length > 0) {
              if (_this.settings.dbg == true)
                console.log(
                  "Subscribing to: " + _this.settings.subscribeTopics + "\n"
                );
              _this.mqttc.subscribe(_this.settings.subscribeTopics);
            }
          }
          if (_this.settings.onConnectCallback != undefined)
            _this.settings.onConnectCallback(
              _this.settings.onConnectCallbackContext
            );
          resolve();
        },
        onFailure: () => { throw new Error("Could not connect!"); },
        willMessage: _this.settings.willMessage,
        reconnect: _this.settings.reconnect,
        useSSL: _this.settings.useSSL
      });
    });
  }

  // message publication to self (invoke onMessageCallback directly)
  directMesssage(topic, payload) {
    if (typeof payload !== "string") payload = JSON.stringify(payload);
    let msg = new Paho.Message(payload);
    msg.destinationName = topic;
    _this.settings.onMessageCallback(msg);
  }

  disconnect() {
    try {
      this.mqttc.disconnect();
    } catch (err) {
      if (this.settings.dbg == true) console.log("MQTT Disconnected.");
    }
  }

  reConnect() {
    try {
      this.mqttc.disconnect();
    } catch (err) {
      if (this.settings.dbg == true) console.log("MQTT Disconnected.");
    }
    clientConnect();
  }

  /**
   * Callback; Called when the client loses its connection
   */
  onConnectionLost(responseObject) {
    if (this.settings.dbg == true) console.log("Mqtt client disconnected...");

    if (responseObject.errorCode !== 0) {
      if (this.settings.dbg == true)
        console.log("Mqtt ERROR: " + responseObject.errorMessage + "\n");
    }
  }

  /**
   * Callback; Called when a message arrives
   */
  onMessageArrived(message) {
    if (this.settings.dbg == true)
      console.log(
        "Mqtt Msg [" +
          message.destinationName +
          "]: " +
          message.payloadString +
          "\n"
      );

    if (this.settings.onMessageCallback != undefined)
      this.settings.onMessageCallback(message);
  }

  publish(topic, payload) {
    if (typeof payload !== "string") payload = JSON.stringify(payload);
    if (this.settings.dbg == true)
      console.log("Publishing (" + topic + "):" + payload);
    this.mqttc.send(topic, payload, 0, false);
  }

  subscribe(topic) {
    if (this.settings.dbg == true) console.log("Subscribing :" + topic);
    this.mqttc.subscribe(topic);
  }

  unsubscribe(topic) {
    console.log("Unsubscribing :" + topic);
    this.mqttc.unsubscribe(topic);
  }
}

exports.MqttClient = MqttClient;