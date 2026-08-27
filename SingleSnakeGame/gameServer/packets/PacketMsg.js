var CmdConfig = require('./CmdConfig');

//var ProtoBuf = dcodeIO.ProtoBuf;
//var file = "res/snake.proto";
//var builder = ProtoBuf.loadProto(Util.readTxtFileSync(file), null, file);
//var MessageBuilder = builder.build("Snake");

//var os = require("os");
//var is_window_os = /Window/.test(os.type());
//var is_window_os = false;
//var raw_pack = null;
//var raw_unpack = null;
//if (is_window_os) {
//    raw_pack = function(result)
//    {
//        var message = new MessageBuilder.Request(result);
//        return  message.toBuffer();
//    };
//    raw_unpack = function(data, useBinary) {
//        if (useBinary) {
//            var message = MessageBuilder.Request.decode(data);
//        }
//        else {
//            var message = JSON.parse(data);
//        }
//        return message;
//    };
//}
//else
//{
//    var p = require("node-protobuf") ;
//	var fs = require("fs");
//    var pb = new p(fs.readFileSync(path.join(__dirname,"snake.desc")));
//    raw_pack = function(result) {
//        return pb.serialize(result, "Snake.Request");
//    };

var raw_unpack = function (data) {
    //if (useBinary) {
    //    var message = pb.parse(data, "Snake.Request");
    //    this.useBinary = true;
    //}
    //else {
    var message = JSON.parse(data);
    this.useBinary = false;
    //}
    return message;
};
//}

var PacketMsg = {
    packetMsg: function (cmd, data) {
        var config = CmdConfig[cmd];
        var msgHead = {serverTime: (new Date()).getTime()};
        var packetBody = config.packetBody;
        var result = {};
        result['messageType'] = [cmd];
        result['messageHead'] = msgHead;
        result[packetBody] = data;

        var message = JSON.stringify(result);
        return message;
    },
    decodeMsg: raw_unpack,

    packetMsgBatch: function (datas, bBin) {
        var msgHead = {serverTime: (new Date()).getTime()};
        var result = {
            messageType: [],
            messageHead: msgHead,
        };

        for (var a of datas) {
            var cmd = a.cmd;
            var data = a.data;
            var config = CmdConfig[cmd];
            var packetBody = config.packetBody;
            result.messageType.push(cmd);
            result[packetBody] = data;
        }

        var message = null;
        if (bBin) {
            message = raw_pack(result);
        } else {
            message = JSON.stringify(result);
        }
        return message;
    }
};

module.exports = PacketMsg;