'use strict'
let SnakeModel = require('../models/SnakeModel');
let EventEmitter = require('../utils/eventEmitter');
let Snake = require('../entities/snake');

var globalGameTime = 5; //game time for every round (minutes)

class RoomService {
    constructor() {
        this.roomId = null;
        this.clientsNum = 0;
        this.enableReport = false;
        this.startTime = 0;
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
        this.startTime = new Date().getTime();
        this.endTime = this.startTime + globalGameTime * 60 * 1000;
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

    getElapsedSeconds() {
        if (this.status !== "running" || this.startTime === 0) {
            return 0;
        }
        var elapsed = (new Date().getTime() - this.startTime) / 1000;
        var totalSec = globalGameTime * 60;
        return Math.max(0, Math.min(totalSec, elapsed));
    }

    getMatchProgress() {
        var totalSec = globalGameTime * 60;
        if (totalSec <= 0) {
            return 0;
        }
        return Math.max(0, Math.min(1.0, this.getElapsedSeconds() / totalSec));
    }

    getTier() {
        var progress = this.getMatchProgress();
        if (progress < 0.20) {
            return 1; // Tier 1 (0 - 60s): Docile Forager
        } else if (progress < 0.60) {
            return 2; // Tier 2 (60 - 180s): Agile Competitor
        } else {
            return 3; // Tier 3 (180 - 300s): Apex Predator
        }
    }

    getAITierConfig() {
        var p = this.getMatchProgress(); // 0.0 -> 1.0
        // Continuous smooth interpolation across match
        return {
            tier: this.getTier(),
            progress: p,
            // Dodge reaction interval (seconds between collision checks)
            dodgeInterval: 0.45 - 0.38 * p, // 0.45s down to 0.07s
            // Likelihood of hunting / intercepting nearby snakes vs solely eating food
            huntingAggression: Math.max(0, (p - 0.15) / 0.85), // 0 in early game, rises to 1.0
            // Likelihood of attempting encircling maneuvers when larger
            encircleProp: Math.max(0, (p - 0.25) / 0.75), // 0 -> 1.0
            // Lead time for predictive head interception (seconds into future)
            interceptLead: 0.2 + 1.2 * p, // 0.2s -> 1.4s
            // Multi-ray sensor range scale
            sensorRangeScale: 1.0 + 0.8 * p, // 1.0x -> 1.8x
            // Tactical boost aggressiveness
            tacticalBoostProp: 0.15 + 0.75 * p // 0.15 -> 0.90
        };
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