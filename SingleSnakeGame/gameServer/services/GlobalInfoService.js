var gameUtils = require("../utils/gameUtils");
var settings = require("../utils/settings");
var FoodModel = require("../models/FoodModel");
var SnakeModel = require("../models/SnakeModel");
var Constants = require('../utils/constants')
//var CostTimeInfo = require('../utils/timeUtils.js');
var _ = require("underscore");
var Food = require("../entities/food");

var MAP_RADIUS = settings.readSetting("map-radius");
var MAP_BORDER = settings.readSetting("map-border");

//var updateFoodCostTime = new CostTimeInfo('UpdateFindFood');
//var updateSnakeCostTime = new CostTimeInfo('UpdateFindSnake');

var GlobalInfoService = {

    filterByAABB: function (snakeSelf, othSnake) {
        // 根据蛇的包围盒进行可见裁减
        var othAABB = othSnake.getAABB();
        var selfView = {
            xMin: snakeSelf.headPos.xPos - snakeSelf.screenX,
            xMax: snakeSelf.headPos.xPos + snakeSelf.screenX,
            yMin: snakeSelf.headPos.yPos - snakeSelf.screenY,
            yMax: snakeSelf.headPos.yPos + snakeSelf.screenY
        };

        if (othAABB.xMax < selfView.xMin || othAABB.xMin > selfView.xMax ||
            othAABB.yMax < selfView.yMin || othAABB.yMin > selfView.yMax) {
            return false;
        }

        return true;
    },

    canSeeSnake: function (snakeSelf, othSnake) {
        var canSee = false;

        if (!this.filterByAABB(snakeSelf, othSnake)) {
            return false;
        }

        // 插入点进行更精确的判断
        var othBodyPoints = gameUtils.getInterpolatePoints(othSnake.getBodyPoints(), othSnake.width);
        for (var i = 0; i < othBodyPoints.length; i++) {
            var detalX = snakeSelf.headPos.xPos - othBodyPoints[i].xPos;
            var detalY = snakeSelf.headPos.yPos - othBodyPoints[i].yPos;
            canSee = canSee || ((Math.abs(detalX) < snakeSelf.screenX) && (Math.abs(detalY) < snakeSelf.screenY));
            if (canSee) {
                return true;
            }
        }

        return canSee;
    },

    filterMoveFood: function (snakeSelf, foodIds) {
        var headPos = snakeSelf.headPos;
        var result = [];
        for (var foodId of foodIds) {
            var food = FoodModel.getById(foodId);
            if (food) {
                if ((Math.abs(headPos.xPos - food.position.xPos) <= snakeSelf.screenX) &&
                    ( Math.abs(headPos.yPos - food.position.yPos) <= snakeSelf.screenY)) {
                    result.push(foodId);
                }
            }
        }
        return result;
    },

    updateVisibleFoods: function (PacketHandler) {

        var snakeSelf = PacketHandler.getSnake();
        if (!snakeSelf) {
            //console.log("error no found self");
            return;
        }

        var normalFoods = FoodModel.getFromBlockStore(snakeSelf.headPos.xPos, snakeSelf.headPos.yPos, snakeSelf.screenX, snakeSelf.screenY);
        var movableFoods = FoodModel.getMovableFoods();
        var movFood = this.filterMoveFood(PacketHandler.getSnake(), movableFoods);
        var visFoods = normalFoods;
        visFoods.sort();
        PacketHandler.newAddFoods = _.difference(visFoods, PacketHandler.visibleFoods);
        PacketHandler.newAddFoods = PacketHandler.newAddFoods.concat(movFood);
        PacketHandler.visibleFoods = visFoods;
    },

    updateVisibleSnakes: function (PacketHandler) {

        var snakeSelf = PacketHandler.getSnake();
        if (!snakeSelf) {
            return;
        }
        PacketHandler.newAddSnakes = [];
        PacketHandler.oldAddSnakes = [];
        var oldVis = PacketHandler.visibleSnakes;
        var newVis = new Set();
        SnakeModel.snakes.forEach(snake => {
            if (snake.snakeId === snakeSelf.snakeId) {
                return;
            }
            if (this.canSeeSnake(snakeSelf, snake)) {
                if (!oldVis.has(snake.snakeId)) {
                    PacketHandler.newAddSnakes.push(snake.snakeId);
                    newVis.add(snake.snakeId);
                } else {
                    PacketHandler.oldAddSnakes.push(snake.snakeId);
                    newVis.add(snake.snakeId);
                }
            }
        });
        PacketHandler.visibleSnakes = newVis;
    },

    updateVisible: function (PacketHandler) {
        if (!PacketHandler) {
            return;
        }

        //updateFoodCostTime.begin();
        this.updateVisibleFoods(PacketHandler);
        //updateFoodCostTime.end();

        //updateSnakeCostTime.begin();
        this.updateVisibleSnakes(PacketHandler);
        //updateSnakeCostTime.end();
    },

    getSnakeInfo: function (snake, bGlobal) {
        var selfSnakeInfo = {};
        selfSnakeInfo.snakeId = snake.snakeId;
        selfSnakeInfo.width = Math.round(snake.width);
        selfSnakeInfo.energy = snake.energy;
        selfSnakeInfo.dirPos = snake.dirPos;
        var isProtected = snake.isProtected() ? 1 : 0;
        selfSnakeInfo.statusFlag = (snake.accelerate << Constants.StatusFlag.STATUS_ACCELERATE);
        selfSnakeInfo.statusFlag |= (isProtected << Constants.StatusFlag.STATUS_PROTECTION);
        if (bGlobal) {
            selfSnakeInfo.bodyPoints = snake.getBodyPointInfo();
            selfSnakeInfo.name = snake.name;
            selfSnakeInfo.skinId = snake.skinId;
            selfSnakeInfo.increment = 0;
        } else {
            selfSnakeInfo.bodyPoints = snake.getIncrementInfo();
            selfSnakeInfo.increment = snake.getKeyCount();
        }

        return selfSnakeInfo;
    },

    getData: function (PacketHandler, bGlobal) {

        if (!PacketHandler) {
            return;
        }

        var snakeSelf = PacketHandler.getSnake();
        if (!snakeSelf) {
            return;
        }

        //组合GlobalInfo, push给客户端
        var globalData = {};
        if (bGlobal) {
            globalData.mapRadius = MAP_RADIUS;
            globalData.mapBorder = MAP_BORDER;
        }

        globalData.viewSize = Math.round(snakeSelf.getViewScale());

        globalData.snakeSelf = this.getSnakeInfo(snakeSelf, bGlobal);

        globalData.snakeOthers = [];
        PacketHandler.newAddSnakes.forEach(snakeId => {
            var snake = SnakeModel.getById(snakeId);
            globalData.snakeOthers.push(this.getSnakeInfo(snake, true));
        });

        PacketHandler.oldAddSnakes.forEach(snakeId => {
            var snake = SnakeModel.getById(snakeId);
            globalData.snakeOthers.push(this.getSnakeInfo(snake, false));

        });

        globalData.foodInfo = [];
        PacketHandler.newAddFoods.forEach(foodId => {
            var food = FoodModel.getById(foodId);
            if (food) {
                globalData.foodInfo.push({
                    foodType: food.foodType,
                    foodId: food.foodId,
                    radius: food.radius,
                    color: food.color,
                    position: food.position
                });
            }
        });

        return globalData;
    }
};

module.exports = GlobalInfoService;
