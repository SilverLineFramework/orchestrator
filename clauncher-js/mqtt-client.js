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
    this.settings = {
      host: st.host !== undefined ? st.host : "oz.andrew.cmu.edu",
      port: st.port !== undefined ? st.port : 9001,
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
    };

    if (this.settings.willMessage !== undefined)
      this.settings.willMessage.destinationName = st.willMessageTopic;

    if (this.settings.dbg == true) console.log(this.settings);

    _this = this;
  }

  async connect() {
    // init Paho client connection
    this.mqttc = new Paho.Client(
      this.settings.host,
      Number(this.settings.port),
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
        willMessage: _this.settings.willMessage,
      });
    });
  }

  // simulate a module creation message for testing purposes
  moduleCreateTestMsg(fn) {
    let str_msg = '{"object_id": "fcb2780b-abdd-43b6-bc13-895baa2075a2", "action": "create", "type": "arts_req", "data": {"type": "module", "details": {"uuid": "44c72c87-c4ec-4759-b587-30ddc8590f6b", "name": "test", "parent": {"uuid": "' +
    _this.settings.clientid +
    '"}, "filename": "' +
    fn +
    '", "fileid": "na", "filetype": "WA", "args": "", "channels":[{ "path":"/ch/light","type":"pubsub","mode":"w", "params":{ "topic":"kitchen/light" }}]}}}';
    let msg = new Paho.Message(str_msg);
    msg.destinationName = "realm/proc/control/" + _this.settings.clientid;
    _this.settings.onMessageCallback(msg);
  }

  reConnect() {
    try {
      this.mqttc.disconnect();
    } catch (err) {
      if (this.settings.dbg == true) console.log("Not connected..");
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
