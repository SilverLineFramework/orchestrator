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
        object_id: rt.uuid,
        name: rt.name,
        max_nmodules: rt.max_nmodules,
        apis: rt.apis,
    };
    return msg;
}

// register/delete module message
export function mod(mod, msg_action) {
    let msg = req(msg_action);

    msg.data = mod;
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