var Food = require("../entities/food");
var FoodModel = require("../models/FoodModel");
var SnakeModel = require("../models/SnakeModel");
//var RankModel = require('../models/RankModel')
var RobotService = require('./RobotService');
var Consts = require("../utils/constants");
var PacketMsg = require("../packets/PacketMsg");
//var RankService = require("./RankService");

var RadarService = {
    radarMsg: null,

    updateRadarSnake: function () {
        var radarInfo = {};
        radarInfo.radarSnakeInfo = [];
        //RankService.getTopRankList().forEach(data => {
        var snakeArray = RobotService.robotSnakes;
        snakeArray.forEach(snake => {
            //var id = data.snakeId;
            //var snake = SnakeModel.getById(id);
            var position = snake.getHeadPos();
            //console.log("snake.getHeadPos()= ", position);
            radarInfo.radarSnakeInfo.push(position);
        });

        //var updateRadarInfo = {};
        //updateRadarInfo.radarInfo = radarInfo;
        //this.radarMsg = PacketMsg.packetMsg(Consts.MessageType.UPDATE_RADAR_INFO, updateRadarInfo);

        this.radarMsg = radarInfo;
    },

    updateRadarInfo: function () {
        this.updateRadarSnake();
    },

    getRadarInfo: function () {
        return this.radarMsg;
    }
};

module.exports = RadarService;
