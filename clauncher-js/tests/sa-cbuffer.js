// TODO: write proper tests
import SharedArrayCircularBuffer from '../sa-cbuffer.js'

var b = new SharedArrayCircularBuffer({size: CBUFFER_SIZE});

console.log("push 1");
b.push([1]);
console.log(JSON.stringify(b));

console.log("push 2");
b.push([2]);
console.log(JSON.stringify(b));

console.log("push 3,4");
b.push([3,4]);
console.log(JSON.stringify(b));

console.log("push 5,6,7,8,9,10");
b.push([5,6,7,8,9,10]);
console.log(JSON.stringify(b));

console.log("push 11");
b.push([11]);
console.log(JSON.stringify(b));

console.log("push 12");
b.push([12]);
console.log(JSON.stringify(b));

var d = b.pop(2);
console.log(d);
console.log(JSON.stringify(b));

var d = b.pop(2);
console.log(d);
console.log(JSON.stringify(b));

var d = b.pop(4);
console.log(d);
console.log(JSON.stringify(b));

var d = b.pop(4);
console.log(d);
console.log(JSON.stringify(b));

console.log("push 1,2,3,4,5,6,7,8,9");
b.push([1,2,3,4,5,6,7,8,9]);
console.log(JSON.stringify(b));

var d = b.pop(8);
console.log(d);
console.log(JSON.stringify(b));

var d = b.pop(1);
console.log(d);
console.log(JSON.stringify(b));

var d = b.pop(1);
console.log(d);
console.log(JSON.stringify(b));}