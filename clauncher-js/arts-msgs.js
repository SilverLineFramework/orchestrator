import {v4 as uuidv4} from 'uuid'; // https://www.npmjs.com/package/uuidjs

export var Action = {
    create: "create",
    delete: "delete"
}

export var ObjType = {
    rt: "runtime",
    mod: "module"
}

export var Type = {
    req: "arts_req",
    resp: "arts_resp"
}

export var Result = {
    ok: "ok",
    err: "error"
}

// register/delete (according to msg_action) runtime message
export function rt(rt, msg_action) {
    let msg = req(msg_action);

    msg.data = {
        type: ObjType.rt,
        uuid: rt.uuid,
        name: rt.name,
        max_nmodules: rt.max_nmodules,
        apis: rt.apis,
    };
    return msg;
}

// register/delete module message
export function mod(mod_data, msg_action) {
    let msg = req(msg_action);

    mod_data = mod_data || {};

    msg.data = {
        type: ObjType.mod,
        uuid: mod_data.uuid !== undefined ? mod_data.uuid : uuidv4(),
        name: mod_data.name !== undefined ? mod_data.name: mod_data.filename !== undefined ? mod_data.filename + "@" + navigator.product: "mod-" + Math.round(Math.random() * 10000) + "@" + navigator.product,
        parent: mod_data.parent !== undefined ? mod_data.parent : "{}",
        filename: mod_data.filename !== undefined ? mod_data.filename : "",
        fileid: mod_data.fileid !== undefined ? mod_data.fileid : "na",
        filetype: mod_data.filetype !== undefined ? mod_data.filetype : "WA",
        env: mod_data.env !== undefined ? mod_data.env : "",
        args: mod_data.args !== undefined ? mod_data.args : "",
        channels: mod_data.channels !== undefined ? mod_data.channels : [],
        wait_state: mod_data.wait_state !== undefined ? mod_data.wait_state : "false",
        memory: mod_data.memory
      };
    
    return msg;
}

// request message
export function req(msg_action) {
    return {
        object_id: uuidv4(), // tmp uuid, used as a transaction id
        action: msg_action,
        type: "arts_req"
    }
}