/*  
 * Class:         Snake
 * Description:   Entity class for the players snake.
 * Created:       15.04.2016
 * Last change:   15.04.2016
 * Collaborators: circa94
 */

var Consts = require("../utils/constants");
var settings = require("../utils/settings");
var gameUtils = require("../utils/gameUtils");
var mathUtils = require("../utils/mathUtils");
var configManager = require("../config/ConfigMgr");
var FoodModel = require('../models/FoodModel');
var EventEmitter = require('../utils/eventEmitter');
var snakeCounter = 0;

var SNAKE_DEFAULT_LENGTH = settings.readSetting("snake-length");
var SNAKE_DEFAULT_WIDTH = settings.readSetting("snake-width");
var SNAKE_DEFAULT_ENERGY = settings.readSetting("snake-energy");
var SNAKE_DEFAULT_SPEED = settings.readSetting("snake_speed");
var SNAKE_SKINID_RANGE = settings.readSetting("snake-skinId");
var DEFAULT_VIEW_RADIUS = settings.readSetting("view-radius");
var BORN_SNAKE_GOD_TIME = settings.readSetting("snake-born-god-time") * 1000;
var SNAKE_VIEW_OFFSET = settings.readSetting("view-offset", 30);

//var SNAKE_ROTATE_SPEED = settings.readSetting("rotate-speed") * Math.PI / 180;
//var ROTATE_ADD_TIMES = settings.readSetting("rotate-times");
var ACCEL_NEED_ENERGY = settings.readSetting("accel-energy");
//var ACCEL_ADD_TIMES = settings.readSetting("accel-times");
var ACCEL_ENERGY_DEC = settings.readSetting("energy-dec");

var MULTI_KILL_TIME = settings.readSetting("multi_kill_time");
var MULTI_KILL_COUNT = settings.readSetting("multi_kill_count");

var PI_ANGLE = Math.PI / 180;
/*
 * y = 100% + (x-26) / 10 * 5%
 */
var getViewSize = function (defaultSize, width) {
    return defaultSize * Math.pow(width / 26, 0.42);
};

var getScreenSize = function (size) {
    return size / 2;
};

var getRotateSpeed = function (width, snakeID) {
    var SNAKE_ROTATE_SPEED = netManager.getServerConfig(snakeID).rotate_speed * PI_ANGLE;
    return SNAKE_ROTATE_SPEED * (1.1109 - 0.0042 * width);
};

function Snake(username) {
    snakeCounter += 2;

    this.snakeId = snakeCounter;
    this.skinId = mathUtils.getRandomInt(1, SNAKE_SKINID_RANGE);
    this.name = username;
    this.length = SNAKE_DEFAULT_LENGTH;
    this.width = SNAKE_DEFAULT_WIDTH;
    this.energy = SNAKE_DEFAULT_ENERGY;
    this.speed = SNAKE_DEFAULT_SPEED;
    this.screenX = DEFAULT_VIEW_RADIUS;
    this.screenY = this.screenX;
    this.defaultSX = this.screenX;
    this.defaultSY = this.screenY;
    this.viewScale = 1;
    this.accelerate = 0;
    this.angle = 0;
    this.level = 1;
    this.dead = 0;
    this.nodeAddNum = 0;
    this.nodeDelNum = 0;
    this.addLength = 0;
    this.bornTime = Date.now();
    this.spawnFoodTime = 0;
    this.beginRotate = 0;
    this.isRobot = 0;
    this.multiKillCount = 0;
    this.lastKillTime = 0;
    this.dodgeInterval = 2;
    this.accProp = 50;

    var pos = gameUtils.getRandomSpawnPoint();

    this.target = {
        xPos: 1,
        yPos: 0
    };

    this.dirPos = {
        xPos: 1,
        yPos: 0
    };

    this.headPos = {
        xPos: pos.x,
        yPos: pos.y
    };

    this.tailPos = {
        xPos: pos.x - SNAKE_DEFAULT_LENGTH,
        yPos: pos.y
    };

    this.aabb = {
        xMin: pos.x - SNAKE_DEFAULT_LENGTH,
        yMin: pos.y,
        xMax: pos.x,
        yMax: pos.y
    }

    this.keyNodes = [];

    this.bodyPoints = [];
    this.bodyPoints.push(this.headPos);
    this.bodyPoints.push(this.tailPos);
}

Snake.resetId = function () {
    snakeCounter = 0;
};

Snake.prototype.clear = function () {
    this.nodeAddNum = 0;
    this.nodeDelNum = 0;
};

Snake.prototype.isDead = function () {
    return this.dead;
}

Snake.prototype.isProtected = function () {
    var curTime = Date.now();
    if (curTime - this.bornTime > BORN_SNAKE_GOD_TIME) {
        return false;
    }
    return true;
};

Snake.prototype.setScreenParams = function (width, height) {
    this.defaultSX = getScreenSize(width);
    this.defaultSY = getScreenSize(height);
    this.setViewSize();
};

Snake.prototype.getViewScale = function () {
    return this.viewScale;
}

Snake.prototype.setViewSize = function () {
    var viewSX = getViewSize(this.defaultSX, this.width);
    var viewSY = getViewSize(this.defaultSY, this.width);
    this.viewScale = viewSX / this.defaultSX * 10000;
    this.screenX = viewSX + SNAKE_VIEW_OFFSET;
    this.screenY = viewSY + SNAKE_VIEW_OFFSET;
}

Snake.prototype.getHeadPos = function () {
    return this.headPos;
};

Snake.prototype.getTailPos = function () {
    return this.tailPos;
};

Snake.prototype.getEnergy = function () {
    return this.energy;
};

Snake.prototype.getBodyPoints = function () {
    return this.bodyPoints;
};

Snake.prototype.getAABB = function () {
    return this.aabb;
};

Snake.prototype.getHotZonePos = function (hotDist) {
    var hotPos = {};
    var angle = Math.atan2(this.dirPos.yPos, this.dirPos.xPos);
    var detalY = hotDist * Math.sin(angle);
    var detalX = hotDist * Math.cos(angle);
    hotPos.xPos = this.headPos.xPos + detalX;
    hotPos.yPos = this.headPos.yPos + detalY;
    return hotPos;
}

Snake.prototype.addKillCount = function (count, killedName) {
    var curTime = Date.now();
    if (this.lastKillTime) {
        if (curTime - this.lastKillTime >= MULTI_KILL_TIME) {
            this.multiKillCount = 0;
        }
    }
    this.multiKillCount += count;
    this.lastKillTime = curTime;
    if (this.multiKillCount >= MULTI_KILL_COUNT) {
        var callBoardInfo = {};
        callBoardInfo.boardType = Consts.BoardInfoType.MULTI_KILL;
        callBoardInfo.killerName = this.name;
        //callBoardInfo.killedName = killedName;
        callBoardInfo.killCount = this.multiKillCount;
        EventEmitter.emit('CallBoardInfo', callBoardInfo);
    }
}

Snake.prototype.addEnergy = function (energy) {
    this.energy = mathUtils.floatToFixed1(this.energy + energy);
    var configData = configManager.getData(this.level);
    if (configData && this.energy > configData.energy) {
        var newData = configManager.findCeilData(this.level, this.energy);
        if (newData && newData.level > this.level) {
            this.level = newData.level;
            this.speed = newData.speed;
            this.growup(newData.length - this.length, newData.width - this.width);
        }
    }

    configData = configManager.getAIData(this.energy);
    if (configData) {
        //this.dodgeInterval = configData.dodgeInterval;
        //console.log("this.dodgeInterval = " + this.dodgeInterval);
        this.accProp = configData.accProp;
        //console.log("this.accProp = " + this.accProp);
    }
};

Snake.prototype.updateAIByLength = function (length) {
    var configData = configManager.getAIData(length);
    if (configData) {
        this.dodgeInterval = configData.dodgeInterval;
        //console.log("this.dodgeInterval = " + this.dodgeInterval);
    } else {
        //console.log("configData==null, this.dodgeInterval = " + this.dodgeInterval);
    }
};

Snake.prototype.decEnergy = function (energy) {
    this.energy = mathUtils.floatToFixed1(this.energy - energy);
    if (this.energy < SNAKE_DEFAULT_ENERGY) {
        this.energy = SNAKE_DEFAULT_ENERGY;
    }
    var configData = configManager.getData(this.level);
    if (configData && this.energy < configData.energy) {
        var newData = configManager.findFloorData(this.level, this.energy);
        if (newData && newData.level < this.level) {
            this.level = newData.level;
            this.speed = newData.speed;
            this.growdown(this.length - newData.length, this.width - newData.width);
        }
    }
};

Snake.prototype.spawnPoint = function (x, y) {
    var newPoint = {xPos: x, yPos: y};
    this.keyNodes.push(newPoint);
    this.nodeAddNum = 1;
};

Snake.prototype.destoryPoint = function () {
    if (this.keyNodes.length > 0) {
        this.keyNodes.splice(0, 1);
        this.nodeDelNum++;
    }
};

Snake.prototype.getKeyCount = function () {
    return this.keyNodes.length + 2;
};

Snake.prototype.growup = function (changeLength, changeWidth) {
    this.length += changeLength;
    this.addLength += changeLength;
    this.width += changeWidth;
    this.setViewSize();
};

Snake.prototype.growdown = function (changeLength, changeWidth) {
    this.length -= changeLength;
    this.addLength -= changeLength;
    if (this.length < SNAKE_DEFAULT_LENGTH) {
        this.length = SNAKE_DEFAULT_LENGTH;
    }
    if (this.width > SNAKE_DEFAULT_WIDTH) {
        this.width -= changeWidth;
        if (this.width < SNAKE_DEFAULT_WIDTH) {
            this.width = SNAKE_DEFAULT_WIDTH;
        }
        this.setViewSize();
    }
};

Snake.prototype.speedUp = function () {
    if (!this.accelerate) {
        this.accelerate = 1;
    }
};

Snake.prototype.speedDown = function () {
    if (this.accelerate) {
        this.accelerate = 0;
    }
};

Snake.prototype.transPoints = function () {
    this.bodyPoints = [];
    this.bodyPoints.push(this.headPos);
    if (this.keyNodes.length > 0) {
        for (var j = this.keyNodes.length - 1; j >= 0; j--) {
            this.bodyPoints.push(this.keyNodes[j]);
        }
    }
    this.bodyPoints.push(this.tailPos);
};

Snake.prototype.getBodyPointInfo = function () {
    var pointInfo = [];
    for (var i = 0; i < this.bodyPoints.length; i++) {
        pointInfo.push({
            xPos: this.bodyPoints[i].xPos,
            yPos: this.bodyPoints[i].yPos,
            addNode: 0
        });
    }

    return pointInfo;
};

Snake.prototype.getIncrementInfo = function () {
    var pointInfo = [];
    pointInfo.push({
        xPos: this.headPos.xPos,
        yPos: this.headPos.yPos,
        addNode: this.nodeAddNum
    });
    pointInfo.push({
        xPos: this.tailPos.xPos,
        yPos: this.tailPos.yPos,
        addNode: (this.nodeDelNum == 0) ? 0 : -this.nodeDelNum
    });

    return pointInfo;
};

Snake.prototype.updateAABB = function () {
    for (var i = 0, len = this.bodyPoints.length; i < len; i++) {
        var point = this.bodyPoints[i];

        if (point.xPos < this.aabb.xMin) {
            this.aabb.xMin = point.xPos;
        } else if (point.xPos > this.aabb.xMax) {
            this.aabb.xMax = point.xPos;
        }

        if (point.yPos < this.aabb.yMin) {
            this.aabb.yMin = point.yPos;
        } else if (point.yPos > this.aabb.yMax) {
            this.aabb.yMax = point.yPos;
        }
    }
};

Snake.prototype.setTargetPos = function (targetX, targetY) {
    var len = Math.sqrt(targetX * targetX + targetY * targetY);
    if (len > 0.0001) {
        this.target.xPos = targetX / len;
        this.target.yPos = targetY / len;
    } else {
        this.target.xPos = targetX;
        this.target.yPos = targetY;
    }
    var angle1 = Math.atan2(this.dirPos.yPos, this.dirPos.xPos);
    var angle2 = Math.atan2(this.target.yPos, this.target.xPos);
    if (angle2 - angle1 > Math.PI) {
        this.angle = (angle2 - angle1) - 2 * Math.PI;
    } else if (angle2 - angle1 < -Math.PI) {
        this.angle = 2 * Math.PI - (angle1 - angle2);
    } else {
        this.angle = angle2 - angle1;
    }
};

Snake.prototype.updateMove = function (dt) {
    this.clear();

    var speed = this.speed * netManager.getServerConfig(this.snakeId).speed_times;
    //var rotate = getRotateSpeed(this.width);
    var rotate = getRotateSpeed(this.width, this.snakeId); //only for test
    var acc_speed_times = netManager.getServerConfig(this.snakeId).acc_times;
    var acc_rotate_times = netManager.getServerConfig(this.snakeId).rotate_times;

    if (this.accelerate == 1) {
        if (this.getEnergy() > ACCEL_NEED_ENERGY) {
            this.decEnergy(ACCEL_ENERGY_DEC * dt);
            speed *= acc_speed_times;
            rotate *= acc_rotate_times;

            //var curTime = Date.now();
            this.spawnFoodTime += dt;
            if (this.spawnFoodTime > 0.1) {
                FoodModel.generateSpeedFood(this);
                this.spawnFoodTime = 0;
            }
        } else {
            this.accelerate = 0;
        }
    }

    var moveDist = speed * dt;
    var rotateD = rotate * dt;

    //计算蛇头旋转
    var rotateS = 0;
    if (this.angle > 0) {
        if (this.angle - rotateD > 0) {
            this.angle -= rotateD;
            rotateS = rotateD;
        } else {
            rotateS = this.angle;
            this.angle = 0;
        }
    } else if (this.angle < 0) {
        if (this.angle + rotateD < 0) {
            this.angle += rotateD;
            rotateS = -rotateD;
        } else {
            rotateS = this.angle;
            this.angle = 0;
        }
    }

    //计算蛇头移动
    if (rotateS != 0) {
        var cosVal = Math.cos(rotateS);
        var sinVal = Math.sin(rotateS);
        var x1 = this.dirPos.xPos * cosVal - this.dirPos.yPos * sinVal;
        var y1 = this.dirPos.xPos * sinVal + this.dirPos.yPos * cosVal;
        this.dirPos.xPos = x1;
        this.dirPos.yPos = y1;

        var widthScale = this.width / SNAKE_DEFAULT_WIDTH;
        if (++this.beginRotate >= Math.round(widthScale)) {
            this.spawnPoint(this.headPos.xPos, this.headPos.yPos);
            this.beginRotate = 0;
        }
    } else {
        this.dirPos.xPos = this.target.xPos;
        this.dirPos.yPos = this.target.yPos;
    }

    var angle0 = Math.atan2(this.dirPos.yPos, this.dirPos.xPos);
    var detalY0 = moveDist * Math.sin(angle0);
    var detalX0 = moveDist * Math.cos(angle0);
    this.headPos.xPos += detalX0;
    this.headPos.yPos += detalY0;

    // 计算蛇的尾部移动
    var prePart = this.headPos;
    var leftDist = moveDist - this.addLength;
    this.addLength = 0;
    if (leftDist >= 0) {
        while (this.keyNodes.length > 0) {
            var preNode = this.keyNodes[0];
            var dist1 = Math.pow((this.tailPos.xPos - preNode.xPos), 2) + Math.pow((this.tailPos.yPos - preNode.yPos), 2);
            if (dist1 < leftDist * leftDist) {
                this.tailPos.xPos = preNode.xPos;
                this.tailPos.yPos = preNode.yPos;
                leftDist -= Math.sqrt(dist1);
                // 清除无效关键点
                this.destoryPoint();
            } else {
                prePart = preNode;
                break;
            }
        }

    } else {

        if (this.keyNodes.length > 0) {
            prePart = this.keyNodes[0];
        }
    }

    var angle1 = Math.atan2(prePart.yPos - this.tailPos.yPos, prePart.xPos - this.tailPos.xPos);
    var detalY1 = leftDist * Math.sin(angle1);
    var detalX1 = leftDist * Math.cos(angle1);
    this.tailPos.xPos += detalX1;
    this.tailPos.yPos += detalY1;

    this.transPoints();
    this.updateAABB();
};

module.exports = Snake;
