require("babel-polyfill");
var PacketHandler = require('../packets/PacketHandler');
var RoomService = require('../services/RoomService');
var configManager = require("../config/ConfigMgr");

var gPacketHandler = {
    mPacketHandler: null,

    runServer(){
        console.log("runServer()");
        if (null == this.mPacketHandler) {
            console.log("runServer(): create packetHandler");
            RoomService.disableReport();
            configManager.init();

            this.mPacketHandler = new PacketHandler();
        }
    },

    restart(){
        this.mPacketHandler = null;
    },

    getHandler(){
        return this.mPacketHandler;
    },

    pauseGame(){
        if (this.mPacketHandler) {
            this.mPacketHandler.pauseServer();
        }
    },

    resumeGame(){
        if (this.mPacketHandler) {
            this.mPacketHandler.resumeServer();
        }
    }

};

module.exports = gPacketHandler;