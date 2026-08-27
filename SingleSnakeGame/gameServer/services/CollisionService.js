var Collision = require("../collision/collision");
var settings = require("../utils/settings");
var FoodModel = require("../models/FoodModel");
var SnakeModel = require("../models/SnakeModel");

var CollisionService = {
    collision: null,
    init: function () {
        var size = settings.readSetting("map-size");
        this.collision = new Collision(size, size);
    },

    checkCollision: function (packetHandler) {
        //var t1 = new Date();
        // clear all data
        this.collision.reset();

        //var t2 = new Date();
        // add elements from snake models and food models
        this.collision.addElements(packetHandler);

        //var t3 = new Date();
        // check collision
        this.collision.checkCollision();

        //var t4 = new Date();
        //console.log("check collision detail: reset= " + (t2 - t1) + ", addElements= " + (t3 - t2) + ", checkCollision= " + (t4 - t3));
    }
};

CollisionService.init();

module.exports = CollisionService;
    
