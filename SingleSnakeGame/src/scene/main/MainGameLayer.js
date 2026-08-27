/**
 * 20160506
 * created by brandyxie
 *
 */
var MainGameLayer = cc.Layer.extend({

    ctor: function () {
        this._super();

        this.init();
    },

    init: function () {
        this.setAnchorPoint(0.5, 0.5);

        var foodLayer = new FoodLayer(mapSize);
        this.addChild(foodLayer, LAYER_DEF.FOOD_BALL);

        //init player manager
        playerManager.init(this);

        //initialize all player
        this.initAllPlayers();
    },

    initAllPlayers: function () {
        playerManager.createMainPlayer();
        playerManager.createOtherPlayer();
    },

    onExit: function () {
        this._super();

        //clear all data
        playerManager.clearAll();
        snakeMoveController.reset();
    },
});