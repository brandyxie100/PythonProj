'use strict';
var SnakeModel = require('../models/SnakeModel');
var settings = require("../utils/settings");
var PacketHandler = require("../packets/PacketHandler");
var EventEmitter = require('../utils/eventEmitter');
var FoodModel = require("../models/FoodModel");
var Food = require("../entities/food");

var gameUtils = require("../utils/gameUtils");

// AI蛇的最大数目
var ROBOT_SNAKE_MAX_COUNT = settings.readSetting("robot-snake-max-count");
// AI蛇产生的间隔（毫秒）
//var ROBOT_SNAKE_INTERVAL = settings.readSetting("robot-snake-interval") * 1000;
// AI蛇转向的平均间隔（秒）
var ROBOT_SNAKE_ROTATE_TIME = settings.readSetting("robot-snake-rotate-time");
// AI蛇找食物的平均间隔（秒）
var ROBOT_SNAKE_FIND_FOOD = settings.readSetting("robot-snake-find-food");
// AI蛇躲避碰撞的平均间隔（秒）
//var ROBOT_SNAKE_DODGE_CRASH = settings.readSetting("robot-snake-dodge-crash");
// AI蛇碰到死亡残留食物是否加速
//var ROBOT_ACCEL_DEAD_FOOD = settings.readSetting("robot-accel-dead-food");

var g_mapSize = settings.readSetting("map-size");
var g_mapRadius = settings.readSetting("map-radius");
var g_frameTime = settings.readSetting("frame", 30);
var aiNames = settings.readSetting("AI_NAME", []);
var g_centerPos = {xPos: g_mapSize / 2, yPos: g_mapSize / 2};
var ROBOT_LIVE_RANGE = settings.readSetting("robot-live-range");

var RobotService = {
    lastTime: new Date(),
    turnTime: new Date(),
    lastGeneSnakeTime: new Date(),
    geneSnakeStatus: true,
    robotSnakes: [],
    aiNameCache: new Set(),

    spawnRobots: function () {
        this.aiNameCache.clear();

        EventEmitter.emit('spawnRobots');
    },

    allocAiName: function () {
        var i = 0;
        var randomCount = 2 * aiNames.length;
        var snakeName = aiNames[Math.floor(Math.random() * aiNames.length)];
        while (this.aiNameCache.has(snakeName)) {
            i += 1;
            if (i >= randomCount) {
                break;
            }
            snakeName = aiNames[Math.floor(Math.random() * aiNames.length)];
        }

        if (i < randomCount) {
            this.aiNameCache.add(snakeName);
        }

        return snakeName;
    },

    delAiName: function (snakeName) {
        if (this.aiNameCache.has(snakeName)) {
            this.aiNameCache.delete(snakeName);
        }
    },

    destoryRobots: function () {
        var destoryIDs = [];
        for (var j = 0; j < this.robotSnakes.length; j++) {
            var snake = this.robotSnakes[j];
            if (snake && !snake.dead) {
                snake.dead = 1;
                destoryIDs.push(snake.snakeId);
            }
        }

        if (destoryIDs.length > 0) {
            for (var id of destoryIDs) {
                SnakeModel.delete(id);
            }
        }

        this.robotSnakes = [];
    },

    updateRobots: function (snakeArrayVisible) {
        var curTime = new Date();

        // 如果蛇的数量不足，每秒生成1条蛇
        var ROBOT_SNAKE_INTERVAL = netManager.getServerConfig().robot_born_time * 1000;
        if (SnakeModel.snakes.size < ROBOT_SNAKE_MAX_COUNT && this.geneSnakeStatus && curTime - this.lastGeneSnakeTime >= ROBOT_SNAKE_INTERVAL) {
            // console.info('Generate new snake.');
            this.lastGeneSnakeTime = curTime;
            var snakeName = this.allocAiName();
            var data = SnakeModel.getInitSnake(snakeName);
            SnakeModel.insert(data);
            var result = data;
            result.isRobot = 1;
            result.target.xPos = Math.random() - 0.5;
            result.target.yPos = Math.random() - 0.5;
            var angle = Math.atan2(result.target.yPos, result.target.xPos);
            var detalY = result.length * Math.sin(angle);
            var detalX = result.length * Math.cos(angle);
            result.tailPos.xPos = result.headPos.xPos - detalX;
            result.tailPos.yPos = result.headPos.yPos - detalY;
            this.robotSnakes.push(result);
            EventEmitter.emit('spawnRobots');
        }

        var dt = curTime - this.lastTime;
        this.lastTime = curTime;
        dt *= 0.001;

        var deadNum = 0;
        var robotSnakes = this.robotSnakes;
        //console.log("this.robotSnakes.length= " + robotSnakes.length);
        for (var j = 0; j < robotSnakes.length; j++) {
            var snake = robotSnakes[j];
            if (snake.dead) {
                deadNum++;
                continue;
            }

            var distX = snake.headPos.xPos - g_centerPos.xPos;
            var distY = snake.headPos.yPos - g_centerPos.yPos;
            var distS = Math.pow(distX, 2) + Math.pow(distY, 2);
            //can not in view sight
            var bHas = snakeArrayVisible.has(snake.snakeId);
            if (!bHas) {
                if (Math.round(Math.random() * 20) == 0) {
                    //console.log("update snake index= " + j);

                    if (distS > Math.pow(g_mapRadius, 2)) {
                        this.handleDeath(snake);
                    } else if (distS > Math.pow(ROBOT_LIVE_RANGE, 2)) {
                        snake.setTargetPos(g_centerPos.xPos - snake.headPos.xPos, g_centerPos.yPos - snake.headPos.yPos);
                    }
                    snake.updateMove(dt);
                }
            } else {  //only update snakes in sight
                var bTurn = false;
                if (Math.round(Math.random() * g_frameTime * ROBOT_SNAKE_ROTATE_TIME) == 0) {
                    bTurn = true;
                }

                var bEat = false;
                if (Math.round(Math.random() * g_frameTime * ROBOT_SNAKE_FIND_FOOD) == 0) {
                    bEat = true;
                }

                var bDodge = false;
                if (Math.round(Math.random() * g_frameTime * snake.dodgeInterval) == 0) {
                    bDodge = true;
                }

                if (Math.round(Math.random() * g_frameTime * 2) == 0) {
                    snake.speedDown();
                }

                if (distS > Math.pow(g_mapRadius, 2)) {
                    this.handleDeath(snake);
                } else if (distS > Math.pow(ROBOT_LIVE_RANGE, 2)) {
                    snake.setTargetPos(g_centerPos.xPos - snake.headPos.xPos, g_centerPos.yPos - snake.headPos.yPos);
                } else {
                    if (bEat) {
                        this.eatFood(snake);
                    }
                    if (bDodge) {
                        this.dodgeSnake(snake);
                    }
                }
                snake.updateMove(dt);
            }
        }
    },

    eatFood: function (snake) {
        var bFindDead = false;
        var nearestDeadFoodId = 0;
        var nearestOthFoodId = 0;
        var nearestDeadFoodDist = Math.pow(snake.screenX, 2) + Math.pow(snake.screenY, 2);
        //var nearestDeadFoodDist = snake.screenX * 1.4;
        var nearestOthFoodDist = nearestDeadFoodDist;
        var normalFoods = FoodModel.getFromBlockStore(snake.headPos.xPos, snake.headPos.yPos, snake.screenX, snake.screenY);
        normalFoods.forEach(foodId => {
            var food = FoodModel.getById(foodId);
            if (food) {
                var distPow = Math.pow(Math.round(snake.headPos.xPos - food.position.xPos), 2) + Math.pow(Math.round(snake.headPos.yPos - food.position.yPos), 2);
                if (food.foodType == Food.Type.AFTER_DEAD) {
                    if (distPow < nearestDeadFoodDist) {
                        nearestDeadFoodDist = distPow;
                        nearestDeadFoodId = foodId;
                    }
                    bFindDead = true;
                } else {
                    if (distPow < nearestOthFoodDist) {
                        nearestOthFoodDist = distPow;
                        nearestOthFoodId = foodId;
                    }
                }
            }
        });

        var targetFoodId = (nearestDeadFoodId > 0) ? nearestDeadFoodId : nearestOthFoodId;
        if (targetFoodId) {
            var targetFood = FoodModel.getById(targetFoodId);
            if (targetFood) {
                snake.setTargetPos(targetFood.position.xPos - snake.headPos.xPos, targetFood.position.yPos - snake.headPos.yPos);
            }

            var bAcc = (Math.round(Math.random() * 600) <= snake.accProp) ? 1 : 0;
            if (bAcc) {
                if (bFindDead) {
                    snake.speedUp();
                } else {
                    snake.speedDown();
                }
            }
        }
    },

    filterByAABB: function (moveToPos, radiusSize, othSnake) {
        // 根据蛇头的包围盒进行可见裁减
        var othAABB = othSnake.getAABB();
        var selfView = {
            xMin: moveToPos.xPos - radiusSize,
            xMax: moveToPos.xPos + radiusSize,
            yMin: moveToPos.yPos - radiusSize,
            yMax: moveToPos.yPos + radiusSize
        };

        if (othAABB.xMax < selfView.xMin || othAABB.xMin > selfView.xMax ||
            othAABB.yMax < selfView.yMin || othAABB.yMin > selfView.yMax) {
            return false;
        }

        return true;
    },

    mayCrash: function (moveToPos, moveDist, othSnake) {

        if (!this.filterByAABB(moveToPos, moveDist, othSnake)) {
            return false;
        }

        var radiusPow = moveDist * moveDist;
        var othBodyPoints = gameUtils.getInterpolatePoints(othSnake.getBodyPoints(), othSnake.width);
        for (var i = 0; i < othBodyPoints.length; i++) {
            var detalX = moveToPos.xPos - othBodyPoints[i].xPos;
            var detalY = moveToPos.yPos - othBodyPoints[i].yPos;
            var distPow = Math.pow(detalX, 2) + Math.pow(detalY, 2);
            if (distPow <= radiusPow) {
                return true;
            }
        }

        return false;
    },

    dodgeSnake: function (snakeSelf) {
        var bMayCrash = false;

        var moveDist = snakeSelf.speed;
        var angle0 = Math.atan2(snakeSelf.dirPos.yPos, snakeSelf.dirPos.xPos);
        var detalY0 = moveDist * Math.sin(angle0);
        var detalX0 = moveDist * Math.cos(angle0);
        var moveToPos = {
            xPos: snakeSelf.headPos.xPos + detalX0,
            yPos: snakeSelf.headPos.yPos + detalY0
        };

        for (let snake of SnakeModel.snakes.values()) {
            if (snake.snakeId !== snakeSelf.snakeId) {
                if (this.mayCrash(moveToPos, moveDist, snake)) {
                    bMayCrash = true;
                    break;
                }
            }
        }

        if (bMayCrash) {
            snakeSelf.setTargetPos(-1 * snakeSelf.dirPos.xPos, -1 * snakeSelf.dirPos.yPos);
            snakeSelf.speedDown();
        }
    },

    handleDeath: function (snake) {
        snake.dead = 1;
        this.delAiName(snake.name);
        SnakeModel.delete(snake.snakeId);
    },

    setRobotAIByLength: function (length) {
        for (var j = 0; j < this.robotSnakes.length; j++) {
            var snake = this.robotSnakes[j];
            if (snake && !snake.dead) {
                snake.updateAIByLength(length);
            }
        }
    }

};

EventEmitter.on('TimeStart', () => {
    RobotService.geneSnakeStatus = true;
    console.log("spawn robots");
    RobotService.spawnRobots();
});

EventEmitter.on('TimeOver', () => {
    RobotService.geneSnakeStatus = false;
    setTimeout(() => {
        console.log("destroy robots");
        RobotService.destoryRobots();
    }, 100);
});


module.exports = RobotService;
