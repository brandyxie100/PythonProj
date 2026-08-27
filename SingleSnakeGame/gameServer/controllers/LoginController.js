'use strict'
var Util = require('util')
var Controller = require('./Controller')
var SnakeModel = require('../models/SnakeModel')
var Constants = require('../utils/constants')
var GlobalInfoService = require('../services/GlobalInfoService')
var RoomService = require('../services/RoomService')
var EventEmitter = require('../utils/eventEmitter');
var settings = require("../utils/settings");
var gameUtils = require("../utils/gameUtils");
var FoodModel = require("../models/FoodModel");

class LoginController extends Controller {

    constructor(PacketHandler) {
        super(PacketHandler);

        console.log("LoginController: constructor");
    }

    login(loginRequest) {

        if (this.PacketHandler.isActive()) {
            console.log("Snake is already active", this.PacketHandler.snakeId);
            return;
        }
        if (RoomService.getStatus() == "stop") {
            console.log(RoomService.getStatus() == "stop");
            this.PacketHandler.sendErrorMsg(Constants.MessageType.ERROR_RESPONSE, Constants.ErrorCode.ROOM_IS_FULL);
            return;
        }

        //if (this.PacketHandler.getClientsNum() > MAX_PLAYER_NUM) {
        //    this.PacketHandler.sendErrorMsg(Constants.MessageType.ERROR_RESPONSE, Constants.ErrorCode.ROOM_IS_FULL);
        //    return;
        //}
        //
        //var clientVersion = loginRequest.version;
        //if (!gameUtils.compareVersion(clientVersion)) {
        //    this.PacketHandler.sendErrorMsg(Constants.MessageType.ERROR_RESPONSE, Constants.ErrorCode.VERSION_TOO_LOW);
        //    return;
        //}

        var userName = loginRequest.name || Math.random().toString().substring(2, 12);
        var data = SnakeModel.getInitSnake(userName);
        if (loginRequest.screenWidth && loginRequest.screenHeight) {
            data.setScreenParams(loginRequest.screenWidth, loginRequest.screenHeight);
        }

        var result = data;
        SnakeModel.insert(data);
        this.PacketHandler.setSnake(result);

        GlobalInfoService.updateVisibleFoods(this.PacketHandler);

        this.sendToClient(
            Constants.MessageType.LOGIN_RESPONSE,
            {
                name: data.name,
                globalInfo: GlobalInfoService.getData(this.PacketHandler, true),
                endTime: RoomService.ensureEndTime()
            }
        );
    }

    revive(reviveSnake) {

        if (this.PacketHandler.isActive()) {
            console.log("Snake is already active", this.PacketHandler.snakeId);
            return;
        }

        var userName = reviveSnake.name || Math.random().toString().substring(2, 12);
        var data = SnakeModel.getInitSnake(userName);
        if (reviveSnake.screenWidth && reviveSnake.screenHeight) {
            data.setScreenParams(reviveSnake.screenWidth, reviveSnake.screenHeight);
        }

        var result = data;
        SnakeModel.insert(data);
        this.PacketHandler.setSnake(result);

        GlobalInfoService.updateVisibleFoods(this.PacketHandler);

        this.sendToClient(
            Constants.MessageType.REVIVE_RESPONSE,
            {
                name: data.name,
                globalInfo: GlobalInfoService.getData(this.PacketHandler, true)
            }
        );

        EventEmitter.emit('Revive', {
            reviveSnake: reviveSnake,
            newSnake: result
        });
    }

    eatNearFood(snake) {
        var nearestOthFoodId = 0;
        var nearestOthFoodDist = Math.pow(snake.screenX, 2) + Math.pow(snake.screenY, 2);
        var normalFoods = FoodModel.getFromBlockStore(snake.headPos.xPos, snake.headPos.yPos, snake.screenX, snake.screenY);
        normalFoods.forEach(foodId => {
            var food = FoodModel.getById(foodId);
            if (food) {
                var distPow = Math.pow(snake.headPos.xPos - food.position.xPos, 2) + Math.pow(snake.headPos.yPos - food.position.yPos, 2);
                if (distPow < nearestOthFoodDist) {
                    nearestOthFoodDist = distPow;
                    nearestOthFoodId = foodId;
                }
            }
        });

        if (!nearestOthFoodId) {
            console.error("nearestOthFoodId is 0");
            var self = this;
            setTimeout(function () {
                self.eatNearFood(snake);
            }, 3000);
        } else {
            var eatFoodInfo = [];
            eatFoodInfo.push({snakeId: snake.snakeId, eatFoods: [nearestOthFoodId]});

            this.sendToClient(Constants.MessageType.UPDATE_EAT_FOOD, {eatFoodInfo: eatFoodInfo});
        }
    }
}

module.exports = LoginController;