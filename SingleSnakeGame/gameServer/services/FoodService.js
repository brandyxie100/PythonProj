'use strict';
var CollisionService = require('./CollisionService');
var SnakeService = require('./SnakeService');
var Food = require("../entities/food");
var SnakeModel = require('../models/SnakeModel');
var FoodModel = require("../models/FoodModel");
var EventEmitter = require('../utils/eventEmitter');
var settings = require("../utils/settings");
var mathUtils = require("../utils/mathUtils");
var _ = require("underscore");

var g_mapSize = settings.readSetting("map-size");
var HALF_MAP_SIZE = g_mapSize / 2;
var g_mapRadius = settings.readSetting("map-radius");
var g_foodArea = settings.readSetting("food-area");
var g_max = settings.readSetting("max-normal-food", 0);
var g_gfp = settings.readSetting("growing-food-portion", 0);
//var g_maxMovableFood = settings.readSetting("max-movable-food", 0);
//var SPAWN_NORMAL_FOOD_PERSEC = settings.readSetting("spawn-normal-food-persec", 100);

var isInit = false;

var FoodService = {
    init: function () {
        if (!isInit) {
            this.currBasicFood = 0;
            this.currGrowFood = 0;
            this.currMovableFood = 0;
            FoodModel.init();
            isInit = true;
        }
        else {
            console.info("Food service already initialized!");
        }
    },

    updateFood: function () {   // interval: 1 sec
        this.currBasicFood = FoodModel.basic_food_num;
        this.currGrowFood = FoodModel.growFoods.size;
        this.currMovableFood = FoodModel.movableFoods.size;

        // 成长节点
        var food;
        for (var id of FoodModel.growFoods) {
            food = FoodModel.getById(id);
            if (food.energy < 3.0) {
                food.energy += 0.05;
                food.radius += 0.05;
            }
        }

        // 移除超出范围的食物
        var p;
        for (var id of FoodModel.movableFoods) {
            food = FoodModel.getById(id);
            if (this.isOutLimitedArea(food.position)) {
                // 超出食物区域
                FoodModel.deleteMoveFood(food);
                console.log("deleteMoveFood");
                continue;
            }

            // 计算食物的方向
            p = mathUtils.getRandomInt(1, 4);
            if (p == 4 || p == 2) {
                food.velocity = {x: mathUtils.getRandomInt(-180, 180), y: mathUtils.getRandomInt(-180, 180)};
            }
        }
    },

    spawnFood: function () {    // interval: 1 sec
        this.currBasicFood = FoodModel.basic_food_num;
        this.currGrowFood = FoodModel.growFoods.size;
        this.currMovableFood = FoodModel.movableFoods.size;

        var max = g_max;
        var gfp = g_gfp;
        var config = netManager.getServerConfig();
        var maxMovableFood = config.m_food_max_num;
        //var maxMovableFood = g_maxMovableFood;
        var maxBasicFood = max * (1 - gfp);
        var maxGrowFood = max * gfp;


        // 每秒基础型能量点数量：100
        //var amount = SPAWN_NORMAL_FOOD_PERSEC;
        var amount = netManager.getServerConfig().n_food_per_sec;
        //console.log("spawnNormalBasicFood= ", amount);
        var unitBasicFood = amount * (1 - gfp);
        if (maxBasicFood - this.currBasicFood > unitBasicFood) {
            //console.log("spawnNormalBasicFood", unitBasicFood);
            FoodModel.generateNormalFood(Food.Type.BASIC, unitBasicFood);
        }

        var unitGrowFood = amount * gfp;
        if (maxGrowFood - this.currGrowFood > unitGrowFood) {
            //console.log("spawnNormalGrowFood", unitGrowFood);
            FoodModel.generateNormalFood(Food.Type.GROWING, unitGrowFood);
        }

        // 每秒移动型能量点刷新数量：2
        var unitMovableFood = config.m_food_fresh;
        if (maxMovableFood - this.currMovableFood > unitMovableFood) {
            //console.log("spawnMovableFood", unitMovableFood);
            FoodModel.generateMovableFood(Food.Type.MOVABLE, unitMovableFood);
        }
    },

    isOutLimitedArea: function (pos) {
        var distX = pos.xPos - HALF_MAP_SIZE;
        var distY = pos.yPos - HALF_MAP_SIZE;
        var radius = g_mapRadius + 50;
        if (distX * distX + distY * distY >= radius * radius) {
            return true;
        }
        return false;
    },

    // 更新移动的食物
    updateMovableFoodInfo: function (dt, collision) {   // interval: 25 milliseconds
        // 食物运动
        var decSpeed;
        var angle;
        var speedX;
        var speedY;
        var moveSpeed = netManager.getServerConfig().m_food_speed;
        for (var id of FoodModel.getMovableFoods()) {
            var food = FoodModel.getById(id);

            if (mathUtils.almostEqual(food.velocity.x, 0)) food.velocity.x = 0;
            if (mathUtils.almostEqual(food.velocity.y, 0)) food.velocity.y = 0;

            if (food.velocity.x != 0 && food.velocity.y != 0) { // on moving...
                decSpeed = moveSpeed * dt;
                angle = Math.atan2(food.velocity.y, food.velocity.x);
                speedX = decSpeed * Math.cos(angle);
                speedY = decSpeed * Math.sin(angle);
                food.position.xPos -= speedX;
                food.position.yPos -= speedY;

                //restrict position in limited area
                if (this.isOutLimitedArea(food.position)) {
                    food.position.xPos += speedX;
                    food.position.yPos += speedY;
                    //console.log("food is out of range!");
                }
            }
        }

        // 食物躲避
        // {foodId: [snakeId, ...], ...}
        var nearFood = collision.nearMovedFood;
        nearFood.forEach(function (vals, foodId) {
            var snakeId = vals[0];
            var food = FoodModel.getById(foodId);
            var snake = SnakeModel.getById(snakeId);
            if (food && snake) {
                var magic = (foodId % 100 + snakeId % 100) / 200;
                food.velocity.x = -snake.dirPos.xPos * magic;
                food.velocity.y = -snake.dirPos.yPos * (1 - magic);
            }
        });
    },

    // 更新被吃的食物信息
    updateEatenFoodInfo: function (collision) {   // interval: 30 milliseconds
        var eatenFood = collision.eatenFood;
        var eatenFoodId = [];
        this.eatenFoodInfo = [];

        var self = this;
        eatenFood.forEach(function (foodIds, key) {
            eatenFoodId = eatenFoodId.concat(foodIds);
            self.eatenFoodInfo.push({snakeId: key, eatFoods: foodIds});
        });

        SnakeService.updateEatInfo(this.eatenFoodInfo);
        FoodModel.deleteFood(eatenFoodId);

    },

    // 获取玩家视野范围内吃食物信息
    getEatFoodInfo: function (PacketHandler) {
        if (!PacketHandler) {
            console.log("FoodService: null == PacketHandler");
            return;
        }

        var snakeSelf = PacketHandler.getSnake();
        if (!snakeSelf) {
            console.log("FoodService: null == snakeSelf");
            return;
        }
        // 返回全量被吃食物信息，已经做过裁切所以差别不大
        return this.eatenFoodInfo;

        //var eatFoodInfo = [];
        //this.eatenFoodInfo.forEach(eatInfo => {
        //    if (eatInfo.snakeId == snakeSelf.snakeId) {
        //        eatFoodInfo.push(eatInfo);
        //    }
        //    else {
        //        var foodIds = eatInfo.eatFoods;
        //        for (var i = 0; i < foodIds.length; i++) {
        //            if (_.indexOf(PacketHandler.visibleFoods, foodIds[i], true)) {
        //                eatFoodInfo.push(eatInfo);
        //                break;
        //            }
        //        }
        //    }
        //});
        //return eatFoodInfo;
    },

    clearAllFood: function () {
        if (isInit) {
            FoodModel.clearAllFood();
            isInit = false;
        }
        else {
            console.info("food service clear but not initialized!");
        }
    }
};

EventEmitter.on('TimeStart', () => {
    FoodService.init();
});

EventEmitter.on('TimeOver', () => {
    FoodService.clearAllFood();
});

FoodService.init();

module.exports = FoodService;
