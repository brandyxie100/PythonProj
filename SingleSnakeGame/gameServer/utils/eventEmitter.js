var EventEmitter = require('events');
var util = require('util');

function MyEmitter() {
    EventEmitter.call(this);
}
util.inherits(MyEmitter, EventEmitter);

var MyEmitterIns = new MyEmitter();
module.exports = MyEmitterIns;
