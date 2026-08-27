'use strict'
let SnakeModel = require('../models/SnakeModel');
let EventEmitter = require('../utils/eventEmitter');
let Snake = require('../entities/snake');

var globalGameTime = 1.5; //game time for every round
//var globalGameTime = 3; //game time for every round

class RoomService {
    constructor() {
        this.roomId = null;
        this.clientsNum = 0;
        this.enableReport = false;
        this.endTime = 0;
        this.status = "ready";
        this.t = null;
    }

    init() {
        console.log("RoomService init");
    }

    onClientClose() {
        this.clientsNum--;
        if (this.clientsNum <= 0) {
            if (this.endTime > 0) {
                this.timeOver()
            }
        } else {
            this.report()
        }
    }

    trigger(roomId, num) {
        this.status = "ready";
        this.setRoomId(roomId);
        this.clientsNum = num;

        if (this.endTime == 0) {
            this.startCountDown();
        }
    }

    startCountDown() {
        this.endTime = new Date().getTime() + globalGameTime * 60 * 1000;
        clearInterval(this.t);
        this.t = setInterval(() => {
            if (new Date().getTime() >= this.endTime) {
                clearInterval(this.t);
                this.timeOver();
            }
        }, 1000);
        if (this.status == "ready") {
            this.status = "running";
            EventEmitter.emit('TimeStart');
        }
    }

    ensureEndTime() {
        if (this.endTime == 0) {
            this.startCountDown()
        }
        return this.endTime;
    }

    setRoomId(roomId) {
        this.roomId = roomId;
    }

    timeOver() {
        this.endTime = 0;
        this.report();
        EventEmitter.emit('TimeOver');

        this.status = "stop";
    }

    report() {
        if (!this.enableReport || !this.roomId) {
            return;
        }
    }

    getStatus() {
        return this.status;
    }

    disableReport() {
        this.enableReport = false;
    }
}

var g_room_server = new RoomService();

g_room_server.init();

module.exports = g_room_server;