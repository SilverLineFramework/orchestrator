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
export function mod(mod, msg_action) {
    let msg = req(msg_action);

    msg.data = {
        type: ObjType.mod,
        uuid: mod.uuid !== undefined ? mod.uuid : uuidv4(),
        name: mod.name !== undefined ? mod.name: mod.filename !== undefined ? mod.filename + "@" + navigator.product: "mod-" + Math.round(Math.random() * 10000) + "@" + navigator.product,
        parent: mod.parent !== undefined ? mod.parent : "{}",
        filename: mod.filename !== undefined ? mod.filename : "",
        fileid: mod.fileid !== undefined ? mod.fileid : "na",
        filetype: mod.filetype !== undefined ? mod.filetype : "WA",
        args: mod.args !== undefined ? mod.args : "",
        channels: mod.channels !== undefined ? mod.channels : [],
        wait_state: mod.wait_state !== undefined ? mod.wait_state : "false",
        memory: mod.memory
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