/*
 * author: tonghuang
 * date: 2016.05.05
 */

'use strict';

var FoodModel = require("../models/FoodModel");
var SnakeModel = require("../models/SnakeModel");
var QuadTree = require("./quadtree");
var FoodEntity = require("../entities/food");
var gameUtils = require("../utils/gameUtils");
var settings = require("../utils/settings");
var geometry = require("../utils/geometry");

// 蛇头增加的热区大小
var SNAKE_HEAD_EXTRA_SIZE = settings.readSetting("snake-head-extra-size");
// 移动型食物判断距离
var MOVE_FOOD_EXTRA_SIZE = settings.readSetting("move-food-extra-size");
// 出生的蛇无敌状态时间（秒）
var BORN_SNAKE_GOD_TIME = settings.readSetting("snake-born-god-time") * 1000;
// 蛇头碰撞时缩进判断
var SNAKE_HEAD_SHRINK_SIZE = 10;
// 理论食物最大大小
var MAX_FOOD_SIZE = 20;
// 判断是否加入碰撞检测的视野范围扩大系数
var SCREEN_SCALE_RATE = 0.62;

var ElementType = {
    NORMAL_FOOD: 1,
    MOVE_FOOD: 2,
    SNAKE_HEAD: 3,
    SNAKE_BODY: 4
};


class Collision {
    constructor(width, height) {
        var args = {x: 0, y: 0, h: height, w: width, maxChildren: 5, maxDepth: 5};
        this.quadtree = QuadTree.init(args);    // 初始化四叉树
        this.elementList = [];  // 保存着所有节点的信息
        this.killedSnake = new Map();  // 被杀死的蛇
        this.eatenFood = new Map();    // 被吃掉的食物
        this.nearMovedFood = new Map(); // 进入移动食物的热区

        this.killedSnakeSet = new Set();  // 被杀死的蛇
        this.eatenFoodSet = new Set();    // 被吃掉的食物
    }

    reset() {
        this.quadtree.clear();
        this.elementList = [];
        this.killedSnake.clear();
        this.eatenFood.clear();
        this.nearMovedFood.clear();
        this.killedSnakeSet.clear();
        this.eatenFoodSet.clear();
    }

    filterByAABB(snakeSelf, othSnake) {
        var othAABB = othSnake.getAABB();
        var disX = cc.winSize.width * SCREEN_SCALE_RATE; //适当扩大屏幕可视范围
        var disY = cc.winSize.height * SCREEN_SCALE_RATE;
        var selfView = {
            xMin: snakeSelf.headPos.xPos - disX,
            xMax: snakeSelf.headPos.xPos + disX,
            yMin: snakeSelf.headPos.yPos - disY,
            yMax: snakeSelf.headPos.yPos + disY
        };

        if (othAABB.xMax < selfView.xMin || othAABB.xMin > selfView.xMax ||
            othAABB.yMax < selfView.yMin || othAABB.yMin > selfView.yMax) {
            return false;
        }
        return true;
    }

    isInViewAreaSnake(snakeSelf, othSnake) {
        if (!this.filterByAABB(snakeSelf, othSnake)) {
            return false;
        }

        // 插入点进行更精确的判断
        var deltaX;
        var deltaY;
        var canSee = false;
        var disX = cc.winSize.width * SCREEN_SCALE_RATE;
        var disY = cc.winSize.height * SCREEN_SCALE_RATE;
        var othBodyPoints = gameUtils.getInterpolatePoints(othSnake.getBodyPoints(), othSnake.width);
        for (var i = 0; i < othBodyPoints.length; i++) {
            deltaX = snakeSelf.headPos.xPos - othBodyPoints[i].xPos;
            deltaY = snakeSelf.headPos.yPos - othBodyPoints[i].yPos;
            canSee = canSee || ((Math.abs(deltaX) < disX) && (Math.abs(deltaY) < disY));
            if (canSee) {
                return canSee;
            }
        }
        return false;
    }

    addElements(packetHandler) {
        //var foodNum = FoodModel.foods.size;
        //var moveFoodNum = FoodModel.movableFoods.size;

        // 插入可移动的食物
        var food;
        for (var id of FoodModel.movableFoods) {
            food = FoodModel.foods.get(id);
            if (food) {
                this.elementList.push({
                    x: food.position.xPos - food.radius - MOVE_FOOD_EXTRA_SIZE,
                    y: food.position.yPos - food.radius - MOVE_FOOD_EXTRA_SIZE,
                    h: food.radius * 2 + 2 * MOVE_FOOD_EXTRA_SIZE,
                    w: food.radius * 2 + 2 * MOVE_FOOD_EXTRA_SIZE,
                    type: ElementType.MOVE_FOOD,
                    id: food.foodId
                });
            }
        }

        var snakeHeadNum = 0;
        var snakeBodyNum = 0;
        var normalFoodNum = 0;
        var blockIds = new Set();
        //console.log("SnakeModel.snakes.size= " + SnakeModel.snakes.size);

        var snakeSelf = packetHandler.getSnake();
        var snakeCanSeeList = [];
        var snakeNotSeeList = [];
        SnakeModel.snakes.forEach(snake => {
            if (snake.snakeId === snakeSelf.snakeId) {
                snakeCanSeeList.push(snake);
            } else {
                if (this.isInViewAreaSnake(snakeSelf, snake)) {
                    snakeCanSeeList.push(snake);
                } else {
                    snakeNotSeeList.push(snake);
                }
            }
        });
        //console.log("snakeCanSeeList.length= " + snakeCanSeeList.length);
        //console.log("snakeNotSeeList.length= " + snakeNotSeeList.length);
        var bLowConfig;
        if (cc.sys.os === cc.sys.OS_IOS || cc._renderType !== cc.game.RENDER_TYPE_CANVAS) {
            bLowConfig = false;
        } else {
            bLowConfig = true;
        }
        //add random energy here
        var snake;
        var addEnergy = bLowConfig ? 2 : Math.round(Math.random() * 10 + 2);
        var randomValue;
        for (var i in snakeNotSeeList) {
            snake = snakeNotSeeList[i];
            randomValue = Math.round(Math.random() * 20);
            if (randomValue == 0) {
                snake.addEnergy(addEnergy);
                //console.log("snake.energy += " + addEnergy);
            }
        }

        //SnakeModel.snakes.forEach(snake => {
        snakeCanSeeList.forEach(snake => {
            // 蛇头调整中心点
            var newPos = snake.getHotZonePos(SNAKE_HEAD_EXTRA_SIZE);
            var halfWidth = snake.width / 2;
            this.elementList.push({
                x: newPos.xPos - halfWidth - SNAKE_HEAD_EXTRA_SIZE,
                y: newPos.yPos - halfWidth - SNAKE_HEAD_EXTRA_SIZE,
                h: snake.width + 2 * SNAKE_HEAD_EXTRA_SIZE,
                w: snake.width + 2 * SNAKE_HEAD_EXTRA_SIZE,
                type: ElementType.SNAKE_HEAD,
                id: snake.snakeId,
                srcX: snake.headPos.xPos - halfWidth,
                srcY: snake.headPos.yPos - halfWidth
            });
            snakeHeadNum++;

            var len = halfWidth + SNAKE_HEAD_EXTRA_SIZE + MAX_FOOD_SIZE;
            var x1 = FoodModel.getBlockIndex(newPos.xPos - len);
            var x2 = FoodModel.getBlockIndex(newPos.xPos + len);
            var y1 = FoodModel.getBlockIndex(newPos.yPos - len);
            var y2 = FoodModel.getBlockIndex(newPos.yPos + len);
            // console.info('[x1=%d] [x2=%d] [y1=%d] [y2=%d]', x1, x2, y1, y2);
            var keyName = null;
            for (var i = x1; i <= x2; ++i) {
                for (var j = y1; j <= y2; ++j) {
                    keyName = i * 100000 + j;
                    if (!(blockIds.has(keyName))) {
                        normalFoodNum += FoodModel.blockStore[i][j].length;
                        var food = null;
                        for (var food_id of FoodModel.blockStore[i][j]) {
                            food = FoodModel.foods.get(food_id);
                            if (food) {
                                this.elementList.push({
                                    x: food.position.xPos - food.radius,
                                    y: food.position.yPos - food.radius,
                                    h: food.radius * 2,
                                    w: food.radius * 2,
                                    type: ElementType.NORMAL_FOOD,
                                    id: food.foodId
                                });
                            }
                        }
                        blockIds.add(keyName);
                        //console.info('add block[%d][%d] [foodNum=%d]', i, j, FoodModel.blockStore[i][j].length);
                    }
                }
            }

            // 对蛇的身体进行插值
            var bodyPoints = gameUtils.getInterpolatePoints(snake.getBodyPoints(), snake.width);
            /*
             var debugOutput = false;
             if (snake.name == "HTT" && Math.ceil(Math.random() * 100) == 50) {
             debugOutput = true;
             console.info("FOR TEST BEGIN");
             }
             */

            bodyPoints.forEach(bodyPos => {
                this.elementList.push({
                    x: bodyPos.xPos - (snake.width / 2),
                    y: bodyPos.yPos - (snake.width / 2),
                    h: snake.width,
                    w: snake.width,
                    type: ElementType.SNAKE_BODY,
                    id: snake.snakeId
                });

                /*if (debugOutput) {
                 console.info("[SnakeId=%d] [AfterInterpolate:] ((%d-beginX)*scale,(%d-beginY)*scale,%d*scale,%d*scale)",
                 snake.snakeId, bodyPos.xPos, bodyPos.yPos, snake.width, snake.width);
                 }*/

                snakeBodyNum++;
            });
        });

        //console.log("[elementsize=%d] [moveFoodNum=%d] [normalFoodNum=%d] [snakeHeadNum=%d] [snakeBodyNum=%d]",
        //    this.elementList.length, moveFoodNum, normalFoodNum, snakeHeadNum, snakeBodyNum);

        this.quadtree.insert(this.elementList);
    }

    checkCollision() {
        var elementListNum = this.elementList.length;
        var checkStepNum = 0;
        var thisCollision = this;
        var element;
        for (var i = 0; i < elementListNum; i++) {
            element = this.elementList[i];
            if (element.type == ElementType.SNAKE_HEAD) {
                // 对所有的蛇头节点进行碰撞检测
                this.quadtree.retrieve(element, function (item) {
                    thisCollision.detectCollisionRect(element, item);
                    checkStepNum++;
                })
            }
        }
    }

    detectCollisionRect(item1, item2) {
        // 1. 同个对象直接返回
        if (item1 == item2) {
            return;
        }

        // 2. 同条蛇直接返回
        if (item1.id == item2.id && item1.type == ElementType.SNAKE_HEAD
            && item2.type == ElementType.SNAKE_BODY) {
            return;
        }

        if (item2.type == ElementType.SNAKE_HEAD) {
            // 如果是蛇头的话需要使用原始坐标进行碰撞检测
            if (item1.srcX + item1.w - 2 * SNAKE_HEAD_EXTRA_SIZE - SNAKE_HEAD_SHRINK_SIZE < item2.srcX ||
                item1.srcY + item1.h - 2 * SNAKE_HEAD_EXTRA_SIZE - SNAKE_HEAD_SHRINK_SIZE < item2.srcY ||
                item1.srcX > item2.srcX + item2.w - 2 * SNAKE_HEAD_EXTRA_SIZE - SNAKE_HEAD_SHRINK_SIZE ||
                item1.srcY > item2.srcY + item2.h - 2 * SNAKE_HEAD_EXTRA_SIZE - SNAKE_HEAD_SHRINK_SIZE) {
                return;
            }
        }
        else if (item2.type == ElementType.SNAKE_BODY) {
            // 如果是蛇身的话需要使用原始坐标进行碰撞检测
            if (item1.srcX + item1.w - 2 * SNAKE_HEAD_EXTRA_SIZE - SNAKE_HEAD_SHRINK_SIZE < item2.x || item1.srcX > item2.x + item2.w ||
                item1.srcY + item1.h - 2 * SNAKE_HEAD_EXTRA_SIZE - SNAKE_HEAD_SHRINK_SIZE < item2.y || item1.srcY > item2.y + item2.h) {
                return;
            }
        }
        else {
            if (item1.x + item1.w < item2.x || item1.x > item2.x + item2.w ||
                item1.y + item1.h < item2.y || item1.y > item2.y + item2.h) {
                return;
            }
        }

        // 4. 如果是移动型食物，需要看是否在扩展区域，并不是真的碰撞
        if (item2.type == ElementType.MOVE_FOOD) {
            // 如果处于移动型食物扩展区域，需要记录下来通知移动食物反向移动
            if (item1.x + item1.w < item2.x + MOVE_FOOD_EXTRA_SIZE || item1.x > item2.x + item2.w - MOVE_FOOD_EXTRA_SIZE ||
                item1.y + item1.h < item2.y + MOVE_FOOD_EXTRA_SIZE || item1.y > item2.y + item2.h - MOVE_FOOD_EXTRA_SIZE) {
                // console.info('Snake [id=%d] (%d,%d) (%d,%d) in move food near area [id=%d] (%d,%d) (%d,%d)',
                //    item1.id, item1.x.toFixed(1), item1.y.toFixed(1), item1.w, item1.h,
                //    item2.id, item2.x.toFixed(1), item2.y.toFixed(1), item2.w, item2.h);

                var val = this.nearMovedFood.get(item2.id);
                if (val) {
                    val.push(item1.id);
                } else {
                    this.nearMovedFood.set(item2.id, [item1.id]);
                }
                return;
            }
        }

        // 5. 发生吃食物的行为
        if (item2.type == ElementType.NORMAL_FOOD || item2.type == ElementType.MOVE_FOOD) {
            if (this.eatenFoodSet.has(item2.id)) {
                console.log("this.eatenFoodSet.has: item2.id= " + item2.id);
                return;
            }
            var val = this.eatenFood.get(item1.id);
            if (val) {
                val.push(item2.id);
            } else {
                this.eatenFood.set(item1.id, [item2.id]);
            }
            return;
        }

        // 6. 蛇被吃了
        if (item2.type == ElementType.SNAKE_BODY || item2.type == ElementType.SNAKE_HEAD) {
            if (this.killedSnakeSet.has(item2.id)) {
                return;
            }
            var val = this.killedSnake.get(item2.id);
            if (val && (val.indexOf(item1.id) == -1)) {
                val.push(item1.id);
            } else {
                this.killedSnake.set(item2.id, [item1.id]);
            }

            /*
             console.log('Snake [id=%d] (%d,%d) (%d,%d) (%d,%d) killed by Snake [id=%d] (%d,%d) (%d,%d) (%d,%d)]',
             item1.id, item1.x.toFixed(1), item1.y.toFixed(1), item1.w, item1.h, item1.srcX.toFixed(1), item1.srcY.toFixed(1),
             item2.id, item2.x.toFixed(1), item2.y.toFixed(1), item2.w, item2.h,
             item2.type == ElementType.SNAKE_HEAD ? item2.srcX.toFixed(1) : item2.x.toFixed(1),
             item2.type == ElementType.SNAKE_HEAD ? item2.srcY.toFixed(1) : item2.y.toFixed(1));
             */
            return;
        }
    }
}
;

module.exports = Collision;
