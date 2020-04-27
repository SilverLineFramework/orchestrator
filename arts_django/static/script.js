var reload_interval_milli = 5000

var topic = 'realm/proc/control';
var ctl_topic = 'realm/proc/control';
var dbg_topic = 'realm/proc/debug';
var stdout_topic = dbg_topic+'/stdout';

var pending_uuid="";

var stdout_txt=[];

var selected_mod;
var status_box;
var stdout_box;
var treeData;
var mqttc;

document.addEventListener('DOMContentLoaded', function() {
    status_box = document.getElementById('status-box');
    stdout_box = document.getElementById('stdout-box');
    module_label = document.getElementById('module_label');
    runtime_select = document.getElementById('runtime_select');
    loadTreeData();
    startConnect();
    setTimeout(loadTreeData, reload_interval_milli); // reload data periodically
});

function displayTree(treeData) {
    // Set the dimensions and margins of the diagram
    var margin = {top: 20, right: 90, bottom: 30, left: 90},
        width = 960 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;

    // append the svg object to the body of the page
    // appends a 'group' element to 'svg'
    // moves the 'group' element to the top left margin
    panel = document.getElementById('panel')
    
    d3.select("svg").remove(); 

    //if (svg == undefined) {
        svg = d3.select("div").append("svg")
            .attr("width", width + margin.right + margin.left)
            .attr("height", height + margin.top + margin.bottom)
        .append("g")
            .attr("transform", "translate("
                + margin.left + "," + margin.top + ")");
    //}

    //d3.select("g.parent").selectAll("*").remove();
    //root.remove();
    
    var i = 0,
        duration = 750,
        root;

    // declares a tree layout and assigns the size
    var treemap = d3.tree().size([height, width]);

    // Assigns parent, children, height, depth
    root = d3.hierarchy(treeData, function(d) { return d.children; });
    root.x0 = height / 2;
    root.y0 = 0;

    // Collapse after the second level
    //oot.children.forEach(collapse);

    while (runtime_select.options.length > 0) {                
        runtime_select.remove(0);
    }  

    runtime_select.options[runtime_select.options.length] = new Option('Schedule', '');

    // Define the div for the tooltip
    var div = d3.select("body").append("div")	
        .attr("class", "tooltip")				
        .style("opacity", 0);

    update(root);

    // Collapse the node and all it's children
    function collapse(d) {
    if(d.children) {
        d._children = d.children
        d._children.forEach(collapse)
        d.children = null
    }
    }

    function update(source) {

    // Assigns the x and y position for the nodes
    var treeData = treemap(root);

    // Compute the new tree layout.
    var nodes = treeData.descendants(),
        links = treeData.descendants().slice(1);

    // Normalize for fixed-depth.
    nodes.forEach(function(d){ d.y = d.depth * 180});

    // ****************** Nodes section ***************************

    // Update the nodes...
    var node = svg.selectAll('g.node')
        .data(nodes, function(d) {return d.id || (d.id = ++i); });

    // Enter any new modes at the parent's previous position.
    var nodeEnter = node.enter().append('g')
        .attr('class', 'node')
        .attr("transform", function(d) {

            if("undefined" === typeof(d.data["filename"])){
                if("string" === typeof(d.data["uuid"])){
                    //runtimes[d.data.uuid] = { uuid: d.data.uuid, name: d.data.name }
                    runtime_select.options[runtime_select.options.length] = new Option(d.data.name+'('+d.data.uuid+')', d.data.uuid);
                }
            }

            return "translate(" + source.y0 + "," + source.x0 + ")";

        })
        .on('click', click);

    // Add Circle for the nodes
    nodeEnter.append('circle')
        .attr('class', 'node')
        .attr('r', 1e-6)
        .style("fill", function(d) {
            return d._children ? "lightsteelblue" : "#fff";
        });

    // Add labels for the nodes
    nodeEnter.append('text')
        .attr("dy", ".35em")
        .attr("x", function(d) {
            return d.children || d._children ? -13 : 13;
        })
        .attr("text-anchor", function(d) {
            return d.children || d._children ? "end" : "start";
        })
        .on("mouseover", function(d) {	
                if("undefined" === typeof(d.data["filename"])){
                    // runtime
                    disp_text = d.data.uuid  + "<br/>" + "nmodules:" + d.data.nmodules  + "<br/>";
                }else{
                    // module
                    disp_text = d.data.uuid  + "<br/>" + "filename:" + d.data.filename  + "<br/>";
                }            	
                div.transition()		
                    .duration(200)		
                    .style("opacity", .9);		
                div	.html(disp_text)	
                    .style("left", (d3.event.pageX) + "px")		
                    .style("top", (d3.event.pageY - 28) + "px");	
                })					
            .on("mouseout", function(d) {		
                div.transition()		
                    .duration(500)		
                    .style("opacity", 0);	
            })
        .text(function(d) { return d.data.name; });

    // UPDATE
    var nodeUpdate = nodeEnter.merge(node);

    // Transition to the proper position for the node
    nodeUpdate.transition()
        .duration(duration)
        .attr("transform", function(d) { 
            return "translate(" + d.y + "," + d.x + ")";
        });

    // Update the node attributes and style
    nodeUpdate.select('circle.node')
        .attr('r', 10)
        .style("fill", function(d) {
            return d._children ? "lightsteelblue" : "#fff";
        })
        .attr('cursor', 'pointer');

    // Remove any exiting nodes
    var nodeExit = node.exit().transition()
        .duration(duration)
        .attr("transform", function(d) {
            return "translate(" + source.y + "," + source.x + ")";
        })
        .remove();

    // On exit reduce the node circles size to 0
    nodeExit.select('circle')
        .attr('r', 1e-6);

    // On exit reduce the opacity of text labels
    nodeExit.select('text')
        .style('fill-opacity', 1e-6);

    // ****************** links section ***************************

    // Update the links...
    var link = svg.selectAll('path.link')
        .data(links, function(d) { return d.id; });

    // Enter any new links at the parent's previous position.
    var linkEnter = link.enter().insert('path', "g")
        .attr("class", "link")
        .attr('d', function(d){
            var o = {x: source.x0, y: source.y0}
            return diagonal(o, o)
        });

    // UPDATE
    var linkUpdate = linkEnter.merge(link);

    // Transition back to the parent element position
    linkUpdate.transition()
        .duration(duration)
        .attr('d', function(d){ return diagonal(d, d.parent) });

    // Remove any exiting links
    var linkExit = link.exit().transition()
        .duration(duration)
        .attr('d', function(d) {
            var o = {x: source.x, y: source.y}
            return diagonal(o, o)
        })
        .remove();

    // Store the old positions for transition.
    nodes.forEach(function(d){
        d.x0 = d.x;
        d.y0 = d.y;
    });
    }
  // Creates a curved (diagonal) path from parent to the child nodes
  function diagonal(s, d) {

    path = `M ${s.y} ${s.x}
            C ${(s.y + d.y) / 2} ${s.x},
              ${(s.y + d.y) / 2} ${d.x},
              ${d.y} ${d.x}`

    return path
  }

  // Toggle children on click.
  function click(d) {
    if (d.children) {
        d._children = d.children;
        d.children = null;
      } else {
        d.children = d._children;
        d._children = null;
      }

    if (selected_mod != undefined) {
        console.log("Unsubscribing from:"+ stdout_topic + "/" + selected_mod.uuid)
        mqttc.unsubscribe(stdout_topic + "/" + selected_mod.uuid);
    }
    selected_mod = d.data;
    console.log("Subscribing:"+ stdout_topic + "/" + selected_mod.uuid)
    mqttc.subscribe(stdout_topic + "/" + selected_mod.uuid);
    stdout_box.value = "";
    module_label.innerHTML = "Stdout for module '" + selected_mod.name + "' (" + selected_mod.uuid + ")" + " :";
    //console.log(d.data)
  }
}

async function sendRequest(mthd = 'POST', rsrc = '', data = {}) {
    // Default options are marked with *
    url = 'http://' + window.location.host + rsrc;
    //console.log(url)
    const response = await fetch(url, {
        method: mthd, // *GET, POST, PUT, DELETE, etc.
        cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
        credentials: 'omit', // include, *same-origin, omit
        headers: {
            'Content-Type': 'application/json'
        },
        referrer: 'no-referrer', // no-referrer, *client
    });
    if (mthd = 'POST') {
        response.body = JSON.stringify(data); // body data type must match 'Content-Type' header
    }
    return await response.json(); // parses JSON response into native JavaScript objects
}

async function loadTreeData() {
    setTimeout(loadTreeData, reload_interval_milli); // reload data periodically   
    c_data = await sendRequest('GET', '/api/v1/runtimes/');     
    td = {
        "name": "arena", "t": "t1",
        "children" : c_data
    }
    if (_.isEqual(treeData, td) == false) {
        treeData=td;
        displayTree(treeData);
    }

}

// Called after DOMContentLoaded
function startConnect() {
    // Generate a random client ID
    clientID = 'clientID-' + parseInt(Math.random() * 100);

    host = document.getElementById('mqtt_server').value;
    port = document.getElementById('mqtt_port').value;

    // Print output for the user in the messages div
    status_box.value += 'Connecting to: ' + host + ' on port: ' + port + '\n';
    status_box.value += 'Using the following mqttc value: ' + clientID + '\n';

    // Initialize new Paho client connection
    mqttc = new Paho.MQTT.Client(host, Number(port), clientID);

    // Set callback handlers
    mqttc.onConnectionLost = onConnectionLost;
    mqttc.onMessageArrived = onMessageArrived;

    // Connect the client, if successful, call onConnect function
    mqttc.connect({
        onSuccess: onConnect,
    });
}

// Called on connect button click
function reConnect() {
    try {
        mqttc.disconnect();
    } catch (err) {
        console.log("Not connected..");
    }
    startConnect();
}

// Called when the client connects
function onConnect() {
    // Print output for the user in the messages div
    status_box.value += 'Subscribing to: ' + ctl_topic + '\n';

    // Subscribe to the requested topic
    mqttc.subscribe(ctl_topic);
}

// Called when the client loses its connection
function onConnectionLost(responseObject) {
    console.log('Disconnected...');

    status_box.value += 'Disconnected.\n';
    if (responseObject.errorCode !== 0) {
        status_box.value += 'ERROR: ' + responseObject.errorMessage + '\n';
    }
}

// Called when a message arrives
function onMessageArrived(message) {
    status_box.value += 'Received: ' + message.payloadString + '\n';
 
    //console.log(message);
    //console.log("Dbg msg");
//ff93c36f-74a0-478d-8d29-4ab6412d5f8c
    if (message.destinationName.startsWith(stdout_topic)) {
        /*
        mod_uuid = message.destinationName.substring(message.destinationName.length-36);
        console.log("uuid:"+mod_uuid);
        if (stdout_txt[mod_uuid] == undefined) stdout_txt[mod_uuid] = "";
        stdout_txt[mod_uuid] = message.payloadString + '\n' + stdout_txt[mod_uuid];
        if (selected_mod.uuid == mod_uuid){
            stdout_box.value = message.payloadString + '\n' + stdout_box.value;
        }
        */
        stdout_box.value = message.payloadString + '\n' + stdout_box.value;
    }

    if (message.destinationName == ctl_topic) {
        //console.log(message.payloadString);
        var msg_req = JSON.parse(message.payloadString);
        //console.log(msg_req.uuid)
        //console.log(pending_uuid)
        //console.log(msg_req.type)
        if (pending_uuid == msg_req.object_id && msg_req.type == 'arts_resp') {
                console.log(msg_req.data)
                if (msg_req.data.result == 'ok') {
                    mod_instance = JSON.parse(msg_req.data.details);
                    // Print output for the user in the messages div
                    status_box.value += 'Created: ' + mod_instance + '\n';
                    //stdout_txt[mod_instance.uuid] = "";
                    //mqttc.subscribe(stdout_topic + "/" + mod_instance.uuid);
                } else {
                    // Print output for the user in the messages div
                    status_box.value += 'Error: ' + msg_req.data.details + '\n';
                } 
        }
    }
}

// Called when the disconnection button is pressed
function startDisconnect() {
    mqttc.disconnect();
    status_box.value += 'Disconnected\n';
}

function uuidv4() {
    return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
      (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
  }

function createModule() {
    mname = document.getElementById('mname').value;
    fn = document.getElementById('filename').value;
    fid = document.getElementById('fileid').value;
    ft = document.getElementById('filetype').value;
    args = document.getElementById('args').value;
    modid = document.getElementById('runtime_select').value;

    pending_uuid = uuidv4();

    req = { 
        object_id: pending_uuid, 
        action: "create",
        type: "arts_req", 
        data: { 
            type: "module", 
            name: mname, 
            filename: fn, 
            fileid: fid,
            filetype: ft, 
            args: args
        }
    } 

    console.log(modid);
    if (modid.length > 0) {
        console.log('adding parent');
        req.data.parent_object_id = modid
    }

    req_json = JSON.stringify(req);
    console.log("Publishing ("+ctl_topic+"):"+req_json);
    message = new Paho.MQTT.Message(req_json);
    message.destinationName = req_json;
    mqttc.send(ctl_topic, req_json); 

    setTimeout(loadTreeData, 500); // reload data in 0.5 seconds
} 
