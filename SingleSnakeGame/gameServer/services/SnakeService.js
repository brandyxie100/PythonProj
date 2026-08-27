var SnakeModel = require('../models/SnakeModel');
var settings = require("../utils/settings");
var FoodModel = require("../models/FoodModel");
var EventEmitter = require('../utils/eventEmitter');
var RobotService = require('./RobotService');
//var HistoryDataModel = require('../models/HistoryDataModel');
var Consts = require("../utils/constants");

var g_mapSize = settings.readSetting("map-size");
var g_mapRadius = settings.readSetting("map-radius");
var g_frameTime = settings.readSetting("frame", 30);

var SnakeService = {
    playerSnakeID: 0,

    updateSnake: function (PacketHandler, dt) {
        if (!PacketHandler) {
            return;
        }

        var snake = PacketHandler.getSnake();
        if (!snake || snake.dead) {
            return;
        }
        this.playerSnakeID = snake.snakeId;

        var distX = snake.headPos.xPos - g_mapSize / 2;
        var distY = snake.headPos.yPos - g_mapSize / 2;
        if (Math.pow(distX, 2) + Math.pow(distY, 2) > Math.pow(g_mapRadius, 2)) {
            snake.dead = 1;
            EventEmitter.emit('SnakeSuicide', snake);
            EventEmitter.emit('DestorySnake', [snake.snakeId]);
            this.delete(snake.snakeId);
            return;
        }

        // Move snake
        snake.updateMove(dt);
    },

    delete: function (snakeId) {
        SnakeModel.delete(snakeId);
    },

    getSnake: function (snakeId) {
        return SnakeModel.getById(snakeId);
    },

    updateKillSnakeInfo: function (collision) {
        var outKillSnake = collision.killedSnake;
        this.snakeKillInfo = [];
        EventEmitter.emit('KillSnakeInfo', outKillSnake);

        var self = this;
        outKillSnake.forEach(function (snakeDeath, snakeId) {
            var snakeKiller = SnakeModel.getById(snakeId);
            if (!snakeKiller || snakeKiller.isProtected()) {
                return;
            }

            var killInfo = {
                killerId: snakeId,
                killerName: snakeKiller.name,
                snakeDeathInfo: []
            };
            var killedName = null;
            var snake;
            for (var snakeId of snakeDeath) {
                killInfo.snakeDeathInfo.push({
                    snakeId: snakeId
                });

                snake = SnakeModel.getById(snakeId);
                if (snake && snake.isProtected()) {
                    return;
                }
                if (snake) {
                    //HistoryDataModel.setEnemyInfo(snakeId, {
                    //    enemyId: killInfo.killerId,
                    //    enemyName: killInfo.killerName
                    //});
                    FoodModel.generateDeathFood(snake);
                    if (!snake.isRobot) {
                        self.handleDeathOne(snakeId);
                    } else {
                        RobotService.handleDeath(snake);
                    }
                    killedName = snake.name;
                }
            }
            self.snakeKillInfo.push(killInfo);

            snakeKiller.addKillCount(snakeDeath.length, killedName);
        });
    },

    getKillSnakeInfo: function (PacketHandler) {
        if (!PacketHandler) {
            return;
        }

        var snakeSelf = PacketHandler.getSnake();
        if (!snakeSelf) {
            return;
        }

        var snakeKillInfo = [];
        this.snakeKillInfo.forEach(killInfo => {
            var has = PacketHandler.visibleSnakes.has(killInfo.killerId);
            if (killInfo.killerId == snakeSelf.snakeId || has) {
                snakeKillInfo.push(killInfo);
            }

            //if (killInfo.killerId == snakeSelf.snakeId) {
            //var enemyInfo = HistoryDataModel.getEnemyInfo(snakeSelf.snakeId);
            //if (enemyInfo) {
            //    for (var i = 0; i < killInfo.snakeDeathInfo.length; i++) {
            //        var deathInfo = killInfo.snakeDeathInfo[i];
            //        if (deathInfo.snakeId == enemyInfo.enemyId) {
            //            var callBoardInfo = {};
            //            callBoardInfo.boardType = Consts.BoardInfoType.REVENGE_KILL;
            //            callBoardInfo.killerName = snakeSelf.name;
            //            callBoardInfo.killedName = enemyInfo.enemyName;
            //            PacketHandler.sendToClient(Consts.MessageType.UPDATE_CALL_BOARD, callBoardInfo);
            //            //HistoryDataModel.setEnemyInfo(snakeSelf.snakeId, null);
            //            break;
            //        }
            //    }
            //}
            //}
        });

        return snakeKillInfo;
    },

    updateEatInfo: function (eatInfos) {
        for (var i = 0; i < eatInfos.length; i++) {
            var eatInfo = eatInfos[i];
            var snakeId = eatInfo.snakeId;
            var snake = SnakeModel.getById(snakeId);
            for (var j = 0; j < eatInfo.eatFoods.length; j++) {
                var foodId = eatInfo.eatFoods[j];
                var food = FoodModel.getById(foodId);
                if (food) {
                    snake.addEnergy(food.energy);
                }
            }

            if (snakeId == this.playerSnakeID) {
                //console.log("player eat food: length= " + snake.energy);
                RobotService.setRobotAIByLength(snake.energy);
            }
        }
    },

    handleDeathOne: function (snakeId) {
        var snake = SnakeModel.getById(snakeId);
        if (snake) {
            snake.dead = 1;
        }
        SnakeModel.delete(snakeId);
    }

};

module.exports = SnakeService;

