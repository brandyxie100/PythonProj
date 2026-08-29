'use strict';
var SnakeModel = require('../models/SnakeModel');
var settings = require("../utils/settings");
var PacketHandler = require("../packets/PacketHandler");
var EventEmitter = require('../utils/eventEmitter');
var FoodModel = require("../models/FoodModel");
var Food = require("../entities/food");
var RoomService = require('./RoomService');
var gameUtils = require("../utils/gameUtils");

// AI蛇的最大数目
var ROBOT_SNAKE_MAX_COUNT = settings.readSetting("robot-snake-max-count");
// AI蛇转向的平均间隔（秒）
var ROBOT_SNAKE_ROTATE_TIME = settings.readSetting("robot-snake-rotate-time");
// AI蛇找食物的平均间隔（秒）
var ROBOT_SNAKE_FIND_FOOD = settings.readSetting("robot-snake-find-food");

var g_mapSize = settings.readSetting("map-size");
var g_mapRadius = settings.readSetting("map-radius");
var g_frameTime = settings.readSetting("frame", 30);
var aiNames = settings.readSetting("AI_NAME", []);
var g_centerPos = {xPos: g_mapSize / 2, yPos: g_mapSize / 2};
var ROBOT_LIVE_RANGE = settings.readSetting("robot-live-range");

// Candidate ray angles relative to current heading (radians)
var SENSOR_RAY_ANGLES = [0, 0.45, -0.45, 0.95, -0.95, 1.6, -1.6];

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
        var tierConfig = RoomService.getAITierConfig();

        // 如果蛇的数量不足，每秒生成1条蛇
        var ROBOT_SNAKE_INTERVAL = netManager.getServerConfig().robot_born_time * 1000;
        if (SnakeModel.snakes.size < ROBOT_SNAKE_MAX_COUNT && this.geneSnakeStatus && curTime - this.lastGeneSnakeTime >= ROBOT_SNAKE_INTERVAL) {
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
        for (var j = 0; j < robotSnakes.length; j++) {
            var snake = robotSnakes[j];
            if (snake.dead) {
                deadNum++;
                continue;
            }

            var distX = snake.headPos.xPos - g_centerPos.xPos;
            var distY = snake.headPos.yPos - g_centerPos.yPos;
            var distS = Math.pow(distX, 2) + Math.pow(distY, 2);

            var bHas = snakeArrayVisible.has(snake.snakeId);
            if (!bHas) {
                if (Math.round(Math.random() * 20) == 0) {
                    if (distS > Math.pow(g_mapRadius, 2)) {
                        this.handleDeath(snake);
                    } else if (distS > Math.pow(ROBOT_LIVE_RANGE, 2)) {
                        snake.setTargetPos(g_centerPos.xPos - snake.headPos.xPos, g_centerPos.yPos - snake.headPos.yPos);
                    }
                    snake.updateMove(dt);
                }
            } else {
                // Out of boundary check
                if (distS > Math.pow(g_mapRadius, 2)) {
                    this.handleDeath(snake);
                    continue;
                } else if (distS > Math.pow(ROBOT_LIVE_RANGE, 2)) {
                    snake.setTargetPos(g_centerPos.xPos - snake.headPos.xPos, g_centerPos.yPos - snake.headPos.yPos);
                    snake.updateMove(dt);
                    continue;
                }

                // AI Decision Cycle:
                // Step 1: Multi-Ray Spatial Perception to check for obstacles/hazards
                var rayResults = this.castSpatialRays(snake, tierConfig);
                var forwardRay = rayResults.rays[0];
                var isForwardObstructed = forwardRay.clearance < forwardRay.maxDistance * 0.75;

                // Step 2: If forward path is hazardous, execute Tangential Evasion immediately
                if (isForwardObstructed) {
                    this.evadeThreats(snake, rayResults, tierConfig);
                } else {
                    // Step 3: Progressive Tactical Behaviors (Hunt, Encircle, Forage)
                    var effectiveDodgeInterval = Math.min(snake.dodgeInterval || 0.5, tierConfig.dodgeInterval);
                    var bDodgeTick = (Math.round(Math.random() * g_frameTime * effectiveDodgeInterval) == 0);

                    if (bDodgeTick) {
                        this.dodgeSnake(snake, tierConfig);
                    } else {
                        var bTacticalTick = (Math.round(Math.random() * g_frameTime * ROBOT_SNAKE_FIND_FOOD) == 0);
                        if (bTacticalTick) {
                            this.executeTacticalBehavior(snake, tierConfig);
                        } else if (Math.round(Math.random() * g_frameTime * ROBOT_SNAKE_ROTATE_TIME) == 0) {
                            // Gentle random wander turn
                            if (tierConfig.tier === 1) {
                                snake.setTargetPos(Math.random() - 0.5, Math.random() - 0.5);
                            }
                        }
                    }

                    // Natural speed regulation
                    if (Math.round(Math.random() * g_frameTime * 2) == 0 && snake.accelerate) {
                        // High tier AI only drops speed when energy is low or not actively intercepting
                        if (tierConfig.tier < 3 || snake.energy < 25) {
                            snake.speedDown();
                        }
                    }
                }

                snake.updateMove(dt);
            }
        }
    },

    /**
     * Cast multi-ray spatial perception cone around snake's heading.
     * Evaluates boundary hazards and other snake body segments.
     */
    castSpatialRays: function (snakeSelf, tierConfig) {
        var baseAngle = Math.atan2(snakeSelf.dirPos.yPos, snakeSelf.dirPos.xPos);
        var maxSensorDist = Math.max(90, snakeSelf.speed * 1.5) * tierConfig.sensorRangeScale;
        var samples = [0.35, 0.7, 1.0];
        var rays = [];
        var bestRay = null;
        var highestScore = -Infinity;

        // Pre-filter nearby snakes to keep spatial ray checks fast and efficient
        var nearbySnakes = [];
        for (let other of SnakeModel.snakes.values()) {
            if (other.snakeId !== snakeSelf.snakeId && !other.dead) {
                var dx = other.headPos.xPos - snakeSelf.headPos.xPos;
                var dy = other.headPos.yPos - snakeSelf.headPos.yPos;
                if (Math.abs(dx) < maxSensorDist * 2.5 && Math.abs(dy) < maxSensorDist * 2.5) {
                    nearbySnakes.push({
                        snake: other,
                        bodyPoints: gameUtils.getInterpolatePoints(other.getBodyPoints(), other.width)
                    });
                }
            }
        }

        for (var i = 0; i < SENSOR_RAY_ANGLES.length; i++) {
            var offset = SENSOR_RAY_ANGLES[i];
            var rayAngle = baseAngle + offset;
            var dirX = Math.cos(rayAngle);
            var dirY = Math.sin(rayAngle);
            var clearance = maxSensorDist;
            var blocked = false;

            for (var s = 0; s < samples.length; s++) {
                var d = maxSensorDist * samples[s];
                var testX = snakeSelf.headPos.xPos + dirX * d;
                var testY = snakeSelf.headPos.yPos + dirY * d;

                // Check Map Boundary
                var centerDist = Math.sqrt(Math.pow(testX - g_centerPos.xPos, 2) + Math.pow(testY - g_centerPos.yPos, 2));
                if (centerDist > g_mapRadius - 80) {
                    clearance = d;
                    blocked = true;
                    break;
                }

                // Check other snake bodies
                var collisionRadius = snakeSelf.width * 0.75;
                var collisionRadiusSq = collisionRadius * collisionRadius;

                for (var k = 0; k < nearbySnakes.length; k++) {
                    var pts = nearbySnakes[k].bodyPoints;
                    for (var p = 0; p < pts.length; p++) {
                        var pDistSq = Math.pow(testX - pts[p].xPos, 2) + Math.pow(testY - pts[p].yPos, 2);
                        if (pDistSq <= collisionRadiusSq) {
                            clearance = d;
                            blocked = true;
                            break;
                        }
                    }
                    if (blocked) break;
                }
                if (blocked) break;
            }

            // Score ray based on clearance and deviation penalty
            var score = clearance - Math.abs(offset) * 40;
            var rayInfo = {
                angleOffset: offset,
                rayAngle: rayAngle,
                dirX: dirX,
                dirY: dirY,
                clearance: clearance,
                maxDistance: maxSensorDist,
                score: score,
                isClear: clearance >= maxSensorDist * 0.85
            };
            rays.push(rayInfo);

            if (score > highestScore) {
                highestScore = score;
                bestRay = rayInfo;
            }
        }

        return {
            rays: rays,
            bestRay: bestRay,
            maxSensorDist: maxSensorDist
        };
    },

    /**
     * Steer smoothly along the safest escape vector avoiding sudden 180° jerks.
     */
    evadeThreats: function (snakeSelf, rayResults, tierConfig) {
        var bestRay = rayResults.bestRay;
        if (bestRay) {
            snakeSelf.setTargetPos(bestRay.dirX * 500, bestRay.dirY * 500);

            // If clearance is dangerously low, decelerate; if a wide open exit exists in higher tiers, sprint through
            if (bestRay.clearance < rayResults.maxSensorDist * 0.4) {
                snakeSelf.speedDown();
            } else if (tierConfig.tier >= 2 && bestRay.isClear && snakeSelf.energy > 30) {
                snakeSelf.speedUp();
            }
        }
    },

    /**
     * Multi-behavior tactical controller: Intercept, Encircle, or Forage based on match tier.
     */
    executeTacticalBehavior: function (snakeSelf, tierConfig) {
        // High Tier Tactics: Predictive Hunting & Encircling
        if (tierConfig.tier >= 2) {
            var targetSnake = this.findTacticalTarget(snakeSelf, tierConfig);
            if (targetSnake) {
                // Encircling Maneuver: AI is significantly larger and close
                var distToTarget = Math.sqrt(
                    Math.pow(targetSnake.headPos.xPos - snakeSelf.headPos.xPos, 2) +
                    Math.pow(targetSnake.headPos.yPos - snakeSelf.headPos.yPos, 2)
                );

                var canEncircle = (snakeSelf.length > targetSnake.length * 1.4) &&
                                  (distToTarget < snakeSelf.length * 0.5) &&
                                  (Math.random() < tierConfig.encircleProp);

                if (canEncircle) {
                    this.executeEncircle(snakeSelf, targetSnake);
                    return;
                }

                // Predictive Interception Hunting
                if (Math.random() < tierConfig.huntingAggression) {
                    this.executeInterception(snakeSelf, targetSnake, tierConfig, distToTarget);
                    return;
                }
            }
        }

        // Default / Tier 1 Behavior: Intelligent Food Foraging
        this.eatFood(snakeSelf, tierConfig);
    },

    /**
     * Locate the most suitable opponent snake in view.
     */
    findTacticalTarget: function (snakeSelf, tierConfig) {
        var bestTarget = null;
        var minScore = Infinity;

        for (let other of SnakeModel.snakes.values()) {
            if (other.snakeId === snakeSelf.snakeId || other.dead || other.isProtected()) {
                continue;
            }

            var dx = other.headPos.xPos - snakeSelf.headPos.xPos;
            var dy = other.headPos.yPos - snakeSelf.headPos.yPos;
            var dist = Math.sqrt(dx * dx + dy * dy);

            if (dist > snakeSelf.screenX * 1.5) {
                continue;
            }

            // Prefer targets that are closer and smaller / comparable in length
            var sizeRatio = other.length / (snakeSelf.length + 1);
            var score = dist * (0.6 + 0.4 * sizeRatio);

            if (score < minScore) {
                minScore = score;
                bestTarget = other;
            }
        }

        return bestTarget;
    },

    /**
     * Predictive Head Interception: Compute target's future path and cut off their trajectory.
     */
    executeInterception: function (snakeSelf, targetSnake, tierConfig, distToTarget) {
        var leadSec = tierConfig.interceptLead;
        var targetSpeed = targetSnake.speed || 390;
        var targetHeadingX = targetSnake.dirPos.xPos;
        var targetHeadingY = targetSnake.dirPos.yPos;

        // Predict future position of enemy snake's head
        var predictedX = targetSnake.headPos.xPos + targetHeadingX * targetSpeed * leadSec;
        var predictedY = targetSnake.headPos.yPos + targetHeadingY * targetSpeed * leadSec;

        // Target cut-off vector
        var interceptVectorX = predictedX - snakeSelf.headPos.xPos;
        var interceptVectorY = predictedY - snakeSelf.headPos.yPos;

        snakeSelf.setTargetPos(interceptVectorX, interceptVectorY);

        // Tactical Sprint: Boost when closing in for a cut-off
        if (distToTarget < 400 && snakeSelf.energy > 30 && Math.random() < tierConfig.tacticalBoostProp) {
            snakeSelf.speedUp();
        }
    },

    /**
     * Encircling / Coiling maneuver around smaller trapped snakes.
     */
    executeEncircle: function (snakeSelf, targetSnake) {
        var dx = targetSnake.headPos.xPos - snakeSelf.headPos.xPos;
        var dy = targetSnake.headPos.yPos - snakeSelf.headPos.yPos;
        var angleToTarget = Math.atan2(dy, dx);

        // Steer perpendicular (tangential orbit) around the target
        var orbitAngle = angleToTarget + Math.PI / 2.2;
        snakeSelf.setTargetPos(Math.cos(orbitAngle) * 500, Math.sin(orbitAngle) * 500);

        if (snakeSelf.energy > 40) {
            snakeSelf.speedUp();
        }
    },

    eatFood: function (snake, tierConfig) {
        var bFindDead = false;
        var nearestDeadFoodId = 0;
        var nearestOthFoodId = 0;
        var nearestDeadFoodDist = Math.pow(snake.screenX, 2) + Math.pow(snake.screenY, 2);
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

            var boostChance = (tierConfig && tierConfig.tier >= 2) ? 450 : (snake.accProp || 50);
            var bAcc = (Math.round(Math.random() * 600) <= boostChance) ? 1 : 0;
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

    dodgeSnake: function (snakeSelf, tierConfig) {
        var rayResults = this.castSpatialRays(snakeSelf, tierConfig || RoomService.getAITierConfig());
        if (rayResults.bestRay && !rayResults.bestRay.isClear) {
            this.evadeThreats(snakeSelf, rayResults, tierConfig || RoomService.getAITierConfig());
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


module.exports = RobotService;
