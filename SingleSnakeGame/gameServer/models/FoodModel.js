'use strict';
var Model = require('./Model');
var Food = require("../entities/food");
var settings = require("../utils/settings");
var mathUtils = require("../utils/mathUtils");
var gameUtils = require("../utils/gameUtils");

var name = 'Food';

var MAP_SIZE = settings.readSetting("map-size");
var HALF_MAP_SIZE = MAP_SIZE / 2;
var g_foodArea = settings.readSetting("food-area");
var FOOD_BLOCK_NUM = settings.readSetting("food-block-num", 30);

var g_foodColors = settings.readSetting("food-colors");
var g_foodSize = settings.readSetting("food-size");
var FOOD_DEPRECIATE = settings.readSetting("food-depreciate");
var FOOD_GAP_RAT = settings.readSetting("food-gap-rat");
var FOOD_POS_OFFSET = settings.readSetting("food-pos-offset");

class FoodModel {
    constructor() {
        this.basic_food_num = 0;
        //this.genSpeedFoodTimer = new Map();    // map snake's id to timer
        this.blockNum = FOOD_BLOCK_NUM + 1;
        this.blockSize = MAP_SIZE / FOOD_BLOCK_NUM;
        this.blockStore = [];         // 普通食物分块数组
        this.movableFoods = new Set();       // 可移动食物数组
        this.growFoods = new Set();
        this.foods = new Map();
    }

    /**
     * @method 产生初始食物
     */
    init() {
        // init block at first
        this.initBlockStore();

        // currently all foods are generating and sending. later we should only send the food in players range
        var start = settings.readSetting("start-normal-food", 0);
        var gfp = settings.readSetting("growing-food-portion", 0);
        var startBasicFood = start * (1 - gfp);
        var startGrowFood = start * gfp;
        var startMovableFood = settings.readSetting("start-movable-food", 0);

        this.generateNormalFood(Food.Type.BASIC, startBasicFood);

        this.generateNormalFood(Food.Type.GROWING, startGrowFood);

        this.generateMovableFood(Food.Type.MOVABLE, startMovableFood);
    }

    initBlockStore() {
        for (var i = 0; i < this.blockNum; ++i) {
            var arr = [];
            for (var j = 0; j < this.blockNum; ++j) {
                arr[j] = [];
            }
            this.blockStore[i] = arr;
        }
    }

    getBlockIndex(coordVal, isFloor) {
        // isLeft设置为true 向下取整；设置为falsh向上取整
        var index = Math.round(coordVal / this.blockSize);
        if (index < 0) {
            index = 0;
        } else if (index >= this.blockNum) {
            index = this.blockNum - 1;
        }

        return index;
    }

    setToBlockStore(xPos, yPos, itemId) {
        var xIndex = this.getBlockIndex(xPos, true);
        var yIndex = this.getBlockIndex(yPos, true);

        this.blockStore[xIndex][yIndex].push(itemId);
        return true;
    }

    getFromBlockStore(xPos, yPos, radiusX, radiusY) {
        //var xIndex = this.getBlockIndex(xPos, true);
        //var yIndex = this.getBlockIndex(yPos, true);

        var xLeft = xPos - radiusX;
        var xRight = xPos + radiusX;
        var yBottom = yPos - radiusY;
        var yTop = yPos + radiusY;
        var xStart = this.getBlockIndex(xLeft, true);
        var xEnd = this.getBlockIndex(xRight, false);
        var yStart = this.getBlockIndex(yBottom, true);
        var yEnd = this.getBlockIndex(yTop, false);

        var blocks = this.blockStore;
        var result = [];

        // 内部
        for (var i = xStart; i <= xEnd; ++i) {
            var firstArr = blocks[i];
            for (var j = yStart; j <= yEnd; ++j) {
                var secondArr = firstArr[j];
                if (secondArr.length == 0) {
                    continue;
                }
                if (i == xStart || i == xEnd || j == yStart || j == yEnd) {
                    for (var foodId of secondArr) {
                        var food = this.foods.get(foodId);
                        if (!food) {
                            continue;
                        }
                        if ((yBottom <= food.position.yPos && food.position.yPos <= yTop)
                            && (xLeft <= food.position.xPos && food.position.xPos <= xRight)) {
                            result.push(foodId);
                        }
                    }
                } else {
                    // boxer inner
                    result = result.concat(secondArr);
                }
            }
        }
        return result;
    }

    delInBlockStore(xPos, yPos, foodId) {
        var xIndex = this.getBlockIndex(xPos, true);
        var yIndex = this.getBlockIndex(yPos, true);
        if (xIndex < 0 || xIndex >= this.blockNum || yIndex < 0 || yIndex >= this.blockNum) {
            console.log("delInBlockStore error: xIndex= " + xIndex + ", yIndex= " + yIndex);
            return;
        }
        var findArr = this.blockStore[xIndex][yIndex];
        var newArr = [];
        for (var b of findArr) {
            if (b != foodId) {
                newArr.push(b);
            }
        }
        this.blockStore[xIndex][yIndex].splice(0);
        this.blockStore[xIndex][yIndex] = newArr;
    }

    getMovableFoods() {
        return this.movableFoods;
    }

    // 生成正常食物
    generateNormalFood(type, amount) {
        var xFromPos = HALF_MAP_SIZE - g_foodArea, yFromPos = xFromPos,
            xToPos = xFromPos + g_foodArea * 2, yToPos = xToPos;

        var i = 0;
        while (i < amount) {
            var xPos = mathUtils.getRandomInt(xFromPos, xToPos);
            var yPos = mathUtils.getRandomInt(yFromPos, yToPos);
            var distX = xPos - HALF_MAP_SIZE;
            var distY = yPos - HALF_MAP_SIZE;
            if (Math.pow(distX, 2) + Math.pow(distY, 2) < Math.pow(g_foodArea, 2)) {
                var color = mathUtils.getRandomInt(0, g_foodColors);
                var size = 8;
                var energy = 2.5;
                var food = new Food(type, xPos, yPos, size, color, energy);
                i++;
                this.foods.set(food.foodId, food);
                this.setToBlockStore(food.position.xPos, food.position.yPos, food.foodId);
                if (type == Food.Type.BASIC) {
                    ++this.basic_food_num;
                } else if (type == Food.Type.GROWING) {
                    this.growFoods.add(food.foodId);
                }
            }
        }
    }

    // 生成移动食物
    generateMovableFood(type, amount) {
        var xFromPos = HALF_MAP_SIZE - g_foodArea, yFromPos = xFromPos,
            xToPos = xFromPos + g_foodArea * 2, yToPos = xToPos;

        var i = 0;
        while (i < amount) {
            var xPos = mathUtils.getRandomInt(xFromPos, xToPos);
            var yPos = mathUtils.getRandomInt(yFromPos, yToPos);
            var distX = xPos - HALF_MAP_SIZE;
            var distY = yPos - HALF_MAP_SIZE;
            if (Math.pow(distX, 2) + Math.pow(distY, 2) < Math.pow(g_foodArea, 2)) {
                var color = mathUtils.getRandomInt(0, g_foodColors);
                var size = 12;
                var energy = 80;

                var food = new Food(type, xPos, yPos, size, color, energy);
                /*
                 setInterval(() => { // memory leaks?
                 f.velocity = {x: mathUtils.getRandomInt(-200, 200), y: mathUtils.getRandomInt(-200, 200)};
                 }, 4000);   // 4 sec
                 */

                this.movableFoods.add(food.foodId);
                this.foods.set(food.foodId, food);
                i++;
            }
        }
    }

    // 加速残留食物
    generateSpeedFood(snake) {
        var pos = snake.getTailPos();
        var color = mathUtils.getRandomInt(0, g_foodColors);
        var size = 5;
        var energy = 0.7;
        var food = new Food(Food.Type.AFTER_SPEEDUP, pos.xPos, pos.yPos, size, color, energy);
        this.foods.set(food.foodId, food);

        this.setToBlockStore(food.position.xPos, food.position.yPos, food.foodId);
    }

    // 蛇死亡产生食物
    generateDeathFood(snake) {
        if (snake == null) return;

        var segLen = Math.floor(snake.width * FOOD_GAP_RAT);
        var foodPos = gameUtils.getInterpolatePoints(snake.getBodyPoints(), segLen);
        var len = foodPos.length;
        var energy = Math.round(snake.energy / len * FOOD_DEPRECIATE);
        energy = (energy > 0) ? energy : 2;
        //console.log("generateDeathFood: foodPos.length= " + foodPos.length);

        //var foodList = [];
        foodPos.forEach(pos => {
            var color = mathUtils.getRandomInt(0, g_foodColors);
            var size = mathUtils.getRandomInt(snake.width * g_foodSize[0], snake.width * g_foodSize[1]);

            // scatter the food position
            pos.xPos += Math.round(mathUtils.getRandomInt(-FOOD_POS_OFFSET, FOOD_POS_OFFSET));
            pos.yPos += Math.round(mathUtils.getRandomInt(-FOOD_POS_OFFSET, FOOD_POS_OFFSET));

            var food = new Food(Food.Type.AFTER_DEAD, pos.xPos, pos.yPos, size, color, energy);
            this.foods.set(food.foodId, food);

            this.setToBlockStore(food.position.xPos, food.position.yPos, food.foodId);
            //console.log("generateDeathFood: food.foodId= " + food.foodId);
        });
    }

    // 删除食物
    deleteMoveFood(food) {
        this.movableFoods.delete(food.id);
        this.foods.delete(food.id);
    }

    // 删除食物
    deleteFood(foodIds) {
        for (var id of foodIds) {
            var food = this.foods.get(id);
            if (food) {
                if (food.foodType == Food.Type.MOVABLE) {
                    this.movableFoods.delete(id);
                } else {
                    if (food.foodType == Food.Type.GROWING) {
                        this.growFoods.delete(id);
                    }
                    else if (food.foodType == Food.Type.BASIC) {
                        --this.basic_food_num;
                    }
                    this.delInBlockStore(food.position.xPos, food.position.yPos, id);
                }
            }
            this.foods.delete(id);
        }
    }

    getById(id) {
        return this.foods.get(id);
    }

    batchGet(ids) {
        var result = [];
        for (var id of ids) {
            var food = this.foods.get(id);
            if (food) {
                result.push(food);
            }
        }
        return result;
    }

    clearAllFood() {
        for (var i = 0; i < this.blockNum; ++i) {
            for (var j = 0; j < this.blockNum; ++j) {
                this.blockStore[i][j] = [];
            }
        }
        this.growFoods.clear();
        this.movableFoods.clear();
        this.foods.clear();
    }
}
;

var FoodModelIns = new FoodModel();

module.exports = FoodModelIns;